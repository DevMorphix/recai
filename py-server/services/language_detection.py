import whisper
import os

class LanguageDetector:
    def __init__(self):
        self.model = None
        self._initialized = False
        self.supported_languages = {
            'en': 'English',
            'ml': 'Malayalam',
            'hi': 'Hindi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'mr': 'Marathi',
            'bn': 'Bengali',
            'gu': 'Gujarati',
            'pa': 'Punjabi',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic'
        }
    
    def _initialize(self):
        """Lazy initialization of the Whisper model"""
        if self._initialized:
            return
        self.model = whisper.load_model("base")
        self._initialized = True
    
    def detect(self, audio_file):
        """Detect language from audio"""
        temp_dir = os.getenv('TEMP', '/tmp')
        temp_path = os.path.join(temp_dir, audio_file.filename)
        audio_file.save(temp_path)
        
        try:
            return self.detect_from_file(temp_path)
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def detect_from_file(self, file_path):
        """Detect language from file"""
        self._initialize()
        
        # Load audio and pad/trim it to fit 30 seconds
        audio = whisper.load_audio(file_path)
        audio = whisper.pad_or_trim(audio)
        
        # Make log-Mel spectrogram
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        
        # Detect language
        _, probs = self.model.detect_language(mel)
        detected_lang = max(probs, key=probs.get)
        
        return {
            'language': detected_lang,
            'language_name': self.supported_languages.get(detected_lang, detected_lang),
            'confidence': probs[detected_lang],
            'supported': detected_lang in self.supported_languages,
            'all_probabilities': {
                lang: prob for lang, prob in sorted(
                    probs.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]
            }
        }
