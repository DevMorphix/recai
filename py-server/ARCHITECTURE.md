# System Architecture - Production Deployment

## Request Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Request                            │
│              (Audio File + Optional Num Speakers)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │   Flask App (app.py)               │
        │  ┌──────────────────────────────┐  │
        │  │ GET /health                  │  │
        │  │ - Returns GPU/CPU status     │  │
        │  │ - Torch version              │  │
        │  └──────────────────────────────┘  │
        │  ┌──────────────────────────────┐  │
        │  │ POST /api/diarize            │  │
        │  │ - Validates audio file       │  │
        │  │ - Calls DiarizationService   │  │
        │  └──────────────────────────────┘  │
        │  ┌──────────────────────────────┐  │
        │  │ POST /api/transcribe-with... │  │
        │  │ - Combines transcription +   │  │
        │  │   diarization                │  │
        │  └──────────────────────────────┘  │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  DiarizationService (lazy loaded)  │
        │  ┌──────────────────────────────┐  │
        │  │ Check Cache:                 │  │
        │  │ _cached_pipeline != None?    │  │
        │  └──────────┬───────────────────┘  │
        │             │                      │
        │      ┌──────┴──────┐               │
        │      │ YES   │ NO  │               │
        │      ▼             ▼               │
        │   Use Cache    Load Model          │
        │      │             │               │
        │      │  ┌──────────┘               │
        │      │  │                         │
        │      └─►┌──────────────────────┐  │
        │         │ Pipeline Ready       │  │
        │         │ (GPU or CPU)         │  │
        │         └──────┬───────────────┘  │
        └────────────────┼──────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │   Inference Engine                     │
        │  ┌──────────────────────────────────┐  │
        │  │ Save audio to temp file          │  │
        │  │ (if from upload)                 │  │
        │  └──────────┬───────────────────────┘  │
        │             │                          │
        │      ┌──────▼──────┐                   │
        │      │ GPU Available                   │
        │      └──────┬──────┬─────────────────┐ │
        │             │      │                 │ │
        │      ┌──────▼──┐  │        ┌────────▼─┴─┐
        │      │ CUDA    │  │        │ CPU        │
        │      │ (fast)  │  │        │ (slow)     │
        │      └────┬────┘  │        │ ~20s/min   │
        │           │       │        └────────┬───┘
        │      2-5s │/min   │               │
        │           │       │               │
        │      ┌────┴──┬────┴──────────────┘
        │      │                │
        │      ▼                ▼
        │  ┌──────────────────────────┐
        │  │ Diarization Result       │
        │  │ - Speaker IDs            │
        │  │ - Timeline (start/end)   │
        │  │ - Speaker labels         │
        │  └────────────┬─────────────┘
        │               │
        │      ┌────────▼─────────┐
        │      │ Cleanup temp file │
        │      │ (exception-safe)  │
        │      └────────┬──────────┘
        │               │
        └───────────────┼──────────────────────┘
                        │
                        ▼
        ┌────────────────────────────────────┐
        │    Logging                         │
        │  ┌──────────────────────────────┐  │
        │  │ ai-service.log               │  │
        │  │ - Timestamps                 │  │
        │  │ - INFO/WARNING/ERROR         │  │
        │  │ - Request details            │  │
        │  └──────────────────────────────┘  │
        │  ┌──────────────────────────────┐  │
        │  │ Console (real-time)          │  │
        │  │ - Model loading              │  │
        │  │ - GPU info                   │  │
        │  │ - Errors                     │  │
        │  └──────────────────────────────┘  │
        └────────────────────────────────────┘
                        │
                        ▼
        ┌────────────────────────────────────┐
        │   JSON Response to Client          │
        │  {                                 │
        │    "speakers": [...],              │
        │    "timeline": [...],              │
        │    "num_speakers": 3,              │
        │    "success": true                 │
        │  }                                 │
        └────────────────────────────────────┘
```

## Caching Architecture

```
┌─────────────────────────────────────────────┐
│     Python Process (Single Instance)        │
│                                             │
│  Global Variables:                         │
│  ┌─────────────────────────────────────┐   │
│  │ _cached_pipeline = None (initially) │   │
│  │ _cached_device = None               │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  First Request:                            │
│  ┌─────────────────────────────────────┐   │
│  │ 1. Load model from disk/HF          │   │
│  │ 2. Move to GPU (if available)       │   │
│  │ 3. Store in _cached_pipeline        │   │
│  │ 4. Time: 10-15 seconds              │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Requests 2+:                              │
│  ┌─────────────────────────────────────┐   │
│  │ 1. Check _cached_pipeline (not None)│   │
│  │ 2. Reuse existing pipeline          │   │
│  │ 3. Time: <1 second overhead         │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Disk Cache:                               │
│  ┌─────────────────────────────────────┐   │
│  │ ~/.cache/huggingface/hub/           │   │
│  │ ├── models--pyannote--speaker-...   │   │
│  │ │   ├── pytorch_model.bin (~300MB)  │   │
│  │ │   └── ...                         │   │
│  │ └── (persists across restarts)      │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌──────────────────────────────────┐
│   Request Received               │
└───────────────┬──────────────────┘
                │
    ┌───────────▼───────────┐
    │ Is HUGGINGFACE_TOKEN  │
    │ set?                  │
    └─────┬─────────┬───────┘
          │ YES     │ NO
          │         ▼
          │    ┌──────────────────────────────┐
          │    │ ERROR: ValueError            │
          │    │ Message: "HUGGINGFACE_TOKEN  │
          │    │ not set. Get token at        │
          │    │ huggingface.co/settings"     │
          │    │ Log: ERROR level             │
          │    │ Response: 500 with error msg │
          │    └──────────────────────────────┘
          │
          ▼
    ┌──────────────────────┐
    │ Is model cached?     │
    └──┬──────────┬────────┘
       │ YES      │ NO
       │          ▼
       │     ┌────────────────┐
       │     │ Load from disk │
       │     │ (300MB)        │
       │     │ 10-15 seconds  │
       │     └────────┬───────┘
       │              │
       └──────┬───────┘
              │
              ▼
       ┌──────────────────────┐
       │ Is audio file valid? │
       └──┬──────────┬────────┘
          │ YES      │ NO
          │          ▼
          │     ┌──────────────────────────┐
          │     │ ERROR: FileNotFoundError │
          │     │ Log: ERROR level         │
          │     │ Response: 400 Bad file   │
          │     └──────────────────────────┘
          │
          ▼
       ┌──────────────────┐
       │ Run Pipeline     │
       │ (on GPU or CPU)  │
       └──┬──────────┬────┘
          │ SUCCESS  │ ERROR
          │          ▼
          │     ┌──────────────────────────┐
          │     │ ERROR: RuntimeError      │
          │     │ Log: Full traceback      │
          │     │ Response: 500 with msg   │
          │     └──────────────────────────┘
          │
          ▼
    ┌─────────────────┐
    │ Clean Up Temp   │
    │ File            │
    │ (exception-safe)│
    └────────┬────────┘
             │
             ▼
    ┌──────────────────────┐
    │ Return JSON Response │
    │ with Results         │
    └──────────────────────┘
```

## GPU vs CPU Performance

```
GPU (NVIDIA RTX 4090)           CPU (Intel i7)
─────────────────────           ──────────────
┌─────────────────────┐         ┌──────────────┐
│ 30-sec audio        │         │ 30-sec audio │
│ ▓▓▓ 2-3 seconds     │         │ ████ 15-20s  │
│                     │         │              │
│ 60-sec audio        │         │ 60-sec audio │
│ ▓▓▓▓ 4-5 seconds    │         │ █████████ 25-30s
│                     │         │              │
│ Concurrent reqs     │         │ Concurrent   │
│ ▓▓▓▓▓▓▓▓▓▓ 10-15    │         │ ██ 1-2       │
└─────────────────────┘         └──────────────┘

Speedup: 10-15x faster with GPU
```

## Deployment Architecture (Cloud)

```
┌──────────────────────────────────────────────────────────┐
│                     Load Balancer                        │
│                   (nginx/HAProxy)                        │
└────────────┬─────────────────────────────┬───────────────┘
             │                             │
    ┌────────▼──────┐           ┌──────────▼────────┐
    │  AI Service   │           │   AI Service      │
    │  Instance 1   │           │   Instance 2      │
    │               │           │                   │
    │  ┌─────────┐  │           │  ┌─────────┐     │
    │  │ GPU +   │  │           │  │ GPU +   │     │
    │  │ Cache   │  │           │  │ Cache   │     │
    │  └─────────┘  │           │  └─────────┘     │
    └───────────────┘           └───────────────────┘
           │                             │
    ┌──────▼─────────────────────────────▼──────┐
    │  Shared HuggingFace Cache (NFS/S3)        │
    │  ~/.cache/huggingface/hub/ (~300MB)       │
    │  (optional but recommended)               │
    └──────────────────────────────────────────┘
```

## Files Overview

```
py-server/
├── app.py                          (Flask server with logging)
├── startup.py                      (Automated startup + validation)
├── services/
│   └── diarization_service.py      (GPU support + caching + error handling)
├── ai-service.log                  (Generated on first run)
├── .env                            (HuggingFace token)
│
├── QUICK_START.md                  (5-minute setup)
├── PRODUCTION_SETUP.md             (Complete guide)
├── PRODUCTION_UPDATES.md           (What changed)
├── DEPLOYMENT_SUMMARY.md           (This file + more)
└── requirements.txt                (Python dependencies)
```

---

**Architecture designed for:** ✅ GPU acceleration ✅ Model caching ✅ Error resilience ✅ Easy scaling
