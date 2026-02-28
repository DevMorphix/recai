import whisper
import torch
import os

class TranscriptionService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models = {}
        
    def load_model(self, model_size='medium'):
        """Load Whisper model"""
        if model_size not in self.models:
            # Using standard openai-whisper
            self.models[model_size] = whisper.load_model(model_size, device=self.device)
        return self.models[model_size]
    
    def transcribe(self, audio_file, language='auto', model_size='medium'):
        """Transcribe audio with language support"""
        model = self.load_model(model_size)
        
        # Save to temp file
        temp_dir = os.getenv('TEMP', '/tmp')
        temp_path = os.path.join(temp_dir, audio_file.filename)
        audio_file.save(temp_path)
        
        try:
            # Transcribe
            result = model.transcribe(
                temp_path,
                language=None if language == 'auto' else language,
                task='transcribe'
            )
            
            # Process segments
            segment_list = []
            for segment in result.get('segments', []):
                segment_list.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text']
                })
            
            return {
                'text': result['text'].strip(),
                'segments': segment_list,
                'detected_language': result.get('language', 'unknown'),
                'duration': segment_list[-1]['end'] if segment_list else 0
            }
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def transcribe_from_file(self, file_path, language='auto', model_size='medium'):
        """Transcribe from file path"""
        model = self.load_model(model_size)
        
        result = model.transcribe(
            file_path,
            language=None if language == 'auto' else language,
            task='transcribe'
        )
        
        segment_list = []
        for segment in result.get('segments', []):
            segment_list.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text']
            })
        
        return {
            'text': result['text'].strip(),
            'segments': segment_list,
            'detected_language': result.get('language', 'unknown'),
            'duration': segment_list[-1]['end'] if segment_list else 0
        }
