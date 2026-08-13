"""
test_prescription_pipeline.py
──────────────────────────────
Verification test suite for Doctor's Handwritten Prescription OCR & Prediction Engine.
Aligned with Doctor's Handwritten Prescription BD Dataset (Kaggle).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.medical_prescription_extractor import medical_prescription_extractor
from backend.services.universal_pipeline import run_universal_pipeline

def test_fuzzy_medicine_correction():
    print("\n--- Test 1: Fuzzy Medicine Name Correction (78-Class BD Dataset) ---")
    brand, generic, conf = medical_prescription_extractor.fuzzy_match_medicine("Azipen")
    assert brand == "Azipen", f"Expected Azipen, got {brand}"
    assert generic == "Azithromycin", f"Expected Azithromycin, got {generic}"

    brand2, generic2, conf2 = medical_prescription_extractor.fuzzy_match_medicine("Omeprazol")
    assert "Omeprazole" in generic2, f"Expected Omeprazole generic, got {generic2}"

    brand3, generic3, conf3 = medical_prescription_extractor.fuzzy_match_medicine("Napa")
    assert generic3 == "Paracetamol", f"Expected Paracetamol, got {generic3}"
    print(f"  Azipen -> {brand} ({generic}) [{conf}%]")
    print(f"  Omeprazol -> {brand2} ({generic2}) [{conf2}%]")
    print(f"  Napa -> {brand3} ({generic3}) [{conf3}%]")
    print("[PASS] Test 1 PASSED SUCCESSFULLY!")


def test_prescription_parser():
    print("\n--- Test 2: Prescription BD Extraction Pipeline ---")
    ocr_text = """
    Dr. Rashmi Sharma, MBBS, MD
    BMDC Reg No: 88721
    Patient Name: Kanhaiya Kumar
    Age: 28Y / Male  Date: 12/08/2026
    Diagnosis: Acute Pharyngitis

    Rx
    Tab. Azipen 500mg  1+0+0  After Food  5 Days
    Tab. Omep 20mg   1+0+0  Before Food 7 Days
    Tab. Napa 650mg  1+0+1  After Food  3 Days
    """

    res = run_universal_pipeline(raw_text_input=ocr_text, filename="dr_prescription.png")
    fields = res.get("fields", {})
    tables = res.get("tables", [])

    assert res["document_type"] == "Medical Prescription"
    assert "Doctor Name" in fields
    assert len(tables) > 0
    assert len(tables[0]["rows"]) > 0
    print(f"  Doctor Name: {fields.get('Doctor Name')}")
    print(f"  Prescribed Medicines Count: {fields.get('Prescribed Medicines Count')}")
    print(f"  Table rows: {len(tables[0]['rows'])}")
    for row in tables[0]["rows"]:
        print(f"    {row}")
    print("[PASS] Test 2 PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_fuzzy_medicine_correction()
    test_prescription_parser()
    print("\nALL DOCTOR PRESCRIPTION BD PIPELINE TESTS PASSED 100%!")
