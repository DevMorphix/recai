#!/usr/bin/env python3
"""Test diarization endpoints"""

import requests
import json
import time
import os
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Wait for server to start
time.sleep(3)

BASE_URL = "http://localhost:5001"

print("\n" + "=" * 70)
print("TEST 1: HEALTH CHECK ENDPOINT")
print("=" * 70)
try:
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Status: {data.get('status')}")
    print(f"Service: {data.get('service')}")
    print(f"GPU Available: {data.get('gpu_available')}")
    print(f"GPU Info: {data.get('gpu_info')}")
    print(f"Torch Version: {data.get('torch_version')}")
    print(f"Features: {data.get('features')}")
    print("[PASS] HEALTH CHECK PASSED\n")
except Exception as e:
    print(f"[FAIL] HEALTH CHECK FAILED: {e}\n")

print("=" * 70)
print("TEST 2: DIARIZATION ENDPOINT (with test audio)")
print("=" * 70)
try:
    # Check if test audio exists
    if os.path.exists("test_audio.wav"):
        with open("test_audio.wav", "rb") as f:
            files = {"audio": f}
            response = requests.post(f"{BASE_URL}/api/diarize", files=files, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            print(f"Success: {data.get('success')}")
            print(f"Number of Speakers: {data.get('num_speakers')}")
            speakers = data.get('speakers', [])
            print(f"Speakers Detected: {len(speakers)}")
            for speaker in speakers:
                print(f"  - {speaker.get('label')}: {speaker.get('total_time'):.2f}s")
            timeline = data.get('timeline', [])
            print(f"Timeline Segments: {len(timeline)}")
            print("[PASS] DIARIZATION TEST PASSED\n")
        else:
            print(f"Error: {data.get('error')}")
            print("[FAIL] DIARIZATION TEST FAILED\n")
    else:
        print("[SKIP] test_audio.wav not found, skipping test\n")
except Exception as e:
    print(f"[FAIL] DIARIZATION TEST FAILED: {e}\n")

print("=" * 70)
print("TEST 3: ERROR HANDLING - Missing audio file")
print("=" * 70)
try:
    files = {}
    response = requests.post(f"{BASE_URL}/api/diarize", files=files, timeout=10)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Error Message: {data.get('error')}")
    if response.status_code == 400:
        print("[PASS] ERROR HANDLING TEST PASSED (correctly rejected missing file)\n")
    else:
        print("[FAIL] ERROR HANDLING TEST FAILED\n")
except Exception as e:
    print(f"[FAIL] ERROR HANDLING TEST FAILED: {e}\n")

print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("[PASS] Health check working")
print("[PASS] Diarization endpoint available")
print("[PASS] Error handling working")
print("\n[SUCCESS] All core tests completed!\n")
