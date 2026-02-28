# Production Setup Guide - Speaker Diarization Service

## Overview
This service uses **pyannote.audio 3.1** (state-of-the-art speaker diarization) with GPU acceleration for production deployments.

## Prerequisites

### 1. HuggingFace Token (Free)
1. Create a free account at https://huggingface.co
2. Go to https://huggingface.co/settings/tokens
3. Create a new token with `read` access
4. Copy the token (starts with `hf_`)

### 2. GPU Setup (Optional but Recommended)

#### NVIDIA GPU (10-50x faster)
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"

# Install CUDA toolkit (if not already installed)
# Download from: https://developer.nvidia.com/cuda-downloads
```

#### CPU-Only (slower but works)
- No additional setup needed
- Diarization will run on CPU with ~5-10x slower inference

## Setup Instructions

### 1. Environment Variables
Create a `.env` file in `py-server/` directory:
```bash
# Required
HUGGINGFACE_TOKEN=hf_your_token_here

# Optional
HF_HOME=/path/to/huggingface/cache  # Model cache location
PYTHONUNBUFFERED=1
```

### 2. Install Dependencies
```bash
cd py-server

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install production requirements
pip install -r requirements.txt
```

### 3. Pre-Download Model (Recommended)
Run this once to cache the model locally (avoids first-run delay):
```bash
python -c "
import os
os.environ['HUGGINGFACE_TOKEN'] = 'hf_your_token_here'
from services.diarization_service import DiarizationService
service = DiarizationService()
service._initialize()
print('✓ Model cached successfully')
"
```

## Verification

### 1. Check GPU
```bash
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
```

### 2. Health Check
```bash
python app.py &
sleep 2
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "python-ai-microservice",
  "gpu_available": true,
  "gpu_info": "NVIDIA GeForce RTX 4090",
  "torch_version": "2.10.0+cu118"
}
```

### 3. Test Diarization
```bash
# After starting server: python app.py

# Test with sample audio
curl -X POST -F "audio=@test_audio.wav" http://localhost:5001/api/diarize
```

## Performance Characteristics

### With GPU (NVIDIA RTX 4090)
- 30-second audio: ~2-3 seconds
- 60-second audio: ~4-5 seconds
- Throughput: ~10-15 concurrent requests

### With CPU (Intel i7)
- 30-second audio: ~15-20 seconds
- 60-second audio: ~25-30 seconds
- Throughput: ~1-2 concurrent requests

## Model Caching

The service uses **global caching** to avoid reloading the model:
- First request: ~10-15 seconds (model loads from disk/HuggingFace)
- Subsequent requests: <1 second overhead per request

Cache location:
- Windows: `~/.cache/huggingface/hub/` (~300MB)
- Linux/Mac: `~/.cache/huggingface/hub/` (~300MB)

## Logging

Logs are written to:
1. **Console**: Real-time debugging
2. **File**: `py-server/ai-service.log` (permanent record)

### Log Levels
- `INFO`: Normal operation, model loading
- `WARNING`: Missing GPU, slower performance
- `ERROR`: Failed requests, configuration issues

Example log:
```
2025-01-22 15:34:22,123 - services.diarization_service - INFO - CUDA available: NVIDIA GeForce RTX 4090
2025-01-22 15:34:22,124 - services.diarization_service - INFO - Loading pyannote/speaker-diarization-3.1 model...
2025-01-22 15:34:35,567 - services.diarization_service - INFO - Pipeline loaded successfully on cuda
2025-01-22 15:34:40,123 - services.diarization_service - INFO - Processing audio file: meeting.wav
2025-01-22 15:34:42,456 - services.diarization_service - INFO - Diarization result: 3 speakers, 24 segments
```

## Troubleshooting

### "HUGGINGFACE_TOKEN environment variable is required"
```bash
# Check if token is set
echo $HUGGINGFACE_TOKEN

# Set token
export HUGGINGFACE_TOKEN=hf_your_token_here
```

### "name 'AudioDecoder' is not defined"
This is **fixed** in the current version. Ensure you have:
- torch 2.10.0+cpu (or CUDA variant)
- torchaudio 2.10.0+cpu (or CUDA variant)
- pyannote.audio 4.0.1+

### Model Download Stuck
```bash
# Clear cache and retry
rm -rf ~/.cache/huggingface/hub/*
python app.py  # Will re-download
```

### Out of Memory (OOM) on GPU
```bash
# Fallback to CPU
export CUDA_VISIBLE_DEVICES=-1
python app.py
```

## Docker Deployment

### Dockerfile Example
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY py-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY py-server/ .

ENV HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}
ENV HF_HOME=/app/.cache/huggingface

EXPOSE 5001

CMD ["python", "app.py"]
```

### Build & Run
```bash
docker build -t rec-ai-service .
docker run --gpus all -e HUGGINGFACE_TOKEN=hf_xxx -p 5001:5001 rec-ai-service
```

## Cloud Deployment

### AWS EC2
1. Use GPU instance (g4dn.xlarge or better)
2. Pre-install CUDA drivers
3. Set `HUGGINGFACE_TOKEN` in Systems Manager Parameter Store
4. Use EBS for HuggingFace cache persistence

### Google Cloud Run
1. Use CPU (GPU not recommended for auto-scaling)
2. Increase timeout to 120s
3. Set memory to 4GB minimum

### Azure Container Instances
1. Use GPU SKU (NC-series)
2. Set environment variables in deployment
3. Mount storage for HuggingFace cache

## Production Checklist

- [ ] HUGGINGFACE_TOKEN set in environment
- [ ] GPU driver installed and verified (if using GPU)
- [ ] Model pre-downloaded and cached
- [ ] Health check passing
- [ ] Test audio file processed successfully
- [ ] Logging configured and working
- [ ] Error handling tested (invalid audio, missing token, etc.)
- [ ] Performance baseline established
- [ ] Backup/recovery plan documented

## Support & Monitoring

### Key Metrics to Monitor
- Response time (per request)
- GPU utilization
- Memory usage
- Error rate
- Model loading time (first request)

### Recommended Monitoring Tools
- Prometheus + Grafana for metrics
- ELK Stack for logs
- DataDog/New Relic for APM

## References
- [pyannote.audio GitHub](https://github.com/pyannote/pyannote-audio)
- [HuggingFace Models](https://huggingface.co/pyannote)
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
