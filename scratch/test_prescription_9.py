"""
test_prescription_9.py
───────────────────────
Verification test for prescription 9.jpg (C.O. Jones, Joseph McIntyre, Azithromycin).
"""

import sys, os
sys.path.insert(0, os.path.abspath("."))

from backend.services.medical_prescription_extractor import medical_prescription_extractor

rx_text_9 = """
C.O. Jones
25 El Caro Street
Pleasantville, OH 43320

Date: March 10, 2009
Patient Name: Joseph McIntyre
Address:
DOB: 12/26/1998
Allergies: NKDA
Weight: 65 kg

RX: Azithromycin 200 mg/5mL
Day 1: 15 mL
Day 2: 7.5 mL

Dispense 5 mg/mL solution, 30 mL

Refills: 0
CO Jones, ARNP
"""

res = medical_prescription_extractor.extract_prescription_data([], raw_full_text=rx_text_9)
fields = res["fields"]
medicines = res["medicines"]

print("=" * 60)
print("  PRESCRIPTION 9.JPG EXTRACTION VERIFICATION RESULTS")
print("=" * 60)
print("  Doctor Name       :", fields.get("Doctor Name"))
print("  Qualification     :", fields.get("Qualification"))
print("  Patient Name      :", fields.get("Patient Name"))
print("  Date of Birth     :", fields.get("Date of Birth"))
print("  Prescription Date :", fields.get("Prescription Date"))
print("  Address           :", fields.get("Address"))
print("  Weight            :", fields.get("Weight"))
print("  Allergies         :", fields.get("Allergies"))
print("  Medicines Count   :", fields.get("Prescribed Medicines Count"))

print("\n  Medicines Table:")
for m in medicines:
    print("   -", m.get("Brand Name"), "|", m.get("Generic Name"), "| Strength:", m.get("Strength"), "| Dose:", m.get("Dosage Pattern"))

print("=" * 60)

assert fields.get("Doctor Name") in ["C.O. Jones", "Dr. CO Jones", "Dr. C.O. Jones"] or "Jones" in fields.get("Doctor Name")
assert fields.get("Patient Name") == "Joseph Mcintyre" or fields.get("Patient Name") == "Joseph McIntyre"
assert fields.get("Prescription Date") == "March 10, 2009"
assert fields.get("Date of Birth") == "12/26/1998"
assert "Azithromycin" in [m.get("Brand Name") for m in medicines] or "Azithromycin" in [m.get("Generic Name") for m in medicines]
print("  [PASS] ALL VERIFICATION CHECKS PASSED FOR 9.JPG!\n")
