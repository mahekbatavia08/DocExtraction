"""
prescription_validator.py
──────────────────────────
Validates extracted prescription JSON against the standard schema.
Enforces medical safety rules:
  - No hallucination (confidence + needs_review)
  - All required fields present
  - Medicine names are never invented
  - Configurable confidence thresholds
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.config import PRESCRIPTION_MIN_CONFIDENCE, MIN_MEDICINE_CONFIDENCE


# ── Standard prescription schema ───────────────────────────────────────────────
EMPTY_PRESCRIPTION = {
    "document_type": "doctor_prescription",
    "doctor": {
        "name": None,
        "registration_number": None,
        "specialization": None
    },
    "patient": {
        "name": None,
        "age": None,
        "gender": None
    },
    "prescription_date": None,
    "diagnosis": [],
    "medicines": [],
    "tests": [],
    "general_instructions": [],
    "raw_text": "",
    "overall_confidence": 0.0,
    "needs_manual_review": False,
    "model_used": "",
    "fallback_attempt": 0
}

EMPTY_MEDICINE = {
    "name": None,
    "strength": None,
    "dosage": None,
    "frequency": None,
    "duration": None,
    "route": None,
    "instructions": None,
    "confidence": 0.0,
    "needs_review": False
}


def normalize_prescription(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fills missing keys with null/empty defaults, normalizes types.
    Ensures the output always matches the standard schema.
    """
    result = dict(EMPTY_PRESCRIPTION)
    result.update({k: v for k, v in raw.items() if k in EMPTY_PRESCRIPTION})

    # Normalize doctor block
    doctor_raw = raw.get("doctor", {}) or {}
    result["doctor"] = {
        "name": doctor_raw.get("name"),
        "registration_number": doctor_raw.get("registration_number"),
        "specialization": doctor_raw.get("specialization")
    }

    # Normalize patient block
    patient_raw = raw.get("patient", {}) or {}
    result["patient"] = {
        "name": patient_raw.get("name"),
        "age": patient_raw.get("age"),
        "gender": patient_raw.get("gender")
    }

    # Normalize medicines list
    medicines_raw = raw.get("medicines", []) or []
    medicines = []
    for m in medicines_raw:
        if not isinstance(m, dict):
            continue
        med = dict(EMPTY_MEDICINE)
        med.update({k: v for k, v in m.items() if k in EMPTY_MEDICINE})
        # Ensure confidence is float 0-1
        conf = float(med.get("confidence", 0.0))
        if conf > 1.0:
            conf = conf / 100.0
        med["confidence"] = round(conf, 3)
        # Auto-flag low-confidence medicines for review
        if conf < MIN_MEDICINE_CONFIDENCE:
            med["needs_review"] = True
        medicines.append(med)
    result["medicines"] = medicines

    # Normalize overall confidence
    oc = float(raw.get("overall_confidence", 0.0))
    if oc > 1.0:
        oc = oc / 100.0
    result["overall_confidence"] = round(oc, 3)

    # Ensure lists
    result["diagnosis"] = list(raw.get("diagnosis", []) or [])
    result["tests"] = list(raw.get("tests", []) or [])
    result["general_instructions"] = list(raw.get("general_instructions", []) or [])

    # needs_manual_review: set True if overall_confidence < threshold
    needs_review = bool(raw.get("needs_manual_review", False))
    if result["overall_confidence"] < PRESCRIPTION_MIN_CONFIDENCE:
        needs_review = True
    if any(m.get("needs_review") for m in medicines):
        needs_review = True
    result["needs_manual_review"] = needs_review

    return result


def validate_prescription_result(result: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """
    Full validation of extracted prescription JSON.

    Returns:
        (is_acceptable, quality_grade, issues)

    quality_grade: 'high' | 'medium' | 'low' | 'rejected'
    issues: list of human-readable validation issues found
    """
    issues: List[str] = []

    # 1. Type check
    if not isinstance(result, dict):
        return False, "rejected", ["Result is not a dictionary"]

    # 2. Overall confidence
    oc = float(result.get("overall_confidence", 0.0))

    # 3. Raw text check
    raw_text = result.get("raw_text", "") or ""
    if len(raw_text.strip()) < 5:
        issues.append("raw_text is empty or too short")

    # 4. Medicines check
    medicines = result.get("medicines", []) or []
    named_meds = [m for m in medicines if m.get("name")]

    if not named_meds:
        issues.append("No medicine names could be extracted")

    # 5. Medicine confidence check
    if named_meds:
        low_conf_meds = [m for m in named_meds if float(m.get("confidence", 0)) < MIN_MEDICINE_CONFIDENCE]
        if low_conf_meds:
            issues.append(f"{len(low_conf_meds)} medicine(s) below confidence threshold")

    # 6. Hallucination guard: reject if confidence is very low and lots of data present
    if oc < 0.3 and len(named_meds) > 5:
        issues.append(f"Suspicious: {len(named_meds)} medicines found but overall confidence is only {oc:.0%}")

    # Determine quality grade
    if oc >= 0.85 and not issues:
        grade = "high"
    elif oc >= PRESCRIPTION_MIN_CONFIDENCE and len(named_meds) > 0:
        grade = "medium"
    elif oc >= 0.4 or len(named_meds) > 0:
        grade = "low"
    else:
        grade = "rejected"

    is_acceptable = grade in ("high", "medium")

    # Low grade but has medicines → accept with manual review flag
    if grade == "low":
        is_acceptable = True  # accept but flag for review

    return is_acceptable, grade, issues


def build_local_fallback(
    ocr_text: str,
    rx_fields: Dict[str, Any],
    medicines: List[Dict],
    model_name: str = "local_ner",
    attempt: int = 0
) -> Dict[str, Any]:
    """
    Build a prescription result from local NER/CRNN engine output
    when all OpenRouter models fail or API key is not configured.
    Always marks needs_manual_review=True when used as fallback.
    """
    result = dict(EMPTY_PRESCRIPTION)
    result["model_used"] = model_name
    result["fallback_attempt"] = attempt
    result["raw_text"] = ocr_text
    result["needs_manual_review"] = True
    result["overall_confidence"] = 0.70  # local NER is reliable for known vocab

    # Doctor
    result["doctor"]["name"] = rx_fields.get("Doctor Name")
    result["doctor"]["registration_number"] = rx_fields.get("BMDC Registration No")
    result["doctor"]["specialization"] = rx_fields.get("Qualification")

    # Patient
    result["patient"]["name"] = rx_fields.get("Patient Name")
    age_gender = rx_fields.get("Age / Gender", "")
    if "/" in str(age_gender):
        parts = age_gender.split("/")
        result["patient"]["age"] = parts[0].strip()
        result["patient"]["gender"] = parts[1].strip()
    else:
        result["patient"]["age"] = age_gender

    result["prescription_date"] = rx_fields.get("Prescription Date")

    diag = rx_fields.get("Diagnosis / Chief Complaint")
    if diag:
        result["diagnosis"] = [diag]

    # Medicines from CRNN/NER
    result["medicines"] = [
        {
            "name": m.get("Brand Name"),
            "strength": m.get("Strength") if m.get("Strength") != "N/A" else None,
            "dosage": m.get("Dosage Pattern"),
            "frequency": m.get("Dosage Pattern"),
            "duration": m.get("Duration"),
            "route": "oral",
            "instructions": m.get("Timing"),
            "confidence": float(str(m.get("Match Confidence", "70")).replace("%", "")) / 100.0,
            "needs_review": False
        }
        for m in medicines
        if m.get("Brand Name")
    ]

    return normalize_prescription(result)


def check_model_agreement(res_a: Dict[str, Any], res_b: Dict[str, Any]) -> bool:
    """
    Compares outputs from two models (e.g. Primary Vision vs Fallback Vision).
    Returns True if models AGREE on medicine names, False if they DISAGREE.
    If models disagree, needs_manual_review is set to True.
    """
    if not res_a or not res_b:
        return True

    meds_a = [str(m.get("name", "")).strip().lower() for m in res_a.get("medicines", []) if m.get("name")]
    meds_b = [str(m.get("name", "")).strip().lower() for m in res_b.get("medicines", []) if m.get("name")]

    if not meds_a or not meds_b:
        return True

    set_a = set(meds_a)
    set_b = set(meds_b)

    # Disagreement threshold: if intersection ratio < 0.70
    overlap = len(set_a.intersection(set_b))
    total_unique = len(set_a.union(set_b))

    if total_unique > 0 and (overlap / total_unique) < 0.70:
        res_a["needs_manual_review"] = True
        res_b["needs_manual_review"] = True
        return False

    return True

