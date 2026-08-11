"""
document_classifier.py
────────────────────
Document Classification Service using Local Ollama LLM + Heuristic Regex Fallback Rules.
Supported Types:
- PAN_CARD
- AADHAAR_CARD
- BUSINESS_CARD
- DEBIT_CARD
- CREDIT_CARD
- DRIVING_LICENSE
- PASSPORT
- EMPLOYEE_ID
- STUDENT_ID
- INVOICE
- RECEIPT
- OTHER
- UNKNOWN
"""

import re
from typing import Dict, Any, Tuple
from backend.services.ai_service import ai_service
from backend.schemas.ai_schemas import AIDocumentClassification

CLASSIFY_PROMPT_INSTRUCTION = """
Classify the document into EXACTLY one of these types:
["PAN_CARD", "AADHAAR_CARD", "BUSINESS_CARD", "DEBIT_CARD", "CREDIT_CARD", "DRIVING_LICENSE", "PASSPORT", "EMPLOYEE_ID", "STUDENT_ID", "INVOICE", "RECEIPT", "OTHER", "UNKNOWN"]

Respond in JSON format:
{
  "document_type": "<TYPE>",
  "confidence": 0.95,
  "reasoning": "<short sentence>"
}
"""

class DocumentClassifier:

    def classify(self, raw_ocr_text: str, filename: str = "") -> AIDocumentClassification:
        """Classifies document using local AI if available, falling back to heuristic regex rules."""
        text_lower = raw_ocr_text.lower()
        fn_lower = filename.lower()

        # 1. Local LLM Classification Attempt
        ai_res = ai_service.query_local_llm(raw_ocr_text, CLASSIFY_PROMPT_INSTRUCTION)
        if ai_res and "document_type" in ai_res:
            doc_type = str(ai_res.get("document_type", "UNKNOWN")).upper()
            conf = float(ai_res.get("confidence", 0.90))
            return AIDocumentClassification(
                document_type=doc_type,
                confidence=conf,
                reasoning=ai_res.get("reasoning", "Local LLM Classification")
            )

        # 2. Fallback Heuristic Regex Rules (Deterministic)
        # PAN Card
        if re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', raw_ocr_text) or 'income tax department' in text_lower or 'permanent account number' in text_lower:
            return AIDocumentClassification(document_type="PAN_CARD", confidence=0.98, reasoning="Matched PAN pattern [A-Z]{5}[0-9]{4}[A-Z]")

        # Aadhaar Card
        if 'aadhaar' in text_lower or 'unique identification authority' in text_lower or 'mera aadhaar' in text_lower or re.search(r'\b[1-9][0-9]{3}\s[0-9]{4}\s[0-9]{4}\b', raw_ocr_text):
            return AIDocumentClassification(document_type="AADHAAR_CARD", confidence=0.98, reasoning="Matched Aadhaar keywords / 12-digit UID pattern")

        # Business Card
        has_contact_info = ('email' in text_lower or '@' in text_lower) and ('phone' in text_lower or 'mobile' in text_lower or 'tel' in text_lower or '+' in text_lower)
        has_business_terms = any(term in text_lower for term in ['designation', 'manager', 'director', 'officer', 'ceo', 'cto', 'lead', 'engineer', 'developer', 'consultant', 'executive', 'founder', 'vp', 'president', 'head', 'corp', 'ltd', 'pvt', 'inc', 'website', 'www', '.com'])
        if has_contact_info and has_business_terms:
            return AIDocumentClassification(document_type="BUSINESS_CARD", confidence=0.95, reasoning="Matched Business Card contact and corporate structure")

        # Payment Cards (Debit / Credit)
        if any(term in text_lower for term in ['visa', 'mastercard', 'rupay', 'american express', 'debit card', 'credit card', 'valid thru', 'expiry']):
            if 'debit' in text_lower:
                return AIDocumentClassification(document_type="DEBIT_CARD", confidence=0.95, reasoning="Matched Debit Card indicators")
            return AIDocumentClassification(document_type="CREDIT_CARD", confidence=0.95, reasoning="Matched Credit Card indicators")

        # Driving License
        if 'driving' in text_lower or 'dl no' in text_lower or 'licence' in text_lower or re.search(r'\b[A-Z]{2}[0-9]{2}\s?[0-9]{11}\b', raw_ocr_text):
            return AIDocumentClassification(document_type="DRIVING_LICENSE", confidence=0.95, reasoning="Matched Driving License indicators")

        # Passport
        if 'republic of india' in text_lower and ('passport' in text_lower or 'type p' in text_lower):
            return AIDocumentClassification(document_type="PASSPORT", confidence=0.96, reasoning="Matched Indian Passport layout")

        # Invoice / Receipt
        if any(term in text_lower for term in ['invoice', 'bill no', 'subtotal', 'tax invoice', 'gstin']):
            return AIDocumentClassification(document_type="INVOICE", confidence=0.94, reasoning="Matched Invoice financial headers")

        if 'receipt' in text_lower or 'total paid' in text_lower:
            return AIDocumentClassification(document_type="RECEIPT", confidence=0.90, reasoning="Matched Receipt headers")

        return AIDocumentClassification(document_type="UNKNOWN", confidence=0.50, reasoning="Default fallback classification")

document_classifier = DocumentClassifier()
