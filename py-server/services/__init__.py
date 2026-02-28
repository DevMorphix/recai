# Lazy imports - services are imported when needed
__all__ = [
    'WhisperXService',
    'TranscriptionService',
    'DiarizationService', 
    'LanguageDetector',
    'AudioProcessor',
    'task_queue',
    'TaskQueue',
    'TaskStatus'
]

def __getattr__(name):
    if name == 'WhisperXService':
        from .whisperx_service import WhisperXService
        return WhisperXService
    elif name == 'TranscriptionService':
        from .transcription_service import TranscriptionService
        return TranscriptionService
    elif name == 'DiarizationService':
        from .diarization_service import DiarizationService
        return DiarizationService
    elif name == 'LanguageDetector':
        from .language_detection import LanguageDetector
        return LanguageDetector
    elif name == 'AudioProcessor':
        from .audio_processor import AudioProcessor
        return AudioProcessor
    elif name == 'task_queue':
        from .task_queue import task_queue
        return task_queue
    elif name == 'TaskQueue':
        from .task_queue import TaskQueue
        return TaskQueue
    elif name == 'TaskStatus':
        from .task_queue import TaskStatus
        return TaskStatus
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
