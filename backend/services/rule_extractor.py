"""
rule_extractor.py
──────────────────
Deterministic, rule-based field extraction engine using precise regex patterns and layout heuristics.
Executes when all AI models fail or when fast pattern matching is sufficient.
"""

import re
from typing import Dict, Any, List, Optional
from backend.services.address_extractor import address_extractor
from backend.utils.validators import validate_pan_number, validate_verhoeff

class RuleBasedExtractor:

    def extract(self, raw_ocr_text: str, doc_type: str = "General Document") -> Dict[str, Any]:
        """
        Executes deterministic pattern-matching extraction.
        Returns standardized dictionary output.
        """
        lines = [line.strip() for line in raw_ocr_text.splitlines() if line.strip()]
        full_text = " ".join(lines)
        upper_text = full_text.upper()

        extracted: Dict[str, Any] = {
            "document_type": doc_type,
            "name": "",
            "father_name": "",
            "dob": "",
            "pan_number": "",
            "address": "",
            "pincode": "",
            "city": "",
            "state": "",
            "confidence": 75.0,
            "model_used": "Rule-Based Engine",
            "status": "rule_fallback"
        }

        # 1. PAN Number Regex
        pan_match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', upper_text)
        if pan_match:
            pan_val = validate_pan_number(pan_match.group(0))
            if pan_val["is_valid"]:
                extracted["pan_number"] = pan_val["pan_number"]

        # 2. Date of Birth (DOB) Regex
        dob_match = re.search(r'\b(0[1-9]|[12]\d|3[01])[/.-](0[1-9]|1[0-2])[/.-](?:19|20)\d\d\b', full_text)
        if dob_match:
            extracted["dob"] = dob_match.group(0)

        # 3. PIN Code Regex
        pin_match = re.search(r'\b[1-9][0-9]{5}\b', full_text)
        if pin_match:
            extracted["pincode"] = pin_match.group(0)

        # 4. Father's Name Heuristic
        father_name = ""
        father_inline = re.search(r"(?:Father'?s?\s*Name|पिता\s*का\s*नाम)[:\s]+([A-Z\s]{3,})", full_text, re.IGNORECASE)
        if father_inline:
            father_name = father_inline.group(1).strip()
        else:
            for i, line in enumerate(lines):
                u = line.upper()
                if any(kw in u for kw in ["FATHER", "PITA", "पिता"]):
                    for offset in range(1, 3):
                        if i + offset < len(lines):
                            cand = lines[i + offset].strip()
                            if len(cand) > 2 and not re.search(r'\d', cand) and not any(kw in cand.upper() for kw in ["DATE", "BIRTH", "INCOME", "TAX", "GOVT", "SIGNATURE", "FATHER", "NAME", "PITA", "पिता"]):
                                father_name = cand
                                break
                    if father_name:
                        break
        extracted["father_name"] = father_name

        # 5. Primary Cardholder / Person Name Heuristic
        name = ""
        clean_lines = [
            l for l in lines
            if len(l) > 2
            and not re.search(r'\d', l)
            and not any(kw in l.upper() for kw in ["INCOME", "TAX", "DEPARTMENT", "GOVT", "INDIA", "PERMANENT", "ACCOUNT", "NUMBER", "CARD", "SIGNATURE", "FATHER", "PITA", "पिता", "NAME", "नाम", "DATE", "BIRTH"])
        ]
        if clean_lines:
            name = clean_lines[0]
        extracted["name"] = name

        # 6. Precision Address Extraction via PIN & Layout Anchor
        address_res = address_extractor.extract_address_from_ocr(raw_ocr_text, doc_type=doc_type)
        if address_res.get("city") != "Not Found":
            extracted["city"] = address_res["city"]
        if address_res.get("state") != "Not Found":
            extracted["state"] = address_res["state"]
        if address_res.get("pincode") != "Not Found":
            extracted["pincode"] = address_res["pincode"]
        if address_res.get("full_address") != "Not Found":
            extracted["address"] = address_res["full_address"]

        return extracted

rule_extractor = RuleBasedExtractor()
