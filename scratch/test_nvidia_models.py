"""
test_nvidia_models.py
──────────────────────
Test fetching available models from NVIDIA API catalog.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.nvidia_service import nvidia_service

def check():
    print("NVIDIA Configured:", nvidia_service.is_configured())
    models = nvidia_service.get_available_models()
    print(f"Total catalog models fetched: {len(models)}")
    if models:
        print("Sample models:", models[:15])
        vision_models = [m for m in models if "vision" in m.lower() or "vl" in m.lower() or "neva" in m.lower() or "ocr" in m.lower() or "nemotron" in m.lower()]
        print("Vision/Nemotron models found:", vision_models)
    else:
        print("Could not fetch models (key may be unconfigured or invalid).")

if __name__ == "__main__":
    check()
