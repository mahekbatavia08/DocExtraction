"""
business_card_extractor.py
────────────────────────────
Enterprise 25-Point Business Card Field Extraction & Spatial Classification Engine.

Stages:
  1. OCR Token Normalization & Spatial Bounding Box Analysis (center_x, center_y, width, height, font_scale)
  2. Field Priority Classification Engine (Email -> Phone -> Website -> Address -> Designation -> Company -> Name)
  3. Strict Anti-Contamination Rules (Email/Phone/Address can NEVER become Company or Name)
  4. Candidate Scoring & Spatial Relationship Heuristics
  5. Standardized JSON Output with Confidence Scores & Raw Bounding Box Tokens
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class OCRToken:
    text: str
    normalized_text: str
    confidence: float
    bbox: List[List[float]]
    x1: float
    y1: float
    x2: float
    y2: float
    center_x: float
    center_y: float
    width: float
    height: float

DESIGNATION_TITLES = [
    "CHARTERED ACCOUNTANT", "ACCOUNTANT", "SOFTWARE ENGINEER", "DEVELOPER",
    "MANAGER", "GENERAL MANAGER", "PROJECT MANAGER", "SALES MANAGER", "MARKETING MANAGER",
    "DIRECTOR", "MANAGING DIRECTOR", "EXECUTIVE DIRECTOR", "CEO", "CTO", "CFO", "COO",
    "FOUNDER", "CO-FOUNDER", "PRESIDENT", "VICE PRESIDENT", "VP", "EXECUTIVE",
    "SPECIALIST", "CONSULTANT", "LAWYER", "ADVOCATE", "DOCTOR", "DR", "ARCHITECT",
    "PARTNER", "PROPRIETOR", "OWNER", "LEAD", "ASSOCIATE", "ANALYST", "OFFICER",
    "SECRETARY", "PRINCIPAL", "PROFESSOR", "ADVISOR", "CA"
]

COMPANY_KEYWORDS = [
    "SHOP", "STORE", "COMPANY", "FIRM", "LTD", "LIMITED", "PVT", "PRIVATE",
    "INC", "INCORPORATED", "LLP", "SERVICES", "SOLUTIONS", "INDUSTRIES",
    "ENTERPRISES", "STUDIO", "LABS", "CORP", "CORPORATION", "GROUP", "GLOBAL",
    "TECHNOLOGIES", "TECH", "ASSOCIATES", "CA & CO", "JEWELLERS", "CLOTHING",
    "TRADERS", "AGENCY", "CREATIVE", "WORKS"
]

ADDRESS_KEYWORDS = [
    "ADDRESS", "LOCATION", "LANDMARK", "ROAD", "STREET", "NAGAR", "MARG", "GALI",
    "PLOT", "FLAT", "SHOP NO", "OFFICE", "SUITE", "FLOOR", "BUILDING", "TOWER",
    "NEAR", "OPP", "OPPOSITE", "BEHIND", "CITY", "STATE", "PIN", "PINCODE",
    "SURAT", "AHMEDABAD", "MUMBAI", "DELHI", "BANGALORE", "BENGALURU", "HYDERABAD",
    "CHENNAI", "KOLKATA", "PUNE", "GUJARAT", "MAHARASHTRA"
]

class BusinessCardExtractor:

    def normalize_text(self, raw_text: str) -> str:
        """Preserves @, ., +, -, /, digits, and letters while trimming extra whitespace."""
        if not raw_text:
            return ""
        text = re.sub(r'\s+', ' ', raw_text.strip())
        return text

    def parse_tokens(self, ocr_results: List[Tuple[List[List[float]], str, float]]) -> List[OCRToken]:
        """Converts raw OCR detection bounding boxes into normalized OCRToken objects."""
        tokens: List[OCRToken] = []

        for item in ocr_results:
            if len(item) == 3:
                bbox_pts, text, conf = item
            else:
                continue

            cleaned_text = self.normalize_text(text)
            if not cleaned_text:
                continue

            xs = [pt[0] for pt in bbox_pts]
            ys = [pt[1] for pt in bbox_pts]

            x1, x2 = min(xs), max(xs)
            y1, y2 = min(ys), max(ys)
            width = max(1.0, x2 - x1)
            height = max(1.0, y2 - y1)
            center_x = x1 + (width / 2.0)
            center_y = y1 + (height / 2.0)

            tokens.append(OCRToken(
                text=text.strip(),
                normalized_text=cleaned_text,
                confidence=round(float(conf), 4),
                bbox=bbox_pts,
                x1=round(x1, 2),
                y1=round(y1, 2),
                x2=round(x2, 2),
                y2=round(y2, 2),
                center_x=round(center_x, 2),
                center_y=round(center_y, 2),
                width=round(width, 2),
                height=round(height, 2)
            ))

        return tokens

    def extract_structured_data(self, ocr_results: List[Tuple[List[List[float]], str, float]], raw_full_text: str = "") -> Dict[str, Any]:
        """
        25-Point Business Card Field Extraction Algorithm:
          Priority 1: Email (Regex)
          Priority 2: Phone (Multi-Format Regex)
          Priority 3: Website (Domain / URL Regex)
          Priority 4: Address / Location (Keywords & PIN regex)
          Priority 5: Designation (Title dictionary match)
          Priority 6: Company Name (Prominence, keywords, position)
          Priority 7: Person Name (Capitalization, non-assigned, proximity to designation)
        """
        tokens = self.parse_tokens(ocr_results)
        
        # Fallback if no bboxes passed: build synthetic tokens from raw_full_text lines
        if not tokens and raw_full_text:
            lines = [l.strip() for l in raw_full_text.splitlines() if l.strip()]
            for idx, line in enumerate(lines):
                tokens.append(OCRToken(
                    text=line,
                    normalized_text=self.normalize_text(line),
                    confidence=0.90,
                    bbox=[[0, idx * 30], [200, idx * 30], [200, idx * 30 + 25], [0, idx * 30 + 25]],
                    x1=0, y1=idx * 30, x2=200, y2=idx * 30 + 25,
                    center_x=100, center_y=idx * 30 + 12.5,
                    width=200, height=25
                ))

        assigned_token_indices = set()
        fields: Dict[str, Optional[str]] = {
            "name": None,
            "company": None,
            "designation": None,
            "phone": None,
            "email": None,
            "website": None,
            "address": None
        }
        confidence_scores: Dict[str, float] = {
            "name": 0.0,
            "company": 0.0,
            "designation": 0.0,
            "phone": 0.0,
            "email": 0.0,
            "website": 0.0,
            "address": 0.0
        }

        # ── Priority 1: EMAIL DETECTION ──────────────────────────────────────
        email_regex = re.compile(r'\b[a-zA-Z0-9._%+-]+(?:\s*@\s*|\s*\[at\]\s*)[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}\b', re.IGNORECASE)
        for i, token in enumerate(tokens):
            m = email_regex.search(token.normalized_text)
            if m:
                email_val = m.group(0).replace(" ", "").replace("[at]", "@")
                fields["email"] = email_val
                confidence_scores["email"] = round(token.confidence, 2)
                assigned_token_indices.add(i)
                break

        # ── Priority 2: PHONE DETECTION ──────────────────────────────────────
        # Supports +91-0000000000, +91 9876543210, 9876543210, (123) 456-7890, +1 555 123 4567
        phone_regex = re.compile(
            r'(?:\+\s?91[\s.-]*)?[6-9]\d{4}[\s.-]*\d{5}\b|(?:\+\s?\d{1,4}[\s.-]*)?\(?\d{2,5}\)?[\s.-]*\d{3,5}[\s.-]*\d{3,5}\b|\b[6-9]\d{9}\b|\b\d{10}\b',
            re.IGNORECASE
        )
        for i, token in enumerate(tokens):
            if i in assigned_token_indices:
                continue
            m = phone_regex.search(token.normalized_text)
            if m:
                phone_val = m.group(0).strip()
                fields["phone"] = phone_val
                confidence_scores["phone"] = round(token.confidence, 2)
                assigned_token_indices.add(i)
                break

        # ── Priority 3: WEBSITE DETECTION ─────────────────────────────────────
        web_regex = re.compile(r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|in|co\.in|org|net|io|ai|biz|gov)(?:/[^\s]*)?', re.IGNORECASE)
        for i, token in enumerate(tokens):
            if i in assigned_token_indices:
                continue
            m = web_regex.search(token.normalized_text)
            if m and "@" not in token.normalized_text:
                web_val = m.group(0).strip()
                fields["website"] = web_val
                confidence_scores["website"] = round(token.confidence, 2)
                assigned_token_indices.add(i)
                break

        # ── Priority 4: ADDRESS DETECTION ────────────────────────────────────
        address_tokens: List[Tuple[int, OCRToken]] = []
        for i, token in enumerate(tokens):
            if i in assigned_token_indices:
                continue
            u = token.normalized_text.upper()
            has_addr_kw = any(kw in u for kw in ADDRESS_KEYWORDS)
            has_pin = bool(re.search(r'\b[1-9][0-9]{5}\b', token.normalized_text))
            
            if has_addr_kw or has_pin:
                address_tokens.append((i, token))

        if address_tokens:
            combined_addr = ", ".join([t[1].text for t in address_tokens])
            fields["address"] = combined_addr
            avg_conf = sum(t[1].confidence for t in address_tokens) / len(address_tokens)
            confidence_scores["address"] = round(avg_conf, 2)
            for idx, _ in address_tokens:
                assigned_token_indices.add(idx)

        # ── Priority 5: DESIGNATION DETECTION ─────────────────────────────────
        best_desig_candidate: Optional[Tuple[int, OCRToken, int]] = None
        for i, token in enumerate(tokens):
            if i in assigned_token_indices:
                continue
            u = token.normalized_text.upper()
            matched_titles = [title for title in DESIGNATION_TITLES if re.search(r'\b' + re.escape(title) + r'\b', u)]
            if matched_titles:
                max_title_len = max(len(t) for t in matched_titles)
                if best_desig_candidate is None or max_title_len > best_desig_candidate[2]:
                    best_desig_candidate = (i, token, max_title_len)

        if best_desig_candidate:
            idx, tok, _ = best_desig_candidate
            fields["designation"] = tok.text
            confidence_scores["designation"] = round(tok.confidence, 2)
            assigned_token_indices.add(idx)

        # ── Priority 6: COMPANY NAME DETECTION ───────────────────────────────
        max_height = max([t.height for t in tokens]) if tokens else 1.0
        company_candidate: Optional[Tuple[int, OCRToken, float]] = None

        for i, token in enumerate(tokens):
            if i in assigned_token_indices:
                continue

            u = token.normalized_text.upper()
            score = 0.0

            # Signal 1: Company keyword ("SHOP", "STORE", "FIRM", "CO", etc.)
            if any(kw in u for kw in COMPANY_KEYWORDS):
                score += 50.0

            # Signal 2: Font size / height prominence
            size_ratio = token.height / max_height
            score += size_ratio * 30.0

            # Signal 3: Position (Top of card bias)
            if token.center_y < 200:
                score += 20.0

            if company_candidate is None or score > company_candidate[2]:
                company_candidate = (i, token, score)

        if company_candidate and company_candidate[2] >= 20.0:
            idx, tok, sc = company_candidate
            fields["company"] = tok.text
            confidence_scores["company"] = round(tok.confidence, 2)
            assigned_token_indices.add(idx)

        # ── Priority 7: PERSON NAME DETECTION ────────────────────────────────
        name_candidate: Optional[Tuple[int, OCRToken, float]] = None

        desig_y = None
        for tok in tokens:
            if fields["designation"] and tok.text == fields["designation"]:
                desig_y = tok.center_y
                break

        for i, token in enumerate(tokens):
            if i in assigned_token_indices:
                continue

            u = token.normalized_text.upper()
            
            # Anti-Contamination & Name Quality Checks:
            if len(token.text.strip()) < 3:
                continue
            if re.search(r'\d', token.text) or "@" in token.text or "WWW" in u:
                continue
            if u in DESIGNATION_TITLES or u in COMPANY_KEYWORDS:
                continue
            if any(kw in u for kw in ["ADDRESS", "LOCATION", "LANDMARK", "ROAD", "STREET", "PIN"]):
                continue

            words = token.text.split()
            if 1 <= len(words) <= 4:
                score = 20.0
                # Capitalized / Title Case bonus (e.g., "Your Name", "John Doe")
                if token.text.istitle():
                    score += 30.0

                # Multi-word name bonus ("First Last")
                if len(words) >= 2:
                    score += 25.0

                # Proximity bonus if directly adjacent to Designation title
                if desig_y is not None and abs(token.center_y - desig_y) <= 80:
                    score += 35.0

                if name_candidate is None or score > name_candidate[2]:
                    name_candidate = (i, token, score)

        if name_candidate:
            idx, tok, sc = name_candidate
            fields["name"] = tok.text
            confidence_scores["name"] = round(tok.confidence, 2)
            assigned_token_indices.add(idx)

        # ── STAGE C: Build Final Response Structure with Raw Bounding Boxes ────
        raw_ocr_export = [
            {
                "text": t.text,
                "confidence": t.confidence,
                "bbox": t.bbox,
                "center_x": t.center_x,
                "center_y": t.center_y,
                "width": t.width,
                "height": t.height
            }
            for t in tokens
        ]

        formatted_fields: Dict[str, str] = {}
        # Order: Name, Company, Designation, Phone, Email, Website, Address
        field_order = [
            ("name", "Name"),
            ("company", "Company"),
            ("designation", "Designation"),
            ("phone", "Phone"),
            ("email", "Email"),
            ("website", "Website"),
            ("address", "Address")
        ]
        for internal_key, display_key in field_order:
            val = fields[internal_key]
            formatted_fields[display_key] = val if val else "Not Found"

        return {
            "document_type": "Business Card",
            "fields": formatted_fields,
            "raw_fields": fields,
            "confidence": confidence_scores,
            "raw_ocr": raw_ocr_export,
            "tokens_count": len(tokens)
        }

business_card_extractor = BusinessCardExtractor()
