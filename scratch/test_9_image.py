"""
test_9_image.py
───────────────
Test synthetic 9.jpg prescription against meta/llama-3.2-11b-vision-instruct.
"""
import os
import sys
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.nvidia_service import nvidia_service

def test_9():
    # Create image matching 9.jpg from screenshot
    img = np.ones((700, 700, 3), dtype=np.uint8) * 255
    lines = [
        "C.O. Jones",
        "25 El Caro Street",
        "Pleasantville, OH 43320",
        "Date: March 10, 2009",
        "Patient Name: Joseph McIntyre",
        "Address: 25 El Caro Street",
        "DOB: 12/26/1998",
        "Allergies: NKDA",
        "Weight: 65 kg",
        "RX:",
        "Azithromycin 200 mg/5mL",
        "Day 1: 15 mL",
        "Day 2: 7.5 mL",
        "Dispense 5 mg/mL solution, 30 mL",
        "Refills: 0",
        "CO Jones, ARNP"
    ]
    y = 40
    for line in lines:
        cv2.putText(img, line, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        y += 38

    _, buf = cv2.imencode(".jpg", img)
    img_bytes = buf.tobytes()

    print("Sending prescription to NVIDIA Vision Model (meta/llama-3.2-11b-vision-instruct)...")
    res, logs = nvidia_service.extract_prescription_nvidia(img_bytes, filename="9.jpg")

    print("\n--- Logs ---")
    for l in logs:
        print(l)

    print("\n--- Result ---")
    if res:
        print("Doctor Name:", res.get("doctor", {}).get("name"))
        print("Patient Name:", res.get("patient", {}).get("name"))
        print("Prescription Date:", res.get("prescription_date"))
        print("Raw Text:", res.get("raw_text"))
        print("Medicines:")
        for m in res.get("medicines", []):
            print(" ", m)

if __name__ == "__main__":
    test_9()
