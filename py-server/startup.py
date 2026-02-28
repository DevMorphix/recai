#!/usr/bin/env python3
"""
Production startup script with validation and diagnostics.
Run: python startup.py
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Verify production environment setup."""
    logger.info("=" * 60)
    logger.info("PRODUCTION ENVIRONMENT CHECK")
    logger.info("=" * 60)
    
    errors = []
    warnings = []
    
    # Check HuggingFace token
    hf_token = os.getenv('HUGGINGFACE_TOKEN')
    if not hf_token:
        errors.append("❌ HUGGINGFACE_TOKEN not set (required)")
    else:
        logger.info(f"✓ HUGGINGFACE_TOKEN set: {hf_token[:10]}...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        errors.append(f"❌ Python 3.8+ required (found {sys.version_info.major}.{sys.version_info.minor})")
    else:
        logger.info(f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check GPU availability
    try:
        import torch
        logger.info(f"✓ PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            logger.info(f"✓ GPU Available: {torch.cuda.get_device_name(0)}")
            logger.info(f"  - CUDA Version: {torch.version.cuda}")
            logger.info(f"  - GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        else:
            warnings.append("⚠ GPU not available (CPU will be used, slower)")
    except ImportError:
        errors.append("❌ PyTorch not installed")
    
    # Check required packages
    required_packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'torchaudio': 'torchaudio',
        'pyannote.audio': 'pyannote.audio',
        'transformers': 'transformers'
    }
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            logger.info(f"✓ {package_name} installed")
        except ImportError:
            errors.append(f"❌ {package_name} not installed (pip install {package_name})")
    
    # Check .env file
    env_file = Path('.env')
    if not env_file.exists():
        warnings.append("⚠ No .env file found (using environment variables)")
    else:
        logger.info("✓ .env file found")
    
    # Check ffmpeg (Windows)
    if sys.platform == 'win32':
        import shutil
        if not shutil.which('ffmpeg'):
            warnings.append("⚠ ffmpeg not in PATH (audio processing may fail)")
        else:
            logger.info("✓ ffmpeg found in PATH")
    
    # Report results
    logger.info("=" * 60)
    
    if errors:
        logger.error("ERRORS FOUND:")
        for error in errors:
            logger.error(f"  {error}")
        return False
    
    if warnings:
        logger.warning("WARNINGS:")
        for warning in warnings:
            logger.warning(f"  {warning}")
    
    logger.info("✓ Environment check passed!")
    return True

def check_model_access():
    """Test HuggingFace model access."""
    logger.info("=" * 60)
    logger.info("TESTING HUGGINGFACE MODEL ACCESS")
    logger.info("=" * 60)
    
    try:
        from services.diarization_service import DiarizationService
        
        logger.info("Initializing diarization service...")
        service = DiarizationService()
        service._initialize()
        
        logger.info("✓ Model loaded successfully!")
        logger.info(f"  - Device: {service.device}")
        logger.info(f"  - Pipeline: {type(service.pipeline).__name__}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        logger.error("Ensure HUGGINGFACE_TOKEN is valid and you have internet access")
        return False

def start_server():
    """Start Flask server."""
    logger.info("=" * 60)
    logger.info("STARTING AI MICROSERVICE")
    logger.info("=" * 60)
    
    try:
        from app import app
        
        logger.info("Flask server starting on http://0.0.0.0:5001")
        logger.info("Health check: curl http://localhost:5001/health")
        logger.info("Press Ctrl+C to stop")
        logger.info("-" * 60)
        
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,
            use_reloader=False
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Step 1: Environment check
    if not check_environment():
        logger.error("Please fix environment issues and try again")
        sys.exit(1)
    
    # Step 2: Model access check
    if not check_model_access():
        logger.error("Please fix model access issues and try again")
        sys.exit(1)
    
    # Step 3: Start server
    start_server()
