import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    PORT = int(os.getenv('PORT', 5001))
    
    # AI Services
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
    
    # Models
    DEFAULT_WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'medium')
    CACHE_DIR = os.getenv('CACHE_DIR', './models_cache')
    
    # Audio Processing
    MAX_AUDIO_SIZE = int(os.getenv('MAX_AUDIO_SIZE', 100 * 1024 * 1024))  # 100MB
    SUPPORTED_FORMATS = ['wav', 'mp3', 'ogg', 'flac', 'm4a', 'webm']
    
    # Languages
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'ml': 'Malayalam',
        'hi': 'Hindi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'kn': 'Kannada',
        'mr': 'Marathi'
    }
