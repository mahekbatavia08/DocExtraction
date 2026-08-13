"""
medical_ner.py
──────────────
Standalone Medical Named Entity Recognition (NER) & Classification Layer.

Identifies and classifies extracted prescription entities into standard categories:
  - DOCTOR (e.g. "Dr. Sarah Jenkins", "MBBS, MD")
  - PATIENT (e.g. "John Smith", "Age: 45")
  - MEDICINE (e.g. "Paracetamol", "Amoxicillin", "Metformin")
  - STRENGTH (e.g. "500 mg", "10 ml", "0.5 %")
  - DOSAGE (e.g. "1 tablet", "2 puffs", "5 ml")
  - FREQUENCY (e.g. "1-0-1", "TID", "BD", "OD", "QID", "Once daily")
  - DURATION (e.g. "5 days", "1 month", "7 days")
  - ROUTE (e.g. "oral", "topical", "IV", "sublingual")
  - DIAGNOSIS (e.g. "Hypertension", "Type 2 Diabetes", "Acute Bronchitis")
  - TEST (e.g. "CBC", "Lipid Profile", "HbA1c", "Chest X-Ray")
  - INSTRUCTION (e.g. "After meals", "Before bed", "With warm water")
  - DATE (e.g. "13/08/2026", "2026-08-13")

Applies zero-hallucination rules: preserves uncertain/unreadable handwriting markers.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


class MedicalNERService:
    """
    Independent Medical Named Entity Recognition classifier & normalizer.
    """

    # Common frequency patterns
    FREQ_PATTERNS = [
        (r'\b(1-0-1|1\+0\+1)\b', "1-0-1 (Twice daily, morning & night)"),
        (r'\b(1-1-1|1\+1\+1)\b', "1-1-1 (Three times daily)"),
        (r'\b(1-0-0|1\+0\+0)\b', "1-0-0 (Once daily, morning)"),
        (r'\b(0-0-1|0\+0\+1)\b', "0-0-1 (Once daily, night)"),
        (r'\b(0-1-0|0\+1\+0)\b', "0-1-0 (Once daily, afternoon)"),
        (r'\b(tid|t\.i\.d\.)\b', "TID (3 times daily)"),
        (r'\b(bid|b\.i\.d\.|bd)\b', "BD (Twice daily)"),
        (r'\b(qid|q\.i\.d\.)\b', "QID (4 times daily)"),
        (r'\b(od|o\.d\.)\b', "OD (Once daily)"),
        (r'\b(hs|h\.s\.)\b', "HS (At bedtime)"),
        (r'\b(prn|p\.r\.n\.)\b', "PRN (As needed)")
    ]

    # Strength patterns
    STRENGTH_PATTERN = r'\b\d+(\.\d+)?\s*(mg|g|mcg|ml|iu|mEq|%)\b'

    # Duration patterns
    DURATION_PATTERN = r'\b\d+\s*(day|days|week|weeks|month|months|wk|wks)\b'

    def classify_token(self, token: str) -> str:
        """Classify a single token or string into medical entity category."""
        t_lower = token.strip().lower()
        if not t_lower:
            return "UNKNOWN"

        # Check Date
        if re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', token) or re.search(r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', token):
            return "DATE"

        # Check Frequency
        for pat, _ in self.FREQ_PATTERNS:
            if re.search(pat, t_lower):
                return "FREQUENCY"

        # Check Strength
        if re.search(self.STRENGTH_PATTERN, t_lower):
            return "STRENGTH"

        # Check Duration
        if re.search(self.DURATION_PATTERN, t_lower):
            return "DURATION"

        # Check Route
        if t_lower in ["oral", "po", "topical", "iv", "im", "sublingual", "inhaled", "ophthalmic", "otic"]:
            return "ROUTE"

        # Check Doctor prefixes
        if any(prefix in t_lower for prefix in ["dr.", "dr ", "doctor", "mbbs", "md", "ms", "bmdc"]):
            return "DOCTOR"

        # Check Patient prefixes
        if any(prefix in t_lower for prefix in ["patient", "pt.", "age:", "yrs", "years", "male", "female"]):
            return "PATIENT"

        # Check Instruction keywords
        if any(kw in t_lower for kw in ["after meal", "before meal", "empty stomach", "before bed", "with water", "after food"]):
            return "INSTRUCTION"

        # Check Test keywords
        if any(kw in t_lower for kw in ["cbc", "hba1c", "x-ray", "ecg", "ultrasound", "lipid profile", "creatinine", "mri"]):
            return "TEST"

        return "MEDICINE"

    def normalize_medicine_entry(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw medicine dictionary and applies Medical NER normalization & confidence grading.
        Ensures zero hallucination: preserves partial handwriting markers ('Amoxi...').
        """
        raw_name = raw_entry.get("name")
        raw_strength = raw_entry.get("strength")
        raw_dosage = raw_entry.get("dosage")
        raw_freq = raw_entry.get("frequency")
        raw_duration = raw_entry.get("duration")
        raw_route = raw_entry.get("route")
        raw_instructions = raw_entry.get("instructions")
        conf = float(raw_entry.get("confidence", 0.0))
        needs_rev = raw_entry.get("needs_review", False)

        # 1. Unclear/Partial Handwriting Check
        if raw_name:
            clean_name = str(raw_name).strip()
            if "..." in clean_name or clean_name.endswith("?") or len(clean_name) < 3:
                conf = min(conf, 0.45)
                needs_rev = True

        # 2. Normalize Frequency if raw_freq present
        norm_freq = raw_freq
        if raw_freq:
            for pat, std_label in self.FREQ_PATTERNS:
                if re.search(pat, str(raw_freq).lower()):
                    norm_freq = raw_freq  # Preserve exact text, store normalized
                    break

        # 3. Route Inference Safeguard: Do not default to oral unless supported
        norm_route = raw_route
        if norm_route and str(norm_route).lower() == "oral" and not raw_dosage and not raw_freq:
            # Drop unsubstantiated oral route
            norm_route = None

        return {
            "name": raw_name,
            "strength": raw_strength,
            "dosage": raw_dosage,
            "frequency": norm_freq,
            "duration": raw_duration,
            "route": norm_route,
            "instructions": raw_instructions,
            "confidence": round(conf, 2),
            "needs_review": needs_rev or conf < 0.65
        }

    def process_entities(self, medicines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize entire medicine list through Medical NER pipeline."""
        normalized_list = []
        for med in medicines:
            normalized_list.append(self.normalize_medicine_entry(med))
        return normalized_list

    def extract_entities_from_text(self, raw_text: str) -> Dict[str, Any]:
        """
        Scan raw merged OCR text and return a structured dict of all recognized
        medical entities, grouped by category.

        Returns:
            {
              "DOCTOR":      [str, ...],
              "PATIENT":     [str, ...],
              "MEDICINE":    [str, ...],
              "STRENGTH":    [str, ...],
              "DOSAGE":      [str, ...],
              "FREQUENCY":   [str, ...],
              "DURATION":    [str, ...],
              "ROUTE":       [str, ...],
              "DIAGNOSIS":   [str, ...],
              "TEST":        [str, ...],
              "INSTRUCTION": [str, ...],
              "DATE":        [str, ...],
            }
        """
        entities: Dict[str, List[str]] = {
            "DOCTOR": [], "PATIENT": [], "MEDICINE": [], "STRENGTH": [],
            "DOSAGE": [], "FREQUENCY": [], "DURATION": [], "ROUTE": [],
            "DIAGNOSIS": [], "TEST": [], "INSTRUCTION": [], "DATE": []
        }

        if not raw_text or not raw_text.strip():
            return entities

        # ── 1. Extract dates with regex (most reliable) ──────────────────────
        date_hits = re.findall(
            r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b|\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b',
            raw_text
        )
        entities["DATE"] = list(dict.fromkeys(date_hits))

        # ── 2. Extract strengths (e.g. 500mg, 10ml, 0.5%) ───────────────────
        strength_hits = re.findall(self.STRENGTH_PATTERN, raw_text, re.IGNORECASE)
        # strength_hits are (integer_part, decimal_part) tuples from the group
        raw_strength_tokens = re.findall(
            r'\b\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|iu|mEq|%)\b', raw_text, re.IGNORECASE
        )
        entities["STRENGTH"] = list(dict.fromkeys(raw_strength_tokens))

        # ── 3. Extract durations (e.g. 5 days, 2 weeks) ─────────────────────
        duration_hits = re.findall(self.DURATION_PATTERN, raw_text, re.IGNORECASE)
        raw_duration_tokens = re.findall(
            r'\b\d+\s*(?:day|days|week|weeks|month|months|wk|wks)\b', raw_text, re.IGNORECASE
        )
        entities["DURATION"] = list(dict.fromkeys(raw_duration_tokens))

        # ── 4. Extract frequencies from common patterns ──────────────────────
        for pat, label in self.FREQ_PATTERNS:
            if re.search(pat, raw_text, re.IGNORECASE):
                entities["FREQUENCY"].append(label)
        # Numeric patterns like 1-0-1 or 1+1+1
        numeric_freq = re.findall(r'\b[01][-+][01][-+][01]\b', raw_text)
        for nf in numeric_freq:
            if nf not in entities["FREQUENCY"]:
                entities["FREQUENCY"].append(nf)

        # ── 5. Extract routes ────────────────────────────────────────────────
        route_keywords = {
            "oral": "oral", "po": "oral", "p.o.": "oral",
            "iv": "intravenous", "i.v.": "intravenous",
            "im": "intramuscular", "i.m.": "intramuscular",
            "sc": "subcutaneous", "s.c.": "subcutaneous",
            "sl": "sublingual", "sublingual": "sublingual",
            "topical": "topical", "top": "topical",
            "inhaled": "inhaled", "inh": "inhaled",
            "ophthalmic": "ophthalmic", "otic": "otic",
        }
        text_lower = raw_text.lower()
        for kw, label in route_keywords.items():
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                if label not in entities["ROUTE"]:
                    entities["ROUTE"].append(label)

        # ── 6. Classify each line for DOCTOR / PATIENT / MEDICINE etc. ───────
        INSTRUCTION_PHRASES = [
            "after meal", "before meal", "empty stomach", "before bed",
            "with water", "after food", "with milk", "on empty stomach",
            "at bedtime", "before sleep", "after breakfast", "after dinner"
        ]
        TEST_KEYWORDS = [
            "cbc", "hba1c", "x-ray", "ecg", "eeg", "mri", "ultrasound",
            "lipid profile", "creatinine", "urine", "culture", "sensitivity",
            "ct scan", "thyroid", "tsh", "ldl", "hdl", "blood sugar", "rbs",
            "fbs", "ppbs", "chest x"
        ]

        for line in raw_text.splitlines():
            line_stripped = line.strip()
            if not line_stripped or len(line_stripped) < 2:
                continue
            line_lower = line_stripped.lower()

            # Doctor detection
            if any(p in line_lower for p in ["dr.", "dr ", "doctor", "mbbs", " md", "bmdc", "reg no", "clinic"]):
                entities["DOCTOR"].append(line_stripped)
                continue

            # Patient detection
            if any(p in line_lower for p in ["patient:", "pt.", "name:", "age:", "sex:", "weight:", "wt:", "male", "female"]):
                entities["PATIENT"].append(line_stripped)
                continue

            # Instruction detection
            if any(phrase in line_lower for phrase in INSTRUCTION_PHRASES):
                entities["INSTRUCTION"].append(line_stripped)
                continue

            # Test detection
            if any(kw in line_lower for kw in TEST_KEYWORDS):
                entities["TEST"].append(line_stripped)
                continue

            # Diagnosis detection (Dx:, Diagnosis:, C/C:, Chief Complaint)
            if re.search(r'\b(dx|diagnosis|chief complaint|c/c|impression|assessment)[:\s]', line_lower):
                diag_match = re.search(r'(?:dx|diagnosis|chief complaint|c/c|impression|assessment)[:\s]+(.+)', line_lower)
                if diag_match:
                    entities["DIAGNOSIS"].append(diag_match.group(1).strip().title())
                continue

            # Medicine detection: lines starting with Tab/Cap/Syp/Inj/Cr/Drop/Oint
            if re.search(r'^(tab\.?|cap\.?|syp\.?|syr\.?|inj\.?|cr\.?|oint\.?|drop\.?|gel\.?|lotion\.?|powder\.?)\s+\w', line_lower):
                entities["MEDICINE"].append(line_stripped)
                continue

        # Deduplicate all lists preserving order
        for key in entities:
            seen = set()
            deduped = []
            for item in entities[key]:
                norm = item.strip().lower()
                if norm not in seen:
                    seen.add(norm)
                    deduped.append(item.strip())
            entities[key] = deduped

        return entities


medical_ner = MedicalNERService()
