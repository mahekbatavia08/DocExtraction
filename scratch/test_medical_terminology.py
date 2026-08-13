"""
test_medical_terminology.py
───────────────────────────
Dedicated test suite for MedicalAbbreviationExpander + expanded medicine database.
Covers: frequency expansion, dosage pattern decoding, route expansion,
        timing expansion, diagnosis expansion, strength normalization,
        full medicine dict expansion, and prefix-based cursive matching.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services.medical_abbreviations import (
    medical_abbreviation_expander,
    FREQUENCY_EXPANSIONS,
    ROUTE_EXPANSIONS,
    TIMING_EXPANSIONS,
    DIAGNOSIS_EXPANSIONS,
    DOSAGE_PATTERN_EXPANSIONS,
)
from backend.services.medical_prescription_extractor import (
    MEDICINE_BD_DATABASE,
    MEDICINE_PREFIXES,
    MedicalPrescriptionExtractor,
)

PASS = "[PASS]"
FAIL = "[FAIL]"
errors = []

def check(test_name: str, actual, expected, match_type: str = "eq"):
    if match_type == "eq":
        ok = actual == expected
    elif match_type == "in":
        ok = expected.lower() in str(actual).lower()
    elif match_type == "not_none":
        ok = actual is not None
    elif match_type == "gt":
        ok = actual > expected
    else:
        ok = False

    if ok:
        print(f"  {PASS} {test_name}")
    else:
        msg = f"  {FAIL} {test_name}: got {repr(actual)!r}, expected {repr(expected)!r}"
        print(msg)
        errors.append(msg)

print("=" * 70)
print("  MEDICAL TERMINOLOGY & ABBREVIATION EXPANSION TEST SUITE")
print("=" * 70)

# ── Test Group 1: Frequency Abbreviations ───────────────────────────────────
print("\n--- Group 1: Frequency Abbreviation Expansion ---")
exp = medical_abbreviation_expander
check("bd -> twice daily", exp.expand_frequency("bd"), "twice daily")
check("BD -> twice daily", exp.expand_frequency("BD"), "twice daily")
check("b.d. -> twice daily", exp.expand_frequency("b.d."), "twice daily")
check("tds -> three times daily", exp.expand_frequency("tds"), "three times daily")
check("TDS -> three times daily", exp.expand_frequency("TDS"), "three times daily")
check("t.d.s. -> three times daily", exp.expand_frequency("t.d.s."), "three times daily")
check("od -> once daily", exp.expand_frequency("od"), "once daily")
check("OD -> once daily", exp.expand_frequency("OD"), "once daily")
check("qid -> four times daily", exp.expand_frequency("qid"), "four times daily")
check("prn -> as needed", exp.expand_frequency("prn"), "as needed")
check("PRN -> as needed", exp.expand_frequency("PRN"), "as needed")
check("sos -> as needed (if required)", exp.expand_frequency("sos"), "as needed (if required)")
check("SOS -> as needed (if required)", exp.expand_frequency("SOS"), "as needed (if required)")
check("stat -> immediately", exp.expand_frequency("stat"), "immediately (once)")
check("eod -> every other day", exp.expand_frequency("eod"), "every other day")
check("q4h -> every 4 hours", exp.expand_frequency("q4h"), "every 4 hours")
check("q12h -> every 12 hours", exp.expand_frequency("q12h"), "every 12 hours")

# ── Test Group 2: Dosage Pattern Expansion ──────────────────────────────────
print("\n--- Group 2: Dosage Pattern Decoding (1-0-1 style) ---")
check("1-0-1 -> Twice daily morning+night", exp.expand_frequency("1-0-1"), "Twice daily (Morning + Night)")
check("1+0+1 -> Twice daily morning+night", exp.expand_frequency("1+0+1"), "Twice daily (Morning + Night)")
check("1-1-1 -> Three times daily", exp.expand_frequency("1-1-1"), "Three times daily (Morning + Afternoon + Night)")
check("0-0-1 -> Once at night", exp.expand_frequency("0-0-1"), "Once daily (at Night)")
check("1-0-0 -> Once morning", exp.expand_frequency("1-0-0"), "Once daily (Morning)")
check("1-1-0 -> Twice morning+afternoon", exp.expand_frequency("1-1-0"), "Twice daily (Morning + Afternoon)")
check("2-0-2 -> Twice 2 tablets", exp.expand_dosage_pattern("2-0-2"), "Twice daily (2 tablets — Morning + Night)")
check("1-1-1-1 -> Four times daily", exp.expand_dosage_pattern("1-1-1-1"), "Four times daily")

# ── Test Group 3: Route of Administration ───────────────────────────────────
print("\n--- Group 3: Route of Administration Expansion ---")
check("iv -> intravenous", exp.expand_route("iv"), "intravenous")
check("i.v. -> intravenous", exp.expand_route("i.v."), "intravenous")
check("im -> intramuscular", exp.expand_route("im"), "intramuscular")
check("sc -> subcutaneous", exp.expand_route("sc"), "subcutaneous")
check("po -> oral", exp.expand_route("po"), "oral (by mouth)")
check("sl -> sublingual", exp.expand_route("sl"), "sublingual (under tongue)")
check("inh -> inhaled", exp.expand_route("inh"), "inhaled")
check("top -> topical", exp.expand_route("top"), "topical")
check("pr -> rectal", exp.expand_route("pr"), "rectal")

# ── Test Group 4: Timing/Meal Relation ──────────────────────────────────────
print("\n--- Group 4: Timing / Meal Relation Expansion ---")
check("ac -> before meals", exp.expand_timing("ac"), "before meals")
check("a.c. -> before meals", exp.expand_timing("a.c."), "before meals")
check("pc -> after meals", exp.expand_timing("pc"), "after meals")
check("hs -> at bedtime", exp.expand_timing("hs"), "at bedtime")
check("h.s. -> at bedtime", exp.expand_timing("h.s."), "at bedtime")

# ── Test Group 5: Diagnosis Abbreviations ───────────────────────────────────
print("\n--- Group 5: Diagnosis Abbreviation Expansion ---")
check("HTN -> Hypertension", exp.expand_diagnosis("HTN"), "Hypertension")
check("DM -> Diabetes Mellitus", exp.expand_diagnosis("DM"), "Diabetes Mellitus")
check("T2DM -> Type 2 DM", exp.expand_diagnosis("T2DM"), "Type 2 Diabetes Mellitus")
check("UTI -> Urinary Tract Infection", exp.expand_diagnosis("UTI"), "Urinary Tract Infection")
check("COPD -> Chronic Obstructive...", exp.expand_diagnosis("COPD"), "Chronic Obstructive Pulmonary Disease")
check("NKDA -> No Known Drug Allergies", exp.expand_diagnosis("NKDA"), "No Known Drug Allergies")
check("URTI -> Upper Respiratory...", exp.expand_diagnosis("URTI"), "Upper Respiratory Tract Infection")
check("CAD -> Coronary Artery Disease", exp.expand_diagnosis("CAD"), "Coronary Artery Disease")
check("TB -> Tuberculosis", exp.expand_diagnosis("TB"), "Tuberculosis")

# ── Test Group 6: Strength Normalization ────────────────────────────────────
print("\n--- Group 6: Strength Normalization ---")
check("500mg -> 500 mg", exp.normalize_strength("500mg"), "500 mg")
check("200mg/5ml -> 200 mg/5 mL", exp.normalize_strength("200mg/5ml"), "200 mg/5 mL")
check("250mcg -> 250 mcg", exp.normalize_strength("250mcg"), "250 mcg")
check("1g -> 1 g", exp.normalize_strength("1g"), "1 g")
check("1000IU -> 1000 IU", exp.normalize_strength("1000IU"), "1000 IU")

# ── Test Group 7: Full Medicine Dict Expansion ──────────────────────────────
print("\n--- Group 7: Full Medicine Entry Expansion ---")
med1 = {"name": "Amoxicillin", "frequency": "tds", "route": "po", "instructions": "ac",
        "dosage": "1-1-1", "strength": "500mg", "confidence": 0.85}
expanded1 = exp.expand_medicine(med1)
check("Medicine freq tds -> three times daily", expanded1["frequency"], "three times daily")
check("Medicine route po -> oral", expanded1["route"], "oral (by mouth)")
check("Medicine instructions ac -> before meals", expanded1["instructions"], "before meals")
check("Medicine dosage 1-1-1 pattern -> decoded", expanded1["dosage"], "Three times daily (Morning + Afternoon + Night)")
check("Medicine strength 500mg normalized", expanded1["strength"], "500 mg")
check("Medicine abbreviation_expanded flag set", expanded1.get("abbreviation_expanded"), True)

med2 = {"name": "Ceftriaxone", "frequency": "od", "route": "iv", "dosage": "1-0-0",
        "strength": "1g", "instructions": "", "confidence": 0.9}
expanded2 = exp.expand_medicine(med2)
check("Ceftriaxone freq od -> once daily", expanded2["frequency"], "once daily")
check("Ceftriaxone route iv -> intravenous", expanded2["route"], "intravenous")
check("Ceftriaxone dosage 1-0-0 -> once morning", expanded2["dosage"], "Once daily (Morning)")
check("Ceftriaxone strength 1g normalized", expanded2["strength"], "1 g")

# ── Test Group 8: Medicine DB Size Check ────────────────────────────────────
print("\n--- Group 8: Expanded Medicine Database Checks ---")
check("DB size > 400 entries", len(MEDICINE_BD_DATABASE), 400, match_type="gt")
check("Clindamycin in DB", MEDICINE_BD_DATABASE.get("Clindamycin"), "Clindamycin")
check("Ceftriaxone in DB", MEDICINE_BD_DATABASE.get("Ceftriaxone"), "Ceftriaxone")
check("Rosuvastatin in DB", MEDICINE_BD_DATABASE.get("Rosuvastatin"), "Rosuvastatin")
check("Empagliflozin in DB", MEDICINE_BD_DATABASE.get("Empagliflozin"), "Empagliflozin")
check("Ondansetron in DB", MEDICINE_BD_DATABASE.get("Ondansetron"), "Ondansetron")
check("Morphine in DB", MEDICINE_BD_DATABASE.get("Morphine"), "Morphine")
check("Tramadol in DB", MEDICINE_BD_DATABASE.get("Tramadol"), "Tramadol")
check("Olanzapine in DB", MEDICINE_BD_DATABASE.get("Olanzapine"), "Olanzapine")
check("Hydroxychloroquine in DB", MEDICINE_BD_DATABASE.get("Hydroxychloroquine"), "Hydroxychloroquine")
check("Insulin in DB", MEDICINE_BD_DATABASE.get("Insulin"), "Insulin")
check("Warfarin in DB", MEDICINE_BD_DATABASE.get("Warfarin"), "Warfarin")
check("Colchicine in DB", MEDICINE_BD_DATABASE.get("Colchicine"), "Colchicine")
check("Fluconazole in DB", MEDICINE_BD_DATABASE.get("Fluconazole"), "Fluconazole")

# ── Test Group 9: MEDICINE_PREFIXES Coverage ────────────────────────────────
print("\n--- Group 9: Prefix Table Coverage ---")
check("Prefix table size > 80 entries", len(MEDICINE_PREFIXES), 80, match_type="gt")
check("'clind' prefix -> Clindamycin", MEDICINE_PREFIXES.get("clind", (None,))[0], "Clindamycin")
check("'azith' prefix -> Azithromycin", MEDICINE_PREFIXES.get("azith", (None,))[0], "Azithromycin")
check("'cipro' prefix -> Ciprofloxacin", MEDICINE_PREFIXES.get("cipro", (None,))[0], "Ciprofloxacin")
check("'furosem' prefix -> Furosemide", MEDICINE_PREFIXES.get("furosem", (None,))[0], "Furosemide")
check("'olanza' prefix -> Olanzapine", MEDICINE_PREFIXES.get("olanza", (None,))[0], "Olanzapine")
check("'tramad' prefix -> Tramadol", MEDICINE_PREFIXES.get("tramad", (None,))[0], "Tramadol")
check("'fluox' prefix -> Fluoxetine", MEDICINE_PREFIXES.get("fluox", (None,))[0], "Fluoxetine")

print("\n" + "=" * 70)
if errors:
    print(f"  {len(errors)} TEST(S) FAILED:")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print(f"  ALL {70} MEDICAL TERMINOLOGY TESTS PASSED CLEANLY!")
print("=" * 70)
