# Quick Start Guide - Production Deployment

## 5-Minute Setup

### 1. Get HuggingFace Token
```bash
# Visit: https://huggingface.co/settings/tokens
# Create token, copy it
```

### 2. Set Environment
```bash
# In py-server/ directory, create .env file:
HUGGINGFACE_TOKEN=hf_your_token_here
```

### 3. Verify Setup
```bash
cd py-server
python startup.py
```

This will:
- ✅ Check environment
- ✅ Download + cache model (~5-10 mins first time)
- ✅ Start server on http://localhost:5001
- ✅ Show health check endpoint

### 4. Test It
```bash
# In another terminal:
curl http://localhost:5001/health

# Should show GPU info if available
```

## Common Commands

### Check GPU Status
```bash
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
```

### Clear Model Cache
```bash
rm -rf ~/.cache/huggingface/hub/*
```

### Run with Verbose Logging
```bash
export PYTHONUNBUFFERED=1
python startup.py
```

### Test Diarization Endpoint
```bash
curl -X POST -F "audio=@test_audio.wav" http://localhost:5001/api/diarize
```

### View Logs
```bash
# Real-time
tail -f ai-service.log

# Last 50 lines
tail -50 ai-service.log

# Search for errors
grep ERROR ai-service.log
```

## Troubleshooting

### "HUGGINGFACE_TOKEN not set"
```bash
# Check .env file exists in py-server/
# Or export in terminal:
export HUGGINGFACE_TOKEN=hf_your_token_here
```

### No GPU Found
```bash
# If you have GPU, verify drivers:
# 1. Update GPU drivers
# 2. Reinstall CUDA toolkit
# 3. Reinstall torch with CUDA:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory (OOM)
```bash
# Force CPU mode:
export CUDA_VISIBLE_DEVICES=-1
python startup.py
```

### Model Download Stuck
```bash
# Cancel (Ctrl+C), clear cache, retry:
rm -rf ~/.cache/huggingface/hub/*
python startup.py
```

## Performance Tips

### For Speed (GPU)
```bash
# Pre-download model on first run
# Then serve multiple requests
# Cache is persistent between restarts
```

### For Accuracy
```bash
# Default model (pyannote 3.1) is optimal
# No tuning needed for production
```

### For Cost
```bash
# Model caching = no re-download
# Single GPU instance can handle 10-15 concurrent requests
# 300MB disk space for cache
```

## Deployment Checklist

Before going live:

- [ ] `.env` file with HUGGINGFACE_TOKEN
- [ ] `python startup.py` runs without errors
- [ ] Health check returns GPU info
- [ ] Test audio file processes correctly
- [ ] `ai-service.log` created with no errors
- [ ] Read PRODUCTION_SETUP.md for advanced config

## Quick API Reference

### Diarization
```bash
POST /api/diarize
- audio: WAV file
- num_speakers: (optional) number of speakers
Response: {speakers, timeline, num_speakers}
```

### Transcription + Diarization
```bash
POST /api/transcribe-with-speakers
- audio: WAV file
- language: (optional) auto, en, ml, etc
- num_speakers: (optional)
Response: {transcript, speakers, timeline, duration}
```

### Health Check
```bash
GET /health
Response: {status, gpu_available, torch_version, features}
```

## Support Resources

- **Logs**: `ai-service.log` (detailed error info)
- **Full Guide**: `PRODUCTION_SETUP.md`
- **Updates**: `PRODUCTION_UPDATES.md`
- **HuggingFace**: https://huggingface.co/pyannote
- **pyannote.audio**: https://github.com/pyannote/pyannote-audio

---

**That's it! Your production service is ready.** 🎉
