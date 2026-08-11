"""
validation_service.py
─────────────────────
Deterministic Validation Engine & Evidence Matching System.
- Validates field format rules (PAN, PIN, DOB, Name, Address).
- Performs OCR Evidence Verification (fuzzy matching against raw OCR text).
- Computes deterministic confidence score (0-100).
- Identifies model failure conditions (empty fields, unbacked hallucinations, malformed JSON).
"""

import re
import difflib
from typing import Dict, Any, List, Tuple
from backend.utils.validators import validate_pan_number, validate_verhoeff
from backend.config import CONFIDENCE_THRESHOLD

class DocumentValidationService:

    def check_ocr_evidence(self, target_value: str, raw_ocr_text: str, threshold: float = 0.55) -> bool:
        """
        Validates if target_value is supported by raw_ocr_text.
        Allows minor normalization differences (case, spaces, punctuation)
        but rejects completely unbacked hallucinations.
        """
        if not target_value or target_value.lower() in ["not found", "n/a", "null", "none", ""]:
            return True  # Empty/missing field is not a hallucinated fake value

        norm_target = re.sub(r'[^a-zA-Z0-9]', '', target_value.lower())
        norm_ocr = re.sub(r'[^a-zA-Z0-9]', '', raw_ocr_text.lower())

        if not norm_target:
            return True

        # Exact substring match after normalization
        if norm_target in norm_ocr:
            return True

        # Fuzzy sequence matcher across OCR lines
        ocr_lines = [re.sub(r'[^a-zA-Z0-9]', '', line.lower()) for line in raw_ocr_text.splitlines() if line.strip()]
        for line in ocr_lines:
            if not line:
                continue
            ratio = difflib.SequenceMatcher(None, norm_target, line).ratio()
            if ratio >= threshold:
                return True

        # Token-level overlap check for multi-word fields (Name, Address)
        target_tokens = set(re.findall(r'\w+', target_value.lower()))
        ocr_tokens = set(re.findall(r'\w+', raw_ocr_text.lower()))
        
        # Remove common document header stopwords
        stopwords = {"govt", "india", "department", "income", "tax", "card", "name", "father", "date", "birth"}
        meaningful_tokens = target_tokens - stopwords

        if meaningful_tokens:
            matches = meaningful_tokens.intersection(ocr_tokens)
            if len(matches) / len(meaningful_tokens) >= 0.5:
                return True

        return False

    def validate_extraction_output(self, extracted: Dict[str, Any], raw_ocr_text: str) -> Tuple[bool, float, List[str], Dict[str, Any]]:
        """
        Validates AI extraction output and computes deterministic confidence score (0-100).
        Scoring:
          - PAN valid format      : +20
          - Name supported        : +20
          - DOB valid format      : +10
          - Address supported     : +25
          - PIN valid format      : +15
          - OCR evidence match    : +10
        Total Max = 100
        Returns (is_passed, confidence_score, failure_reasons, sanitized_output)
        """
        score = 0.0
        reasons: List[str] = []
        sanitized = extracted.copy()

        name = str(extracted.get("name") or extracted.get("Cardholder Name") or "").strip()
        father_name = str(extracted.get("father_name") or extracted.get("Father's Name") or "").strip()
        dob = str(extracted.get("dob") or extracted.get("Date of Birth") or "").strip()
        pan = str(extracted.get("pan_number") or extracted.get("PAN Number") or "").strip()
        address = str(extracted.get("address") or extracted.get("full_address") or extracted.get("Address") or "").strip()
        pincode = str(extracted.get("pincode") or extracted.get("Pincode") or "").strip()

        # 1. PAN Validation (+20)
        if pan and pan.upper() != "NOT FOUND":
            pan_val = validate_pan_number(pan)
            if pan_val["is_valid"]:
                score += 20.0
                sanitized["pan_number"] = pan_val["pan_number"]
            else:
                reasons.append(f"Invalid PAN structure: '{pan}'")

        # 2. Name Validation & Evidence Match (+20)
        if name and name.upper() != "NOT FOUND":
            if self.check_ocr_evidence(name, raw_ocr_text):
                score += 20.0
            else:
                reasons.append(f"Extracted name '{name}' not supported by OCR evidence")
        else:
            reasons.append("Missing or empty name field")

        # 3. DOB Validation (+10)
        if dob and dob.upper() != "NOT FOUND":
            if re.search(r'\b(0[1-9]|[12]\d|3[01])[/.-](0[1-9]|1[0-2])[/.-](?:19|20)\d\d\b', dob):
                score += 10.0
            else:
                reasons.append(f"Invalid DOB format: '{dob}'")

        # 4. Address Validation & Evidence Match (+25)
        if address and address.upper() != "NOT FOUND" and len(address) >= 10:
            if self.check_ocr_evidence(address, raw_ocr_text, threshold=0.40):
                score += 25.0
            else:
                reasons.append("Address contains text not supported by OCR evidence")
        else:
            # Address optional for non-address ID cards like simple PAN, but score reduced if missing
            pass

        # 5. PIN Validation (+15)
        if pincode and pincode.upper() != "NOT FOUND":
            if re.match(r'^[1-9][0-9]{5}$', pincode):
                score += 15.0
            else:
                reasons.append(f"Invalid Indian PIN code: '{pincode}'")

        # 6. Overall Evidence Match Bonus (+10)
        evidence_passes = 0
        evidence_checks = 0
        for val in [name, father_name, pan, pincode]:
            if val and val.upper() != "NOT FOUND":
                evidence_checks += 1
                if self.check_ocr_evidence(val, raw_ocr_text):
                    evidence_passes += 1

        if evidence_checks > 0 and (evidence_passes / evidence_checks) >= 0.75:
            score += 10.0

        final_score = round(min(100.0, score), 1)
        is_passed = final_score >= CONFIDENCE_THRESHOLD and len(reasons) == 0

        return is_passed, final_score, reasons, sanitized

validation_service = DocumentValidationService()
