import os
from pydub import AudioSegment

SUPPORTED_FORMATS = ['wav', 'mp3', 'ogg', 'flac', 'm4a', 'webm', 'mp4']
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def get_audio_duration(file_path):
    """Get duration of audio file in seconds"""
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0  # Convert milliseconds to seconds
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0

def validate_audio_file(file):
    """Validate uploaded audio file"""
    errors = []
    
    # Check if file exists
    if not file:
        errors.append("No file provided")
        return {'valid': False, 'errors': errors}
    
    # Check filename
    filename = file.filename if hasattr(file, 'filename') else str(file)
    
    # Check file extension
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in SUPPORTED_FORMATS:
        errors.append(f"Unsupported format: {ext}. Supported: {', '.join(SUPPORTED_FORMATS)}")
    
    # Check file size (if we can)
    if hasattr(file, 'seek') and hasattr(file, 'tell'):
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if size > MAX_FILE_SIZE:
            errors.append(f"File too large: {size / (1024*1024):.1f}MB. Max: {MAX_FILE_SIZE / (1024*1024):.0f}MB")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'filename': filename,
        'extension': ext
    }

def clean_transcript(text):
    """Clean and normalize transcript text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove common filler words (optional, can be configurable)
    # fillers = ['um', 'uh', 'hmm', 'ah']
    
    return text.strip()

def merge_adjacent_segments(segments, max_gap=1.0):
    """Merge adjacent segments from the same speaker"""
    if not segments:
        return segments
    
    merged = []
    current = segments[0].copy()
    
    for segment in segments[1:]:
        # Check if same speaker and close enough
        if (segment.get('speaker') == current.get('speaker') and 
            segment['start'] - current['end'] <= max_gap):
            # Merge
            current['end'] = segment['end']
            current['text'] = current['text'] + ' ' + segment['text']
        else:
            merged.append(current)
            current = segment.copy()
    
    merged.append(current)
    return merged
