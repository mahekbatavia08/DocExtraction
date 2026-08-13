"""
medical_abbreviations.py
─────────────────────────
Medical Abbreviation & Dosage Expansion Module.

Decodes standard medical shorthand used by doctors in handwritten prescriptions:
  - Latin dosage frequency abbreviations (bd, tds, od, qid, prn, sos...)
  - Route of administration codes (iv, im, sc, po, sl, pr, inh...)
  - Timing/meal-relation codes (ac, pc, hs, stat...)
  - Dosage pattern normalization (1-0-1 → Twice daily: Morning + Night)
  - Strength unit normalization (200mg/5ml → 200 mg/5 mL)
  - Diagnosis & allergy abbreviations (NKDA, HTN, DM, URTI...)
"""

import re
from typing import Optional


# ── Medical Frequency / Dosage Abbreviations ─────────────────────────────────
FREQUENCY_EXPANSIONS = {
    # Once daily
    "od": "once daily",
    "o.d.": "once daily",
    "qd": "once daily",
    "q.d.": "once daily",
    "qday": "once daily",
    "once daily": "once daily",
    "1/day": "once daily",
    "1x/day": "once daily",

    # Twice daily
    "bd": "twice daily",
    "b.d.": "twice daily",
    "bid": "twice daily",
    "b.i.d.": "twice daily",
    "2/day": "twice daily",
    "2x/day": "twice daily",
    "twice daily": "twice daily",
    "twice a day": "twice daily",

    # Three times daily
    "tds": "three times daily",
    "t.d.s.": "three times daily",
    "tid": "three times daily",
    "t.i.d.": "three times daily",
    "3/day": "three times daily",
    "3x/day": "three times daily",
    "thrice daily": "three times daily",
    "three times daily": "three times daily",

    # Four times daily
    "qid": "four times daily",
    "q.i.d.": "four times daily",
    "4/day": "four times daily",
    "4x/day": "four times daily",
    "four times daily": "four times daily",

    # Every N hours
    "q4h": "every 4 hours",
    "q4hrs": "every 4 hours",
    "q6h": "every 6 hours",
    "q6hrs": "every 6 hours",
    "q8h": "every 8 hours",
    "q8hrs": "every 8 hours",
    "q12h": "every 12 hours",
    "q12hrs": "every 12 hours",

    # As needed / conditional
    "prn": "as needed",
    "p.r.n.": "as needed",
    "sos": "as needed (if required)",
    "s.o.s.": "as needed (if required)",
    "if required": "as needed (if required)",
    "when required": "as needed (if required)",

    # Stat / immediately
    "stat": "immediately (once)",
    "s.t.a.t.": "immediately (once)",
    "immediately": "immediately (once)",

    # Alternate day
    "eod": "every other day",
    "e.o.d.": "every other day",
    "alternate days": "every other day",
    "alt day": "every other day",

    # Weekly
    "qwk": "once weekly",
    "once a week": "once weekly",
    "weekly": "once weekly",

    # Monthly
    "monthly": "once monthly",
    "once a month": "once monthly",
}


# ── Route of Administration Abbreviations ────────────────────────────────────
ROUTE_EXPANSIONS = {
    "po": "oral (by mouth)",
    "p.o.": "oral (by mouth)",
    "oral": "oral (by mouth)",
    "by mouth": "oral (by mouth)",
    "sublingually": "sublingual (under tongue)",
    "sl": "sublingual (under tongue)",
    "s.l.": "sublingual (under tongue)",
    "iv": "intravenous",
    "i.v.": "intravenous",
    "intravenously": "intravenous",
    "im": "intramuscular",
    "i.m.": "intramuscular",
    "intramuscularly": "intramuscular",
    "sc": "subcutaneous",
    "s.c.": "subcutaneous",
    "subcut": "subcutaneous",
    "subcutaneously": "subcutaneous",
    "inh": "inhaled",
    "inhalation": "inhaled",
    "inhaled": "inhaled",
    "top": "topical",
    "topically": "topical",
    "topical": "topical",
    "pr": "rectal",
    "p.r.": "rectal",
    "rectally": "rectal",
    "nasal": "intranasal",
    "intranasal": "intranasal",
    "ophthalmic": "eye drops",
    "eye": "eye drops",
    "otic": "ear drops",
    "ear": "ear drops",
    "transdermal": "transdermal (skin patch)",
    "patch": "transdermal (skin patch)",
    "ng": "nasogastric",
    "nasogastric": "nasogastric",
}


# ── Meal-Relation / Timing Abbreviations ────────────────────────────────────
TIMING_EXPANSIONS = {
    "ac": "before meals",
    "a.c.": "before meals",
    "before meals": "before meals",
    "before food": "before meals",
    "before eating": "before meals",
    "empty stomach": "on empty stomach",
    "pc": "after meals",
    "p.c.": "after meals",
    "after meals": "after meals",
    "after food": "after meals",
    "after eating": "after meals",
    "with food": "with meals",
    "with meals": "with meals",
    "hs": "at bedtime",
    "h.s.": "at bedtime",
    "at bedtime": "at bedtime",
    "bedtime": "at bedtime",
    "night": "at bedtime",
    "am": "in the morning",
    "morning": "in the morning",
    "pm": "in the evening",
    "evening": "in the evening",
}


# ── Diagnosis & Clinical Abbreviations ─────────────────────────────────────
DIAGNOSIS_EXPANSIONS = {
    "nkda": "No Known Drug Allergies",
    "nka": "No Known Allergies",
    "htn": "Hypertension",
    "dm": "Diabetes Mellitus",
    "dm2": "Type 2 Diabetes Mellitus",
    "dm1": "Type 1 Diabetes Mellitus",
    "t2dm": "Type 2 Diabetes Mellitus",
    "t1dm": "Type 1 Diabetes Mellitus",
    "urti": "Upper Respiratory Tract Infection",
    "lrti": "Lower Respiratory Tract Infection",
    "uti": "Urinary Tract Infection",
    "cad": "Coronary Artery Disease",
    "chf": "Congestive Heart Failure",
    "mi": "Myocardial Infarction",
    "cvd": "Cardiovascular Disease",
    "copd": "Chronic Obstructive Pulmonary Disease",
    "gerd": "Gastroesophageal Reflux Disease",
    "ibs": "Irritable Bowel Syndrome",
    "pe": "Pulmonary Embolism",
    "dvt": "Deep Vein Thrombosis",
    "ra": "Rheumatoid Arthritis",
    "oa": "Osteoarthritis",
    "tb": "Tuberculosis",
    "hiv": "HIV",
    "std": "Sexually Transmitted Disease",
    "ckd": "Chronic Kidney Disease",
    "esrd": "End-Stage Renal Disease",
    "nafld": "Non-Alcoholic Fatty Liver Disease",
    "pcos": "Polycystic Ovary Syndrome",
    "asthma": "Asthma",
    "anxiety": "Anxiety Disorder",
    "depression": "Depression",
    "ocd": "Obsessive-Compulsive Disorder",
    "adhd": "Attention Deficit Hyperactivity Disorder",
}


# ── Dosage Pattern Normalization ─────────────────────────────────────────────
DOSAGE_PATTERN_EXPANSIONS = {
    "1-0-1": "Twice daily (Morning + Night)",
    "1+0+1": "Twice daily (Morning + Night)",
    "1-1-1": "Three times daily (Morning + Afternoon + Night)",
    "1+1+1": "Three times daily (Morning + Afternoon + Night)",
    "0-0-1": "Once daily (at Night)",
    "0+0+1": "Once daily (at Night)",
    "1-0-0": "Once daily (Morning)",
    "1+0+0": "Once daily (Morning)",
    "0-1-0": "Once daily (Afternoon)",
    "0+1+0": "Once daily (Afternoon)",
    "1-1-0": "Twice daily (Morning + Afternoon)",
    "1+1+0": "Twice daily (Morning + Afternoon)",
    "0-1-1": "Twice daily (Afternoon + Night)",
    "0+1+1": "Twice daily (Afternoon + Night)",
    "1-0-0-1": "Twice daily (Morning + Night)",
    "1-1-1-1": "Four times daily",
    "2-0-2": "Twice daily (2 tablets — Morning + Night)",
    "2-1-2": "Three times daily (2-1-2 tablets)",
    "2-2-2": "Three times daily (2 tablets each)",
}


class MedicalAbbreviationExpander:
    """
    Expands medical abbreviations found in handwritten prescription extractions.
    Run on extracted `frequency`, `route`, `instructions`, `timing`, and `diagnosis` fields.
    """

    def expand_frequency(self, raw: Optional[str]) -> str:
        """Expand dosage frequency abbreviation to full English."""
        if not raw:
            return raw or ""
        cleaned = raw.strip().lower()

        # Check dosage pattern first (e.g. 1-0-1)
        pattern_key = re.sub(r'\s+', '', raw.strip()).replace('+', '-')
        if pattern_key in DOSAGE_PATTERN_EXPANSIONS:
            return DOSAGE_PATTERN_EXPANSIONS[pattern_key]
        pattern_key_plus = pattern_key.replace('-', '+')
        if pattern_key_plus in DOSAGE_PATTERN_EXPANSIONS:
            return DOSAGE_PATTERN_EXPANSIONS[pattern_key_plus]

        # Word-level expansion
        if cleaned in FREQUENCY_EXPANSIONS:
            return FREQUENCY_EXPANSIONS[cleaned]

        # Token-by-token expansion (handles "bd after food" → "twice daily after food")
        tokens = re.split(r'[\s,/]+', cleaned)
        expanded_tokens = [FREQUENCY_EXPANSIONS.get(t, t) for t in tokens]
        result = " ".join(dict.fromkeys(expanded_tokens))  # Deduplicate adjacent identical tokens
        return result if result != cleaned else raw

    def expand_route(self, raw: Optional[str]) -> str:
        """Expand route of administration abbreviation to full English."""
        if not raw:
            return raw or ""
        cleaned = raw.strip().lower()
        return ROUTE_EXPANSIONS.get(cleaned, raw)

    def expand_timing(self, raw: Optional[str]) -> str:
        """Expand timing/meal-relation abbreviation to full English."""
        if not raw:
            return raw or ""
        cleaned = raw.strip().lower()
        return TIMING_EXPANSIONS.get(cleaned, raw)

    def expand_diagnosis(self, raw: Optional[str]) -> str:
        """Expand diagnosis abbreviations to full medical terms."""
        if not raw:
            return raw or ""
        tokens = re.split(r'[\s,;]+', raw.strip())
        expanded = []
        for token in tokens:
            key = token.strip().lower().rstrip('.')
            expanded.append(DIAGNOSIS_EXPANSIONS.get(key, token))
        return ", ".join(expanded)

    def expand_dosage_pattern(self, raw: Optional[str]) -> str:
        """Normalize and expand dosage patterns like 1-0-1, 1+0+1."""
        if not raw:
            return raw or ""
        key = re.sub(r'\s+', '', raw.strip())
        return DOSAGE_PATTERN_EXPANSIONS.get(key, DOSAGE_PATTERN_EXPANSIONS.get(key.replace('-', '+'), raw))

    def normalize_strength(self, raw: Optional[str]) -> str:
        """Normalize dosage strength strings like 200mg/5ml → 200 mg/5 mL."""
        if not raw:
            return raw or ""
        # Add space between number and unit
        result = re.sub(r'(\d)(mg|mcg|g|ml|mL|IU|units?)', r'\1 \2', raw, flags=re.IGNORECASE)
        # Normalize mL casing
        result = re.sub(r'\bml\b', 'mL', result, flags=re.IGNORECASE)
        # Normalize mcg
        result = re.sub(r'\bmcg\b', 'mcg', result, flags=re.IGNORECASE)
        return result

    def expand_medicine(self, medicine: dict) -> dict:
        """
        Apply all relevant expansions to a single extracted medicine dict.
        Returns the medicine dict with expanded fields.
        """
        expanded = dict(medicine)

        # Expand frequency
        freq_raw = medicine.get("frequency") or medicine.get("dosage") or ""
        if freq_raw:
            expanded["frequency"] = self.expand_frequency(freq_raw)
            expanded["abbreviation_expanded"] = True

        # Expand dosage pattern separately (e.g. 1-0-1)
        dosage_raw = medicine.get("dosage") or ""
        if dosage_raw:
            expanded["dosage"] = self.expand_dosage_pattern(dosage_raw)
            if expanded["dosage"] == dosage_raw:
                expanded["dosage"] = self.expand_frequency(dosage_raw)

        # Expand route
        route_raw = medicine.get("route") or ""
        if route_raw:
            expanded["route"] = self.expand_route(route_raw)

        # Expand instructions/timing
        instr_raw = medicine.get("instructions") or ""
        if instr_raw:
            expanded["instructions"] = self.expand_timing(instr_raw)
            if expanded["instructions"] == instr_raw:
                expanded["instructions"] = self.expand_frequency(instr_raw)

        # Normalize strength
        strength_raw = medicine.get("strength") or ""
        if strength_raw:
            expanded["strength"] = self.normalize_strength(strength_raw)

        return expanded

    def expand_medicines_list(self, medicines: list) -> list:
        """Apply full expansion to a list of extracted medicine dicts."""
        return [self.expand_medicine(m) for m in medicines]

    def expand_diagnoses_list(self, diagnoses: list) -> list:
        """Expand a list of diagnosis strings."""
        return [self.expand_diagnosis(d) for d in diagnoses]

    def expand_allergies(self, raw: Optional[str]) -> str:
        """Expand allergy field (e.g. NKDA → No Known Drug Allergies)."""
        return self.expand_diagnosis(raw) if raw else ""


# Singleton instance
medical_abbreviation_expander = MedicalAbbreviationExpander()
