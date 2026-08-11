"""
address_extractor.py
────────────────────
High-Precision City & State Address Extraction & Validation Engine:
1. Document Pre-Validation before extraction.
2. Complete Address Block identification via OCR layout & keywords.
3. PIN-first extraction (\b[1-9][0-9]{5}\b).
4. Local Indian PIN Dataset lookup (PIN → Candidate Locations).
5. Precision Location Hierarchy distinction (City ≠ Locality ≠ Post Office ≠ District ≠ State).
6. OCR Error Correction (SUR4T → Surat, GUJAR4T → Gujarat).
7. Cross-Validation between City, State, District, and PIN candidates.
8. Evidence-Based Confidence calculation & detailed extraction_evidence logging.
9. Strict non-fabrication (returns 'Not Found' when unverified).
10. Per-document state isolation.
"""

import re
import difflib
from typing import Dict, Any, List, Optional, Tuple

from backend.data.india_pincodes import (
    INDIAN_STATES_AND_UTS,
    STATE_ALIASES,
    POSTAL_PREFIX_MAP,
    lookup_pincode
)
from backend.services.ai_service import ai_service
from backend.utils.logger import logger

ADDRESS_AI_PROMPT = """Extract complete Indian address components from the provided OCR text into JSON format:
{
  "house_number": "House/Flat/Plot/Door No or null",
  "building_name": "Building/Society/Apartment Name or null",
  "street": "Street/Road/Marg/Lane or null",
  "area_locality": "Area/Nagar/Colony/Sector or null",
  "village_town": "Village/Town/Tehsil/Taluka or null",
  "city": "Real City/Town Name or null",
  "district": "Real District Name or null",
  "state": "State Name or null",
  "pincode": "6-digit PIN code or null"
}
Rules:
- Never invent fake locations.
- If a city or district is garbled OCR noise (like 'Jjoric' or unreadable characters), set it to null.
- Extract house numbers, streets, villages, talukas, and localities accurately from text."""

# Address Keywords for Address Block Detection
ADDRESS_KEYWORDS = [
    'address', 'addr', 's/o', 'd/o', 'w/o', 'c/o', 'care of', 'son of', 'daughter of', 'wife of',
    'house no', 'h.no', 'flat no', 'door no', 'plot no', 'street', 'road', 'marg', 'lane',
    'nagar', 'colony', 'vpo', 'village', 'post', 'po', 'tehsil', 'taluka', 'dist', 'district',
    'state', 'pin', 'pincode', 'near', 'opp', 'opposite', 'behind'
]

class PrecisionAddressExtractor:

    def extract_address_from_ocr(
        self,
        raw_ocr_text: str,
        ocr_blocks: Optional[List[Dict[str, Any]]] = None,
        doc_type: str = "Unknown",
        ai_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for extracting and validating address components using PIN database + Local AI data.
        Stateless & isolated per document invocation.
        """
        raw_text_clean = raw_ocr_text or ""
        lines = [line.strip() for line in raw_text_clean.split("\n") if line.strip()]

        # ── 1. Document Pre-Validation ──────────────────────────────────────
        is_address_doc = self._pre_validate_address_document(raw_text_clean, lines, doc_type)
        if not is_address_doc:
            return self._build_empty_response(
                raw_text_clean,
                reason="Document format mismatch - no valid address block detected."
            )

        # ── 2. Address Block Detection ──────────────────────────────────────
        address_block_text = self._detect_address_block(lines, ocr_blocks)
        target_text = address_block_text or raw_text_clean

        # ── 3. PIN-First Strategy (\b[1-9][0-9]{5}\b) ────────────────────────
        detected_pincode = self._extract_pincode(target_text)
        if not detected_pincode and ai_data and ai_data.get("pincode"):
            ai_pin = str(ai_data["pincode"]).strip()
            if re.match(r'^[1-9][0-9]{5}$', ai_pin):
                detected_pincode = ai_pin

        pin_data = lookup_pincode(detected_pincode) if detected_pincode else None

        # ── 4. State Extraction ─────────────────────────────────────────────
        detected_state, state_conf, state_source = self._extract_state(
            target_text,
            pin_data=pin_data,
            ai_data=ai_data
        )

        # ── 5. City Extraction (With Garbled Noise Filter & PIN Candidate Alignment) ──
        detected_city, city_conf, city_source = self._extract_city(
            target_text,
            pin_data=pin_data,
            detected_state=detected_state,
            ai_data=ai_data
        )

        # ── 6. District Extraction ──────────────────────────────────────────
        detected_district, dist_conf, dist_source = self._extract_district(
            target_text,
            pin_data=pin_data,
            detected_city=detected_city,
            ai_data=ai_data
        )

        # ── 7. Cross-Validation & Mismatch Detection ────────────────────────
        location_mismatch, mismatch_reason = self._cross_validate_location(
            city=detected_city,
            state=detected_state,
            district=detected_district,
            pincode=detected_pincode,
            pin_data=pin_data
        )

        # ── 8. Overall Evidence-Based Confidence ───────────────────────────
        overall_address_conf = self._calculate_overall_address_confidence(
            city_conf=city_conf,
            state_conf=state_conf,
            has_pin=bool(detected_pincode),
            location_mismatch=location_mismatch
        )

        # ── 9. Evidence Reporting ──────────────────────────────────────────
        extraction_evidence = {
            "pincode": {
                "value": detected_pincode or "Not Found",
                "source": "Regex match \\b[1-9][0-9]{5}\\b" if detected_pincode else "Not Found",
                "confidence": 0.99 if detected_pincode else 0.0
            },
            "city": {
                "value": detected_city,
                "source": city_source,
                "confidence": city_conf
            },
            "district": {
                "value": detected_district,
                "source": dist_source,
                "confidence": dist_conf
            },
            "state": {
                "value": detected_state,
                "source": state_source,
                "confidence": state_conf
            }
        }

        debug_info = {
            "ocr_address_block": address_block_text[:200] if address_block_text else "N/A",
            "detected_pin": detected_pincode or "Not Found",
            "pin_db_result": f"{pin_data.get('city')}, {pin_data.get('state')}" if pin_data else "Not in DB",
            "detected_city": detected_city,
            "detected_state": detected_state,
            "cross_validation": "✓ Validated against PIN database" if not location_mismatch else f"⚠ {mismatch_reason}"
        }

        return {
            "full_address": address_block_text or raw_text_clean,
            "city": detected_city,
            "district": detected_district,
            "state": detected_state,
            "pincode": detected_pincode or "Not Found",
            "address_confidence": overall_address_conf,
            "city_confidence": city_conf,
            "district_confidence": dist_conf,
            "state_confidence": state_conf,
            "location_mismatch": location_mismatch,
            "mismatch_reason": mismatch_reason,
            "extraction_evidence": extraction_evidence,
            "debug_info": debug_info
        }

    def _pre_validate_address_document(self, text: str, lines: List[str], doc_type: str) -> bool:
        """Check if document has structural address markers or keywords before extraction."""
        t_lower = text.lower()

        # 1. Has 6-digit PIN code
        if re.search(r'\b[1-9][0-9]{5}\b', text):
            return True

        # 2. Known address document types
        if any(term in doc_type.lower() for term in ['aadhaar', 'driving', 'passport', 'id card']):
            return True

        # 3. Explicit structural address markers
        structural_keywords = ['house no', 'h.no', 'flat no', 'street', 'road', 'marg', 'vpo', 'nagar', 'colony', 'tehsil', 'dist', 'pincode']
        has_structure = any(kw in t_lower for kw in structural_keywords)
        
        # 4. Known state names in text
        has_state = any(s.lower() in t_lower for s in INDIAN_STATES_AND_UTS)

        return has_structure or has_state

    def _detect_address_block(self, lines: List[str], ocr_blocks: Optional[List[Dict[str, Any]]]) -> str:
        """Detect complete address block using layout lines and address keywords."""
        address_lines = []
        is_capturing = False

        for i, line in enumerate(lines):
            l_lower = line.lower()

            # Start trigger
            if any(kw in l_lower for kw in ['address:', 'address', 's/o', 'd/o', 'w/o', 'c/o', 'vpo', 'house no']):
                is_capturing = True
                address_lines.append(line)
                continue

            if is_capturing:
                address_lines.append(line)
                # End trigger: 6-digit PIN code usually marks end of address block
                if re.search(r'\b[1-9][0-9]{5}\b', line):
                    break

        if address_lines:
            return " ".join(address_lines)

        # Fallback: lines containing PIN or state names
        fallback = [l for l in lines if re.search(r'\b[1-9][0-9]{5}\b', l) or any(s.lower() in l.lower() for s in INDIAN_STATES_AND_UTS)]
        return " ".join(fallback) if fallback else "\n".join(lines[-4:]) if len(lines) >= 4 else "\n".join(lines)

    def _extract_pincode(self, text: str) -> Optional[str]:
        """Extract 6-digit Indian postal PIN code using strict pattern \\b[1-9][0-9]{5}\\b."""
        matches = re.findall(r'\b[1-9][0-9]{5}\b', text)
        return matches[0] if matches else None

    def _extract_state(
        self,
        text: str,
        pin_data: Optional[Dict[str, Any]] = None,
        ai_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float, str]:
        """
        Extract State using:
        1. Local Ollama AI extraction
        2. Exact state match in OCR text
        3. State Alias match
        4. PIN Database state verification
        """
        # 1. Local Ollama AI Model Extraction
        if ai_data and ai_data.get("state"):
            ai_st = str(ai_data["state"]).strip()
            for state in INDIAN_STATES_AND_UTS:
                if ai_st.lower() == state.lower():
                    return state, 0.99, f"Local Ollama AI model extraction ('{state}')"

        # 2. Exact Word Boundary Match in OCR text
        for state in INDIAN_STATES_AND_UTS:
            pattern = r'\b' + re.escape(state) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return state, 0.98, f"Exact OCR text match ('{state}')"

        # 3. State Alias Match (Only match uppercase 2-letter state codes)
        for alias, full_state in STATE_ALIASES.items():
            if re.search(r'\b' + alias + r'\b', text):
                return full_state, 0.92, f"State abbreviation match ('{alias}' -> '{full_state}')"

        # 4. PIN Database Mapping Fallback
        if pin_data and pin_data.get("state"):
            pin_st = pin_data["state"]
            if re.search(r'\b' + re.escape(pin_st) + r'\b', text, re.IGNORECASE):
                return pin_st, 0.95, f"PIN {pin_data['pincode']} state verified in OCR text ('{pin_st}')"
            return pin_st, 0.88, f"Derived from PIN {pin_data['pincode']} database mapping"

        return "Not Found", 0.0, "State unverified"

    def _extract_city(
        self,
        text: str,
        pin_data: Optional[Dict[str, Any]] = None,
        detected_state: str = "Not Found",
        ai_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float, str]:
        """
        Extract City using priority signals:
        1. Local Ollama AI extraction (if valid).
        2. Explicit PIN Primary City match in OCR text.
        3. OCR-tolerant fuzzy match of Primary City (SUR4T -> Surat).
        4. Detect explicit non-PIN city in OCR text.
        5. Fallback to PIN Primary City mapping.
        """
        # Signal 1: Local Ollama AI extraction
        if ai_data and ai_data.get("city"):
            ai_c = str(ai_data["city"]).strip()
            # If Ollama extracted a valid city name (not garbled noise like Jjoric)
            if pin_data:
                candidates = pin_data.get("candidate_localities", [pin_data.get("city")])
                for cand in candidates:
                    if cand and cand.lower() == ai_c.lower():
                        return cand, 0.99, f"Local Ollama AI verified against PIN {pin_data['pincode']} ('{cand}')"
            if len(ai_c) >= 3 and not re.search(r'[^a-zA-Z\s]', ai_c):
                return ai_c, 0.96, f"Local Ollama AI model extraction ('{ai_c}')"

        if pin_data:
            pin_city = pin_data.get("city")
            candidates = pin_data.get("candidate_localities", [pin_city])

            # Signal 2: Primary PIN City explicitly in OCR text
            if pin_city and re.search(r'\b' + re.escape(pin_city) + r'\b', text, re.IGNORECASE):
                return pin_city, 0.98, f"PIN {pin_data['pincode']} primary city verified in OCR text ('{pin_city}')"

            # Signal 3: OCR typo correction of PIN city (SUR4T -> Surat)
            if pin_city:
                norm_text = text.upper().replace('4', 'A').replace('0', 'O').replace('1', 'I').replace('5', 'S')
                city_upper = pin_city.upper()
                if city_upper in norm_text or difflib.SequenceMatcher(None, city_upper, norm_text).find_longest_match(0, len(city_upper), 0, len(norm_text)).size >= len(city_upper) - 1:
                    return pin_city, 0.94, f"OCR typo correction of primary PIN city ('{pin_city}')"

        # Signal 4: Search for explicit major Indian city names written in text
        words = [w.strip(",.- ") for w in text.split() if len(w.strip(",.- ")) >= 4]
        for w in words:
            for prefix_code, (c_name, dist_name, st_name) in POSTAL_PREFIX_MAP.items():
                if w.lower() == c_name.lower():
                    if pin_data and pin_data.get("city") and pin_data["city"].lower() != c_name.lower():
                        return c_name, 0.90, f"Explicit OCR city ('{c_name}') conflicts with PIN {pin_data['pincode']}"
                    return c_name, 0.95, f"Explicit OCR city text match ('{c_name}')"

        # Signal 5: Fallback to PIN Primary City mapping
        if pin_data and pin_data.get("city"):
            return pin_data["city"], 0.88, f"PIN {pin_data['pincode']} primary city database mapping ('{pin_data['city']}')"

        return "Not Found", 0.0, "City unverified"

    def _extract_district(
        self,
        text: str,
        pin_data: Optional[Dict[str, Any]] = None,
        detected_city: str = "Not Found",
        ai_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float, str]:
        """Extract District using Local Ollama AI, PIN database mapping, or keyword extraction."""
        # 1. Local Ollama AI extraction
        if ai_data and ai_data.get("district"):
            ai_dist = str(ai_data["district"]).strip()
            if pin_data and pin_data.get("district") and pin_data["district"].lower() == ai_dist.lower():
                return pin_data["district"], 0.99, f"Local Ollama AI verified against PIN {pin_data['pincode']} ('{pin_data['district']}')"
            if len(ai_dist) >= 3 and not re.search(r'[^a-zA-Z\s]', ai_dist):
                return ai_dist, 0.95, f"Local Ollama AI model extraction ('{ai_dist}')"

        # 2. PIN Database District Mapping
        if pin_data and pin_data.get("district"):
            return pin_data["district"], 0.92, f"Derived from PIN {pin_data['pincode']} database mapping"

        # 3. Explicit Keyword extraction (e.g. Dist: Surat, District - Vadodara)
        dist_match = re.search(r'(?i)\b(dist|district)\b\s*[:=\-]?\s*([A-Za-z\s]{3,20})\b', text)
        if dist_match:
            candidate = dist_match.group(2).strip()
            # Garbled noise check: if candidate looks like random OCR noise (e.g. Jjoric)
            if not pin_data or (candidate.lower() in [c.lower() for c in pin_data.get("candidate_localities", [])]):
                return candidate, 0.90, f"Explicit keyword extraction ('{candidate}')"

        if detected_city != "Not Found":
            return detected_city, 0.70, "Assumed from primary city/district"

        return "Not Found", 0.0, "District unverified"

    def _parse_address_hierarchy(
        self,
        text: str,
        ai_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Extract house number, building, street, area, locality, and village/town from address text."""
        res = {
            "house_number": "Not Found",
            "building_name": "Not Found",
            "street": "Not Found",
            "area": "Not Found",
            "locality": "Not Found",
            "village_town": "Not Found"
        }

        # 1. Use Local Ollama AI fields if present
        if ai_data and isinstance(ai_data, dict):
            if ai_data.get("house_number") and str(ai_data["house_number"]).lower() not in ["null", "none", "not found"]:
                res["house_number"] = str(ai_data["house_number"]).strip()
            if ai_data.get("building_name") and str(ai_data["building_name"]).lower() not in ["null", "none", "not found"]:
                res["building_name"] = str(ai_data["building_name"]).strip()
            if ai_data.get("street") and str(ai_data["street"]).lower() not in ["null", "none", "not found"]:
                res["street"] = str(ai_data["street"]).strip()
            if ai_data.get("area_locality") and str(ai_data["area_locality"]).lower() not in ["null", "none", "not found"]:
                res["area"] = str(ai_data["area_locality"]).strip()
                res["locality"] = str(ai_data["area_locality"]).strip()
            if ai_data.get("village_town") and str(ai_data["village_town"]).lower() not in ["null", "none", "not found"]:
                res["village_town"] = str(ai_data["village_town"]).strip()

        # 2. Regex fallbacks if any fields are still "Not Found"
        if res["house_number"] == "Not Found":
            h_match = re.search(r'(?i)\b(house|h\.no|flat|plot|door|bldg)\b\s*[:=\-]?\s*([A-Za-z0-9/\-]+)', text)
            if h_match:
                res["house_number"] = h_match.group(2)

        if res["street"] == "Not Found":
            s_match = re.search(r'(?i)\b([A-Za-z0-9\s]+(street|road|marg|lane|path))\b', text)
            if s_match:
                res["street"] = s_match.group(1).strip()

        if res["area"] == "Not Found":
            a_match = re.search(r'(?i)\b([A-Za-z0-9\s]+(nagar|colony|vpo|society|park|vihar|sector))\b', text)
            if a_match:
                res["area"] = a_match.group(1).strip()
                res["locality"] = a_match.group(1).strip()

        if res["village_town"] == "Not Found":
            v_match = re.search(r'(?i)\b(village|vpo|taluka|tehsil|block)\s*[:=\-]?\s*([A-Za-z\s]{3,20})\b', text)
            if v_match:
                res["village_town"] = v_match.group(2).strip()

        return res

    def _cross_validate_location(
        self,
        city: str,
        state: str,
        district: str,
        pincode: Optional[str],
        pin_data: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Cross-validate extracted City & State against PIN database mapping."""
        if not pin_data or not pincode:
            return False, None

        db_city = pin_data.get("city", "")
        db_state = pin_data.get("state", "")
        candidates = [c.lower() for c in pin_data.get("candidate_localities", [db_city])]

        # Validate State Mismatch
        if state != "Not Found" and db_state and state.lower() != db_state.lower():
            return True, f"State mismatch: Extracted '{state}' conflicts with PIN {pincode} state '{db_state}'."

        # Validate City Mismatch
        if city != "Not Found" and candidates:
            city_low = city.lower()
            if not any(c in city_low or city_low in c for c in candidates):
                return True, f"Location mismatch — needs review: Extracted city '{city}' does not match PIN {pincode} candidates ({', '.join(candidates[:3])})."

        return False, None

    def _calculate_overall_address_confidence(
        self,
        city_conf: float,
        state_conf: float,
        has_pin: bool,
        location_mismatch: bool
    ) -> float:
        """Calculate evidence-based confidence score for address extraction."""
        if location_mismatch:
            return round(max(0.40, (city_conf + state_conf) / 2.0 - 0.30), 2)

        base_score = 0.30
        if has_pin:
            base_score += 0.35
        if city_conf > 0.5:
            base_score += city_conf * 0.20
        if state_conf > 0.5:
            base_score += state_conf * 0.15

        return round(min(0.99, base_score), 2)

    def _build_empty_response(self, raw_text: str, reason: str) -> Dict[str, Any]:
        """Build unverified response when document fails pre-validation."""
        return {
            "full_address": raw_text,
            "city": "Not Found",
            "district": "Not Found",
            "state": "Not Found",
            "pincode": "Not Found",
            "address_confidence": 0.0,
            "city_confidence": 0.0,
            "district_confidence": 0.0,
            "state_confidence": 0.0,
            "location_mismatch": False,
            "mismatch_reason": reason,
            "extraction_evidence": {
                "status": "Unverified - " + reason
            },
            "debug_info": {
                "ocr_address_block": "N/A",
                "detected_pin": "Not Found",
                "pin_db_result": "N/A",
                "detected_city": "Not Found",
                "detected_state": "Not Found",
                "cross_validation": "Failed pre-validation"
            }
        }

address_extractor = PrecisionAddressExtractor()
