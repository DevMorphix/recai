# Set up ffmpeg PATH before any audio imports
import os
import sys
import logging

# ============================================
# CRITICAL: PyTorch 2.6+ Compatibility Patch
# Must be done BEFORE any torch imports
# ============================================
import torch

# Monkey-patch torch.load to always use weights_only=False
_torch_load_original = torch.load
def _torch_load_patched(f, *args, **kwargs):
    kwargs['weights_only'] = False
    return _torch_load_original(f, *args, **kwargs)
torch.load = _torch_load_patched

# Also patch the serialization module
import torch.serialization
torch.serialization.load = _torch_load_patched
# ============================================

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai-service.log')
    ]
)
logger = logging.getLogger(__name__)

if sys.platform == 'win32':
    ffmpeg_paths = [
        r'C:\ffmpeg\bin',
        r'C:\Program Files\ffmpeg\bin',
        os.path.expanduser(r'~\AppData\Local\Microsoft\WinGet\Links'),
        os.path.expanduser(r'~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin'),
    ]
    current_path = os.environ.get('PATH', '')
    for ffmpeg_path in ffmpeg_paths:
        if os.path.exists(ffmpeg_path) and ffmpeg_path not in current_path:
            os.environ['PATH'] = ffmpeg_path + os.pathsep + current_path
            current_path = os.environ['PATH']

# Compatibility patches BEFORE any audio/pyannote imports
import torchaudio

if not hasattr(torchaudio, 'list_audio_backends'):
    torchaudio.list_audio_backends = lambda: ['soundfile']

# Create AudioDecoder FIRST before any imports reference it
class AudioDecoder:
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return torchaudio.load(*args, **kwargs)

torchaudio.AudioDecoder = AudioDecoder

# Also set it as a global so it can be imported
import sys
sys.modules['torchaudio.AudioDecoder'] = AudioDecoder

# Note: torch.load is already patched at the top of the file

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from utils.helpers import validate_audio_file

load_dotenv()

app = Flask(__name__)
CORS(app)

# Lazy import services to allow basic routes to work without all dependencies
_whisperx_service = None
_language_detector = None
_audio_processor = None

def get_whisperx_service():
    global _whisperx_service
    if _whisperx_service is None:
        from services.whisperx_service import WhisperXService
        _whisperx_service = WhisperXService()
    return _whisperx_service

def get_language_detector():
    global _language_detector
    if _language_detector is None:
        from services.language_detection import LanguageDetector
        _language_detector = LanguageDetector()
    return _language_detector

def get_audio_processor():
    global _audio_processor
    if _audio_processor is None:
        from services.audio_processor import AudioProcessor
        _audio_processor = AudioProcessor()
    return _audio_processor

@app.route('/health', methods=['GET'])
def health_check():
    import torch
    gpu_available = torch.cuda.is_available()
    gpu_info = ""
    if gpu_available:
        gpu_info = f" - {torch.cuda.get_device_name(0)}"
    
    return jsonify({
        'status': 'healthy',
        'service': 'python-ai-microservice',
        'features': ['transcription', 'diarization', 'multilingual', 'malayalam'],
        'gpu_available': gpu_available,
        'gpu_info': gpu_info,
        'torch_version': torch.__version__
    })

@app.route('/api/detect-language', methods=['POST'])
def detect_language():
    """Detect language from audio"""
    try:
        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({'error': 'No audio file'}), 400
        
        # Validate file
        validation = validate_audio_file(audio_file)
        if not validation['valid']:
            return jsonify({'error': validation['errors']}), 400
        
        result = get_language_detector().detect(audio_file)
        
        return jsonify({
            'success': True,
            'language': result['language'],
            'language_name': result['language_name'],
            'confidence': result['confidence'],
            'supported_languages': result['supported'],
            'all_probabilities': result['all_probabilities']
        })
    except Exception as e:
        print(f"Error in detect_language: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe-advanced', methods=['POST'])
def transcribe_advanced():
    """Advanced transcription with language support using WhisperX"""
    try:
        audio_file = request.files.get('audio')
        language = request.form.get('language', 'auto')  # auto, en, ml, hi, ta, etc.
        model_size = request.form.get('model_size', 'base')
        
        if not audio_file:
            return jsonify({'error': 'No audio file'}), 400
        
        # Validate file
        validation = validate_audio_file(audio_file)
        if not validation['valid']:
            return jsonify({'error': validation['errors']}), 400
        
        result = get_whisperx_service().transcribe(
            audio_file, 
            language=language,
            model_size=model_size
        )
        
        return jsonify({
            'success': True,
            'transcript': result['text'],
            'segments': result['segments'],
            'language': result['detected_language'],
            'duration': result['duration']
        })
    except Exception as e:
        print(f"Error in transcribe_advanced: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/diarize', methods=['POST'])
def diarize_speakers():
    """Speaker diarization using WhisperX"""
    try:
        audio_file = request.files.get('audio')
        num_speakers = request.form.get('num_speakers', None)
        
        if not audio_file:
            return jsonify({'error': 'No audio file'}), 400
        
        # Validate file
        validation = validate_audio_file(audio_file)
        if not validation['valid']:
            return jsonify({'error': validation['errors']}), 400
        
        # Save temp file
        audio_proc = get_audio_processor()
        temp_path = audio_proc.save_temp(audio_file)
        
        try:
            result = get_whisperx_service().diarize_from_file(
                temp_path,
                num_speakers=int(num_speakers) if num_speakers else None
            )
            
            return jsonify({
                'success': True,
                'speakers': result['speakers'],
                'timeline': result['timeline'],
                'num_speakers': result['num_speakers']
            })
        finally:
            audio_proc.cleanup(temp_path)
    except Exception as e:
        print(f"Error in diarize_speakers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe-with-speakers', methods=['POST'])
def transcribe_with_speakers():
    """Complete WhisperX pipeline: transcription + alignment + speaker diarization"""
    try:
        audio_file = request.files.get('audio')
        language = request.form.get('language', 'auto')
        num_speakers = request.form.get('num_speakers', None)
        min_speakers = request.form.get('min_speakers', None)
        max_speakers = request.form.get('max_speakers', None)
        model_size = request.form.get('model_size', 'base')
        
        if not audio_file:
            return jsonify({'error': 'No audio file'}), 400
        
        # Validate file
        validation = validate_audio_file(audio_file)
        if not validation['valid']:
            return jsonify({'error': validation['errors']}), 400
        
        # Run unified WhisperX pipeline
        result = get_whisperx_service().transcribe_with_speakers(
            audio_file,
            language=language,
            model_size=model_size,
            num_speakers=int(num_speakers) if num_speakers else None,
            min_speakers=int(min_speakers) if min_speakers else None,
            max_speakers=int(max_speakers) if max_speakers else None
        )
        
        return jsonify({
            'success': True,
            'language': result['language'],
            'num_speakers': result['num_speakers'],
            'transcript': result['text'],
            'segments_with_speakers': result['segments_with_speakers'],
            'speakers_summary': result['speakers_summary'],
            'duration': result['duration']
        })
            
    except Exception as e:
        print(f"Error in transcribe_with_speakers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """Audio preprocessing - noise reduction, normalization"""
    try:
        audio_file = request.files.get('audio')
        operations = request.form.getlist('operations')  # ['denoise', 'normalize', 'trim']
        
        if not audio_file:
            return jsonify({'error': 'No audio file'}), 400
        
        if not operations:
            operations = ['normalize']  # Default operation
        
        # Validate file
        validation = validate_audio_file(audio_file)
        if not validation['valid']:
            return jsonify({'error': validation['errors']}), 400
        
        result = get_audio_processor().process(audio_file, operations)
        
        return jsonify({
            'success': True,
            'processed_url': result['url'],
            'operations_applied': result['operations']
        })
    except Exception as e:
        print(f"Error in process_audio: {e}")
        return jsonify({'error': str(e)}), 500

# ==================================================
# Queue-based endpoints for Node.js integration
# ==================================================

from services.task_queue import task_queue, TaskStatus

# Register task handlers
def _handle_transcribe_task(params, task_id, queue):
    """Handler for async transcription tasks."""
    queue.update_progress(task_id, 10, "Loading audio...")
    
    service = get_whisperx_service()
    
    # Load audio from temp file path
    temp_path = params['audio_path']
    language = params.get('language', 'auto')
    model_size = params.get('model_size', 'base')
    
    queue.update_progress(task_id, 20, "Loading model...")
    
    result = service.transcribe_from_file(
        temp_path,
        language=language,
        model_size=model_size
    )
    
    queue.update_progress(task_id, 90, "Finalizing...")
    
    # Cleanup temp file
    try:
        os.remove(temp_path)
    except:
        pass
    
    return {
        'transcript': result['text'],
        'segments': result['segments'],
        'language': result['detected_language'],
        'duration': result['duration']
    }


def _handle_full_pipeline_task(params, task_id, queue):
    """Handler for async full pipeline (transcribe + diarize) tasks."""
    queue.update_progress(task_id, 5, "Loading audio...")
    
    service = get_whisperx_service()
    
    temp_path = params['audio_path']
    language = params.get('language', 'auto')
    model_size = params.get('model_size', 'base')
    num_speakers = params.get('num_speakers')
    min_speakers = params.get('min_speakers')
    max_speakers = params.get('max_speakers')
    
    queue.update_progress(task_id, 10, "Loading Whisper model...")
    
    result = service.transcribe_with_speakers_from_file(
        temp_path,
        language=language,
        model_size=model_size,
        num_speakers=num_speakers,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
        progress_callback=lambda p, m: queue.update_progress(task_id, p, m)
    )
    
    # Cleanup temp file
    try:
        os.remove(temp_path)
    except:
        pass
    
    return {
        'language': result['language'],
        'num_speakers': result['num_speakers'],
        'transcript': result['text'],
        'segments_with_speakers': result['segments_with_speakers'],
        'speakers_summary': result['speakers_summary'],
        'duration': result['duration']
    }


# Register handlers
task_queue.register_handler('transcribe', _handle_transcribe_task)
task_queue.register_handler('full_pipeline', _handle_full_pipeline_task)


@app.route('/api/queue/submit', methods=['POST'])
def queue_submit():
    """Submit a task to the queue (for Node.js integration)."""
    try:
        audio_file = request.files.get('audio')
        task_type = request.form.get('task_type', 'full_pipeline')  # transcribe, full_pipeline
        
        if not audio_file:
            return jsonify({'error': 'No audio file'}), 400
        
        # Validate file
        validation = validate_audio_file(audio_file)
        if not validation['valid']:
            return jsonify({'error': validation['errors']}), 400
        
        # Save to temp file (will be cleaned up by handler)
        audio_proc = get_audio_processor()
        temp_path = audio_proc.save_temp(audio_file)
        
        # Build params
        params = {
            'audio_path': temp_path,
            'language': request.form.get('language', 'auto'),
            'model_size': request.form.get('model_size', 'base'),
        }
        
        # Add optional params for full_pipeline
        if task_type == 'full_pipeline':
            if request.form.get('num_speakers'):
                params['num_speakers'] = int(request.form.get('num_speakers'))
            if request.form.get('min_speakers'):
                params['min_speakers'] = int(request.form.get('min_speakers'))
            if request.form.get('max_speakers'):
                params['max_speakers'] = int(request.form.get('max_speakers'))
        
        # Submit to queue
        task_id = task_queue.submit(task_type, params)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': 'pending',
            'queue_info': task_queue.get_queue_info()
        })
        
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/queue/status/<task_id>', methods=['GET'])
def queue_status(task_id):
    """Get the status of a queued task."""
    status = task_queue.get_status(task_id)
    if status:
        return jsonify(status)
    return jsonify({'error': 'Task not found'}), 404


@app.route('/api/queue/result/<task_id>', methods=['GET'])
def queue_result(task_id):
    """Get the result of a completed task."""
    status = task_queue.get_status(task_id)
    if not status:
        return jsonify({'error': 'Task not found'}), 404
    
    if status['status'] == 'completed':
        return jsonify({
            'success': True,
            'result': status['result'],
            'duration': status['duration']
        })
    elif status['status'] == 'failed':
        return jsonify({
            'success': False,
            'error': status['error']
        }), 500
    else:
        return jsonify({
            'success': False,
            'status': status['status'],
            'progress': status['progress'],
            'progress_message': status['progress_message']
        }), 202


@app.route('/api/queue/cancel/<task_id>', methods=['POST'])
def queue_cancel(task_id):
    """Cancel a pending task."""
    if task_queue.cancel(task_id):
        return jsonify({'success': True, 'message': 'Task cancelled'})
    return jsonify({'error': 'Cannot cancel task (already processing or not found)'}), 400


@app.route('/api/queue/info', methods=['GET'])
def queue_info():
    """Get queue statistics."""
    return jsonify(task_queue.get_queue_info())


if __name__ == '__main__':
    # Start task queue worker
    task_queue.start()
    
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    # GPU info
    import torch
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"🚀 GPU Detected: {gpu_name} ({gpu_mem:.1f} GB)")
    else:
        print("⚠️  No GPU detected - running on CPU (slower)")
    
    print(f"🐍 Python AI Service starting on http://localhost:{port}")
    print(f"📋 Queue system enabled for Node.js integration")
    app.run(host='0.0.0.0', port=port, debug=debug)
