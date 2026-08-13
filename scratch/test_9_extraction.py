"""
test_9_extraction.py
────────────────────
Test direct local extraction on synthetic 9.jpg text.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.medical_prescription_extractor import medical_prescription_extractor

def test():
    raw_text = """
C.O. Jones
25 El Caro Street
Pleasantville, OH 43320

Date March 10, 2009
Patient Name: Joseph McIntyre
Address: 25 El Caro Street
DOB: 12/26/1998
Allergies: NKDA
Weight: 65 kg

RX:
Azithromycin 200 mg/5mL
Day 1: 15 mL
Day 2: 7.5 mL
Dispense 5 mg/mL solution, 30 mL
Refills: 0

CO Jones, ARNP
"""
    tokens = []
    res = medical_prescription_extractor.extract_prescription_data(tokens, raw_full_text=raw_text)
    
    print("--- Extracted Fields ---")
    for k, v in res.get("fields", {}).items():
        print(f"  {k}: {v}")

    print("\n--- Extracted Medicines ---")
    for m in res.get("medicines", []):
        print(" ", m)

if __name__ == "__main__":
    test()
