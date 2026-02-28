import torch
import os
import tempfile
import logging
from pathlib import Path
import builtins
import wave

# Compatibility patches for torchaudio/pyannote compatibility
import torchaudio

if not hasattr(torchaudio, 'list_audio_backends'):
    torchaudio.list_audio_backends = lambda: ['soundfile']

# Simplified AudioDecoder that delegates to torchaudio.load
class AudioMetadata:
    def __init__(self, uri):
        self.uri = uri
        try:
            # Use wave module for basic metadata
            with wave.open(uri, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                self.sample_rate = sample_rate
                self.duration = frames / sample_rate
                self.channels = channels
        except Exception as e:
            # Fallback: load audio to get metadata
            waveform, sr = torchaudio.load(uri)
            self.sample_rate = sr
            self.duration = waveform.shape[1] / sr
            self.channels = waveform.shape[0]
    
    @property
    def duration_seconds_from_header(self):
        return self.duration
    
    @property
    def number_of_channels(self):
        return self.channels

def _load_audio_impl(uri, offset=None, duration=None):
    """Internal audio loading function"""
    try:
        waveform, sample_rate = torchaudio.load(uri)
        if offset is not None and duration is not None:
            offset_samples = int(offset * sample_rate)
            duration_samples = int(duration * sample_rate)
            waveform = waveform[:, offset_samples:offset_samples + duration_samples]
        return waveform, sample_rate
    except Exception as e:
        logger.error(f"Error loading audio: {e}")
        raise

class AudioDecoder:
    """Wrapper around torchaudio to decode audio files"""
    
    def __init__(self, uri=None):
        if uri:
            self.metadata = AudioMetadata(uri)
            self.uri = uri
        else:
            self.metadata = None
            self.uri = None
    
    def __call__(self, uri, offset=None, duration=None):
        """Load audio with optional offset and duration"""
        return _load_audio_impl(uri, offset, duration)

# Create module-level function for get_all_samples
def get_all_samples_impl(uri):
    """Load all audio samples from file"""
    return _load_audio_impl(uri, None, None)

# Add get_all_samples as a direct attribute
AudioDecoder.get_all_samples = staticmethod(get_all_samples_impl)

# Register AudioDecoder
torchaudio.AudioDecoder = AudioDecoder
builtins.AudioDecoder = AudioDecoder

from pyannote.audio import Pipeline

logger = logging.getLogger(__name__)


class DiarizationService:
    """Production-grade speaker diarization service with GPU support and caching."""
    
    # Global cache for model to avoid reloading
    _cached_pipeline = None
    _cached_device = None
    
    def __init__(self):
        self.pipeline = None
        self.device = None
        self._initialized = False

    @staticmethod
    def _get_cache_dir():
        """Get model cache directory."""
        if os.name == 'nt':  # Windows
            cache_dir = os.path.expanduser('~/.cache/huggingface/hub')
        else:  # Linux/Mac
            cache_dir = os.path.expanduser('~/.cache/huggingface/hub')
        return cache_dir

    def _initialize(self):
        """Initialize the diarization pipeline with caching and error handling."""
        if self._initialized:
            return

        try:
            # Check for HuggingFace token
            hf_token = os.getenv('HUGGINGFACE_TOKEN')
            if not hf_token:
                raise ValueError(
                    "HUGGINGFACE_TOKEN environment variable is required. "
                    "Get a free token at https://huggingface.co/settings/tokens"
                )

            # Use cached pipeline if available
            if DiarizationService._cached_pipeline is not None:
                self.pipeline = DiarizationService._cached_pipeline
                self.device = DiarizationService._cached_device
                logger.info("Using cached diarization pipeline")
                self._initialized = True
                return

            # Determine device (GPU if available, else CPU)
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
            else:
                self.device = torch.device("cpu")
                logger.warning("CUDA not available, using CPU (slower inference)")

            # Set cache directory
            cache_dir = self._get_cache_dir()
            os.environ['HF_HOME'] = cache_dir
            logger.info(f"Model cache directory: {cache_dir}")

            # Load pipeline with token
            logger.info("Loading pyannote/speaker-diarization-3.1 model...")
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=hf_token
            )

            # Move to device
            self.pipeline.to(self.device)
            logger.info(f"Pipeline loaded successfully on {self.device}")

            # Cache for future use
            DiarizationService._cached_pipeline = self.pipeline
            DiarizationService._cached_device = self.device

            self._initialized = True

        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize diarization pipeline: {e}")
            raise RuntimeError(
                f"Failed to load diarization model: {str(e)}. "
                "Ensure HUGGINGFACE_TOKEN is set and you have internet access."
            )

    def diarize(self, audio_file, num_speakers=None):
        """Perform diarization on uploaded audio file."""
        try:
            self._initialize()

            # Save temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                audio_file.save(temp_file.name)
                temp_path = temp_file.name
                logger.info(f"Processing audio file: {audio_file.filename}")

            try:
                return self.diarize_from_file(temp_path, num_speakers)
            finally:
                # Cleanup temp file
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

        except RuntimeError as e:
            logger.error(f"Diarization failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during diarization: {e}")
            raise RuntimeError(f"Diarization failed: {str(e)}")

    def diarize_from_file(self, file_path, num_speakers=None):
        """Perform diarization from file path."""
        try:
            self._initialize()

            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            # Run diarization
            kwargs = {"num_speakers": num_speakers} if num_speakers else {}
            
            logger.info(f"Starting diarization on {file_path}, num_speakers={num_speakers}")
            diarization = self.pipeline(file_path, **kwargs)
            logger.info("Diarization completed successfully")

            # Process results
            timeline = []
            speakers = {}

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if speaker not in speakers:
                    speakers[speaker] = {
                        'id': speaker,
                        'label': f"Speaker {len(speakers) + 1}",
                        'total_time': 0,
                        'turns': 0
                    }

                duration = turn.end - turn.start
                speakers[speaker]['total_time'] += duration
                speakers[speaker]['turns'] += 1

                timeline.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': speaker,
                    'speaker_label': speakers[speaker]['label']
                })

            result = {
                'timeline': timeline,
                'speakers': list(speakers.values()),
                'num_speakers': len(speakers)
            }
            
            logger.info(f"Diarization result: {len(speakers)} speakers, {len(timeline)} segments")
            return result

        except FileNotFoundError as e:
            logger.error(f"File error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during diarization_from_file: {e}")
            raise RuntimeError(f"Diarization processing failed: {str(e)}")