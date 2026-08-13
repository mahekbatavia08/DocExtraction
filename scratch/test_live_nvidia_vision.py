"""
test_live_nvidia_vision.py
───────────────────────────
Test live vision models on NVIDIA API with sample image.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.nvidia_service import nvidia_service

def test():
    # Find sample image
    img_path = "9.jpg"
    if not os.path.exists(img_path):
        img_path = os.path.join("scratch", "test_prescription.jpg")
    
    if not os.path.exists(img_path):
        print(f"No test image found at {img_path}")
        return

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    print(f"Testing live image extraction ({len(img_bytes)} bytes) using NVIDIA API...")
    res, logs = nvidia_service.extract_prescription_nvidia(img_bytes, filename=os.path.basename(img_path))
    
    print("\n--- Pipeline Audit Logs ---")
    for l in logs:
        print(l)

    print("\n--- Final Extracted Result ---")
    if res:
        print("Doctor Name:", res.get("doctor", {}).get("name"))
        print("Patient Name:", res.get("patient", {}).get("name"))
        print("Date:", res.get("prescription_date"))
        print("Medicines Count:", len(res.get("medicines", [])))
        print("Medicines Details:")
        for m in res.get("medicines", []):
            print("  -", m)
    else:
        print("Result is None!")

if __name__ == "__main__":
    test()
