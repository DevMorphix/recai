from pydub import AudioSegment
from pydub.effects import normalize
import noisereduce as nr
import numpy as np
import os
import uuid

class AudioProcessor:
    def __init__(self):
        self.temp_dir = os.path.join(os.getenv('TEMP', '/tmp'), 'audio_processing')
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def save_temp(self, audio_file):
        """Save uploaded file to temp location"""
        temp_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_{audio_file.filename}")
        audio_file.save(temp_path)
        return temp_path
    
    def process(self, audio_file, operations):
        """Process audio with various operations"""
        temp_path = self.save_temp(audio_file)
        
        # Load audio
        audio = AudioSegment.from_file(temp_path)
        
        applied_operations = []
        
        # Apply operations
        if 'normalize' in operations:
            audio = normalize(audio)
            applied_operations.append('normalize')
        
        if 'denoise' in operations:
            # Convert to numpy array for noise reduction
            samples = np.array(audio.get_array_of_samples())
            rate = audio.frame_rate
            
            # Reduce noise
            reduced = nr.reduce_noise(y=samples.astype(np.float32), sr=rate)
            
            # Convert back to AudioSegment
            audio = AudioSegment(
                reduced.astype(np.int16).tobytes(),
                frame_rate=rate,
                sample_width=audio.sample_width,
                channels=audio.channels
            )
            applied_operations.append('denoise')
        
        if 'trim' in operations:
            # Trim silence from beginning and end
            audio = self._trim_silence(audio)
            applied_operations.append('trim')
        
        # Save processed audio
        output_path = os.path.join(self.temp_dir, f"processed_{uuid.uuid4()}.wav")
        audio.export(output_path, format="wav")
        
        # Cleanup input temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            'url': output_path,
            'operations': applied_operations
        }
    
    def _trim_silence(self, audio, silence_threshold=-40):
        """Trim silence from audio"""
        # Simple implementation - find non-silent parts
        # More sophisticated trim using pydub's detect_silence could be added
        try:
            from pydub.silence import detect_leading_silence
            
            start_trim = detect_leading_silence(audio, silence_threshold=silence_threshold)
            end_trim = detect_leading_silence(audio.reverse(), silence_threshold=silence_threshold)
            
            duration = len(audio)
            trimmed = audio[start_trim:duration-end_trim]
            
            return trimmed if len(trimmed) > 0 else audio
        except Exception:
            return audio
    
    def merge_transcription_diarization(self, segments, timeline):
        """Merge transcription segments with speaker timeline"""
        merged = []
        
        for segment in segments:
            seg_start = segment['start']
            seg_end = segment['end']
            
            # Find overlapping speaker
            speaker = None
            max_overlap = 0
            
            for turn in timeline:
                # Calculate overlap
                overlap_start = max(seg_start, turn['start'])
                overlap_end = min(seg_end, turn['end'])
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    speaker = turn['speaker_label']
            
            merged.append({
                'start': seg_start,
                'end': seg_end,
                'text': segment['text'],
                'speaker': speaker or 'Unknown'
            })
        
        return merged
    
    def cleanup(self, file_path):
        """Remove temporary file"""
        if os.path.exists(file_path):
            os.remove(file_path)
