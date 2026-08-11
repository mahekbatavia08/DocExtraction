"""
extraction_service.py
──────────────────────
Field normalization, entity extraction, and strict sensitive data masking service.
Enforces security guidelines:
- Aadhaar numbers stored only as masked values (XXXX XXXX 1234).
- Credit/Debit cards stored only as masked values (XXXX-XXXX-XXXX-1234).
- CVV codes strictly removed and NEVER stored in the database.
"""

import re
from typing import Dict, Any, List, Tuple

class DataExtractionService:

    @staticmethod
    def mask_aadhaar_number(text: str) -> str:
        """Mask 12-digit Aadhaar number leaving only last 4 digits visible."""
        if not text:
            return ""
        # Match 12 digits separated by spaces, hyphens, or nothing
        pattern = r'\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b'
        def repl(match):
            last4 = match.group(3)
            return f"XXXX XXXX {last4}"
        return re.sub(pattern, repl, text)

    @staticmethod
    def mask_credit_card_number(text: str) -> str:
        """Mask 13-19 digit payment card number leaving only last 4 digits visible."""
        if not text:
            return ""
        pattern = r'\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{1,7})\b'
        def repl(match):
            last_group = match.group(4)
            last4 = last_group[-4:] if len(last_group) >= 4 else last_group
            return f"XXXX-XXXX-XXXX-{last4}"
        return re.sub(pattern, repl, text)

    @staticmethod
    def sanitize_cvv_and_sensitive_text(raw_text: str) -> str:
        """Sanitize raw OCR text to mask CVVs, credit card numbers, and Aadhaar numbers."""
        if not raw_text:
            return ""
        
        # 1. Remove CVV / CVC lines or key-values
        sanitized = re.sub(r'(?i)\b(cvv|cvc|cvv2|security code|card code)\b\s*[:=\-]?\s*\d{3,4}\b', r'\1: ***', raw_text)
        
        # 2. Mask Aadhaar numbers in text
        sanitized = DataExtractionService.mask_aadhaar_number(sanitized)
        
        # 3. Mask Credit/Debit card numbers in text
        sanitized = DataExtractionService.mask_credit_card_number(sanitized)
        
        return sanitized

    @staticmethod
    def sanitize_extracted_fields(fields: Dict[str, Any], doc_type: str = "Unknown") -> Dict[str, str]:
        """
        Process key-value extracted fields:
        - Removes CVV entirely.
        - Masks Aadhaar numbers.
        - Masks Payment Card numbers.
        """
        sanitized_fields: Dict[str, str] = {}

        for key, value in fields.items():
            k_lower = key.lower()
            val_str = str(value).strip()

            # Strictly reject CVV/CVC fields
            if any(term in k_lower for term in ['cvv', 'cvc', 'cvv2', 'security code', 'security_code']):
                continue

            # Mask Aadhaar numbers
            if 'aadhaar' in k_lower or 'uid' in k_lower or doc_type == "Aadhaar Card":
                val_str = DataExtractionService.mask_aadhaar_number(val_str)
            
            # Mask Card numbers
            if any(term in k_lower for term in ['card number', 'card_number', 'credit_card', 'debit_card', 'pan_number']) and 'pan' not in k_lower:
                val_str = DataExtractionService.mask_credit_card_number(val_str)
            elif doc_type in ["Debit Card", "Credit Card", "Payment Card"]:
                if any(char.isdigit() for char in val_str) and len(re.findall(r'\d', val_str)) >= 12:
                    val_str = DataExtractionService.mask_credit_card_number(val_str)

            # Sanitize any residual occurrences inside string values
            val_str = DataExtractionService.sanitize_cvv_and_sensitive_text(val_str)

            sanitized_fields[key] = val_str

        return sanitized_fields

    @staticmethod
    def extract_business_contact(fields: Dict[str, Any], raw_text: str = "") -> Dict[str, str]:
        """
        Extract structured Business Contact details from fields or raw text.
        Returns dictionary with keys: name, company, designation, email, phone, website, address.
        """
        contact = {
            "name": "",
            "company": "",
            "designation": "",
            "email": "",
            "phone": "",
            "website": "",
            "address": ""
        }

        # Match from extracted fields first
        for key, val in fields.items():
            k = key.lower()
            v = str(val).strip()
            if not v:
                continue

            if any(term in k for term in ['name', 'holder', 'full_name', 'cardholder']) and not contact["name"]:
                contact["name"] = v
            elif any(term in k for term in ['company', 'organization', 'org', 'firm']) and not contact["company"]:
                contact["company"] = v
            elif any(term in k for term in ['designation', 'title', 'role', 'position', 'job']) and not contact["designation"]:
                contact["designation"] = v
            elif 'email' in k and not contact["email"]:
                contact["email"] = v
            elif any(term in k for term in ['phone', 'mobile', 'tel', 'call', 'contact']) and not contact["phone"]:
                contact["phone"] = v
            elif any(term in k for term in ['website', 'url', 'site', 'web']) and not contact["website"]:
                contact["website"] = v
            elif any(term in k for term in ['address', 'location', 'street', 'city']) and not contact["address"]:
                contact["address"] = v

        # Fallback regex extraction from raw_text if missing
        if not contact["email"] and raw_text:
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', raw_text)
            if email_match:
                contact["email"] = email_match.group(0)

        if not contact["phone"] and raw_text:
            phone_match = re.search(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', raw_text)
            if phone_match:
                contact["phone"] = phone_match.group(0)

        if not contact["website"] and raw_text:
            web_match = re.search(r'\b(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?\b', raw_text)
            if web_match and '@' not in web_match.group(0):
                contact["website"] = web_match.group(0)

        return contact

extraction_service = DataExtractionService()
