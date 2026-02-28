"""
WhisperX-based transcription and diarization service.
Combines transcription + speaker diarization in a unified pipeline.
"""

import whisperx
import torch
import os
import tempfile
import logging

logger = logging.getLogger(__name__)


class WhisperXService:
    """
    Unified transcription and diarization service using WhisperX.
    
    Features:
    - Fast transcription with whisperx
    - Word-level timestamps with alignment
    - Speaker diarization with pyannote
    - Automatic speaker-word assignment
    """
    
    # Global cache for models
    _cached_model = None
    _cached_model_size = None
    _cached_align_models = {}
    _cached_diarizer = None
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        self.hf_token = os.getenv('HUGGINGFACE_TOKEN')
        
        logger.info(f"WhisperX initialized with device: {self.device}, compute_type: {self.compute_type}")
    
    def _load_model(self, model_size='base', language=None):
        """Load WhisperX model with caching."""
        # Choose model based on language
        if language == 'en':
            # English-optimized model
            effective_model = f"{model_size}.en" if model_size in ['tiny', 'base', 'small', 'medium'] else model_size
        else:
            # Multilingual model (large-v3 recommended for non-English)
            effective_model = 'large-v3' if language and language != 'en' else model_size
        
        if WhisperXService._cached_model is not None and WhisperXService._cached_model_size == effective_model:
            logger.info(f"Using cached WhisperX model: {effective_model}")
            return WhisperXService._cached_model
        
        logger.info(f"Loading WhisperX model: {effective_model}")
        model = whisperx.load_model(
            effective_model, 
            self.device, 
            compute_type=self.compute_type
        )
        
        WhisperXService._cached_model = model
        WhisperXService._cached_model_size = effective_model
        
        return model
    
    def _load_align_model(self, language_code):
        """Load alignment model for word-level timestamps."""
        if language_code in WhisperXService._cached_align_models:
            return WhisperXService._cached_align_models[language_code]
        
        logger.info(f"Loading alignment model for language: {language_code}")
        model_a, metadata = whisperx.load_align_model(
            language_code=language_code,
            device=self.device
        )
        
        WhisperXService._cached_align_models[language_code] = (model_a, metadata)
        return model_a, metadata
    
    def _load_diarization_pipeline(self):
        """Load diarization pipeline."""
        if WhisperXService._cached_diarizer is not None:
            return WhisperXService._cached_diarizer
        
        if not self.hf_token:
            raise ValueError(
                "HUGGINGFACE_TOKEN required for speaker diarization. "
                "Get a token at https://huggingface.co/settings/tokens"
            )
        
        logger.info("Loading diarization pipeline: pyannote/speaker-diarization-3.1")
        
        # Use whisperx.diarize.DiarizationPipeline
        from whisperx.diarize import DiarizationPipeline
        diarizer = DiarizationPipeline(
            model_name="pyannote/speaker-diarization-3.1",
            use_auth_token=self.hf_token,
            device=self.device
        )
        
        WhisperXService._cached_diarizer = diarizer
        return diarizer
    
    def transcribe(self, audio_file, language='auto', model_size='base'):
        """
        Transcribe audio file (uploaded file object).
        
        Args:
            audio_file: Flask uploaded file
            language: Language code ('auto', 'en', 'ml', 'hi', etc.)
            model_size: Model size ('tiny', 'base', 'small', 'medium', 'large-v3')
        
        Returns:
            dict with text, segments, detected_language, duration
        """
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            return self.transcribe_from_file(temp_path, language, model_size)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def transcribe_from_file(self, file_path, language='auto', model_size='base'):
        """
        Transcribe audio from file path.
        
        Args:
            file_path: Path to audio file
            language: Language code ('auto', 'en', 'ml', 'hi', etc.)
            model_size: Model size
        
        Returns:
            dict with text, segments, detected_language, duration
        """
        # Determine language for model selection
        lang_for_model = None if language == 'auto' else language
        
        # Load model
        model = self._load_model(model_size, lang_for_model)
        
        # Transcribe
        logger.info(f"Transcribing: {file_path}, language={language}")
        audio = whisperx.load_audio(file_path)
        result = model.transcribe(
            audio,
            language=None if language == 'auto' else language,
            batch_size=16
        )
        
        detected_language = result.get('language', language if language != 'auto' else 'unknown')
        
        # Align for word-level timestamps (if supported)
        try:
            model_a, metadata = self._load_align_model(detected_language)
            result = whisperx.align(
                result["segments"], 
                model_a, 
                metadata, 
                audio, 
                self.device,
                return_char_alignments=False
            )
            logger.info("Word-level alignment completed")
        except Exception as e:
            logger.warning(f"Alignment not available for {detected_language}: {e}")
        
        # Process segments
        segments = []
        for seg in result.get('segments', []):
            segment_data = {
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip()
            }
            
            # Include word-level timestamps if available
            if 'words' in seg:
                segment_data['words'] = [
                    {
                        'word': w.get('word', ''),
                        'start': w.get('start', seg['start']),
                        'end': w.get('end', seg['end'])
                    }
                    for w in seg['words']
                ]
            
            segments.append(segment_data)
        
        # Calculate full text
        full_text = ' '.join(seg['text'] for seg in segments)
        duration = segments[-1]['end'] if segments else 0
        
        return {
            'text': full_text,
            'segments': segments,
            'detected_language': detected_language,
            'duration': duration
        }
    
    def transcribe_with_speakers(self, audio_file, language='auto', model_size='base', 
                                  num_speakers=None, min_speakers=None, max_speakers=None):
        """
        Full pipeline: transcription + alignment + speaker diarization.
        
        Args:
            audio_file: Flask uploaded file
            language: Language code
            model_size: Model size
            num_speakers: Exact number of speakers (optional)
            min_speakers: Minimum speakers (optional)
            max_speakers: Maximum speakers (optional)
        
        Returns:
            dict with transcript, segments_with_speakers, speakers_summary
        """
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            return self.transcribe_with_speakers_from_file(
                temp_path, language, model_size, 
                num_speakers, min_speakers, max_speakers
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def transcribe_with_speakers_from_file(self, file_path, language='auto', model_size='base',
                                            num_speakers=None, min_speakers=None, max_speakers=None,
                                            progress_callback=None):
        """
        Full pipeline from file path.
        
        Args:
            file_path: Path to audio file
            language: Language code
            model_size: Model size
            num_speakers: Exact number of speakers (optional)
            min_speakers: Minimum speakers (optional)
            max_speakers: Maximum speakers (optional)
            progress_callback: Optional function(progress_percent, message) for updates
        
        Returns:
            {
                'text': full transcript,
                'language': detected language,
                'segments_with_speakers': [
                    {'speaker': 'SPEAKER_00', 'text': '...', 'start': 0.0, 'end': 2.5, 'words': [...]},
                    ...
                ],
                'speakers_summary': [
                    {'id': 'SPEAKER_00', 'label': 'Speaker 1', 'total_time': 30.5, 'turns': 12},
                    ...
                ],
                'num_speakers': 2,
                'duration': 120.5
            }
        """
        def update_progress(pct, msg):
            if progress_callback:
                progress_callback(pct, msg)
            logger.info(f"[{pct}%] {msg}")
        
        update_progress(5, "Loading audio file...")
        
        # Step 1: Load audio once (reused by all steps)
        audio = whisperx.load_audio(file_path)
        
        # Step 2: Transcribe
        update_progress(15, "Loading Whisper model...")
        lang_for_model = None if language == 'auto' else language
        model = self._load_model(model_size, lang_for_model)
        
        update_progress(25, "Transcribing audio...")
        result = model.transcribe(
            audio,
            language=None if language == 'auto' else language,
            batch_size=16
        )
        
        detected_language = result.get('language', language if language != 'auto' else 'unknown')
        update_progress(40, f"Detected language: {detected_language}")
        
        # Step 3: Align for word-level timestamps
        update_progress(45, "Aligning words for timestamps...")
        try:
            model_a, metadata = self._load_align_model(detected_language)
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self.device,
                return_char_alignments=False
            )
            update_progress(55, "Word alignment complete")
        except Exception as e:
            logger.warning(f"Word alignment skipped for {detected_language}: {e}")
            update_progress(55, f"Word alignment skipped ({detected_language})")
        
        # Step 4: Diarization (most time-consuming on CPU)
        update_progress(60, "Loading speaker diarization model...")
        diarizer = self._load_diarization_pipeline()
        
        diarize_kwargs = {}
        if num_speakers:
            diarize_kwargs['num_speakers'] = num_speakers
        if min_speakers:
            diarize_kwargs['min_speakers'] = min_speakers
        if max_speakers:
            diarize_kwargs['max_speakers'] = max_speakers
        
        update_progress(65, "Identifying speakers (this takes a while on CPU)...")
        diarize_segments = diarizer(audio, **diarize_kwargs)
        
        # Step 5: Assign speakers to words
        update_progress(85, "Assigning speakers to transcript...")
        result = whisperx.assign_word_speakers(diarize_segments, result)
        
        # Process final output
        segments_with_speakers = []
        speakers_stats = {}
        
        for seg in result.get('segments', []):
            speaker = seg.get('speaker', 'UNKNOWN')
            
            # Track speaker stats
            if speaker not in speakers_stats:
                speakers_stats[speaker] = {
                    'id': speaker,
                    'label': f"Speaker {len(speakers_stats) + 1}",
                    'total_time': 0,
                    'turns': 0
                }
            
            duration = seg['end'] - seg['start']
            speakers_stats[speaker]['total_time'] += duration
            speakers_stats[speaker]['turns'] += 1
            
            segment_data = {
                'speaker': speaker,
                'speaker_label': speakers_stats[speaker]['label'],
                'text': seg['text'].strip(),
                'start': seg['start'],
                'end': seg['end']
            }
            
            # Include word-level data with speaker info
            if 'words' in seg:
                segment_data['words'] = [
                    {
                        'word': w.get('word', ''),
                        'start': w.get('start', seg['start']),
                        'end': w.get('end', seg['end']),
                        'speaker': w.get('speaker', speaker)
                    }
                    for w in seg['words']
                ]
            
            segments_with_speakers.append(segment_data)
        
        # Build full text
        full_text = ' '.join(seg['text'] for seg in segments_with_speakers)
        total_duration = segments_with_speakers[-1]['end'] if segments_with_speakers else 0
        
        # Sort speakers by total time
        speakers_summary = sorted(
            speakers_stats.values(), 
            key=lambda x: x['total_time'], 
            reverse=True
        )
        
        logger.info(f"Pipeline complete: {len(speakers_stats)} speakers, {len(segments_with_speakers)} segments")
        
        return {
            'text': full_text,
            'language': detected_language,
            'segments_with_speakers': segments_with_speakers,
            'speakers_summary': speakers_summary,
            'num_speakers': len(speakers_stats),
            'duration': total_duration
        }
    
    def diarize_from_file(self, file_path, num_speakers=None):
        """
        Standalone diarization (without transcription).
        
        Returns timeline of speaker turns.
        """
        logger.info(f"Diarizing: {file_path}")
        
        audio = whisperx.load_audio(file_path)
        diarizer = self._load_diarization_pipeline()
        
        kwargs = {'num_speakers': num_speakers} if num_speakers else {}
        diarize_segments = diarizer(audio, **kwargs)
        
        # Process diarization output - WhisperX returns a DataFrame
        timeline = []
        speakers = {}
        
        # diarize_segments is a pandas DataFrame with columns: segment, label, speaker, start, end
        for _, row in diarize_segments.iterrows():
            speaker = row['speaker']
            
            if speaker not in speakers:
                speakers[speaker] = {
                    'id': speaker,
                    'label': f"Speaker {len(speakers) + 1}",
                    'total_time': 0,
                    'turns': 0
                }
            
            duration = row['end'] - row['start']
            speakers[speaker]['total_time'] += duration
            speakers[speaker]['turns'] += 1
            
            timeline.append({
                'start': float(row['start']),
                'end': float(row['end']),
                'speaker': speaker,
                'speaker_label': speakers[speaker]['label']
            })
        
        return {
            'timeline': timeline,
            'speakers': list(speakers.values()),
            'num_speakers': len(speakers)
        }
