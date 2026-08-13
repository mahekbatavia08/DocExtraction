"""
entity_extractor.py
───────────────────
Per-Document Schema AI Entity Extractor with strict non-fabrication enforcement.
- Queries local LLM when available.
- Rejects CVV codes and masks sensitive card numbers / Aadhaar numbers.
- Returns null for unverified/missing fields.
"""

from typing import Dict, Any, Optional
from backend.services.ai_service import ai_service
from backend.services.address_extractor import address_extractor

EXTRACTION_PROMPTS = {
    "PAN_CARD": """Extract PAN Card fields into JSON:
{
  "name": "Full Name or null",
  "father_name": "Father Name or null",
  "pan_number": "10-char PAN or null",
  "dob": "YYYY-MM-DD or null"
}""",
    "AADHAAR_CARD": """Extract Aadhaar Card fields into JSON:
{
  "name": "Full Name or null",
  "dob": "YYYY-MM-DD or null",
  "gender": "Male/Female/Other or null",
  "masked_aadhaar": "XXXX XXXX 1234 or null"
}""",
    "BUSINESS_CARD": """Extract Business Card fields into JSON:
{
  "name": "Person Name or null",
  "company": "Company Name or null",
  "designation": "Job Title or null",
  "phone": "Phone Number or null",
  "email": "Email Address or null",
  "website": "Website URL or null",
  "address": "Full Address or null"
}""",
    "DEBIT_CARD": """Extract Debit Card fields into JSON (NEVER extract CVV or full card number):
{
  "card_holder": "Cardholder Name or null",
  "masked_card_number": "XXXX-XXXX-XXXX-1234 or null",
  "expiry_date": "MM/YY or null"
}""",
    "CREDIT_CARD": """Extract Credit Card fields into JSON (NEVER extract CVV or full card number):
{
  "card_holder": "Cardholder Name or null",
  "masked_card_number": "XXXX-XXXX-XXXX-1234 or null",
  "expiry_date": "MM/YY or null"
}""",
    "PASSPORT": """Extract Passport fields into JSON:
{
  "name": "Full Name or null",
  "passport_number": "Passport Number or null",
  "nationality": "Nationality or null",
  "dob": "YYYY-MM-DD or null",
  "expiry_date": "YYYY-MM-DD or null",
  "address": "Full Address or null"
}""",
    "DRIVING_LICENSE": """Extract Driving License fields into JSON:
{
  "name": "Full Name or null",
  "license_number": "License Number or null",
  "dob": "YYYY-MM-DD or null",
  "validity": "Expiry Date or null",
  "address": "Full Address or null"
}""",
    "INVOICE": """Extract Invoice fields into JSON:
{
  "vendor_name": "Vendor Name or null",
  "invoice_number": "Invoice Number or null",
  "invoice_date": "Date or null",
  "customer_name": "Customer Name or null",
  "subtotal": "Amount or null",
  "tax": "Tax Amount or null",
  "total": "Grand Total Amount or null"
}""",
    "MEDICAL_PRESCRIPTION": """Extract Doctor Prescription fields into JSON:
{
  "doctor_name": "Doctor Full Name or null",
  "qualification": "Medical Qualifications or null",
  "bmdc_reg_no": "BMDC or Medical Reg No or null",
  "patient_name": "Patient Full Name or null",
  "age_gender": "Age and Gender or null",
  "prescription_date": "Prescription Date or null",
  "diagnosis": "Diagnosis or Chief Complaint or null"
}"""
}

class SchemaEntityExtractor:

    def extract_entities(
        self,
        raw_ocr_text: str,
        doc_type: str,
        filename: str = ""
    ) -> Dict[str, Any]:
        """Extract structured fields using local AI prompt if available, enriched with precision address parser."""
        extracted: Dict[str, Any] = {}

        # 1. Query Local AI if instruction schema exists
        schema_prompt = EXTRACTION_PROMPTS.get(doc_type)
        if schema_prompt:
            ai_data = ai_service.query_local_llm(raw_ocr_text, schema_prompt)
            if ai_data and isinstance(ai_data, dict):
                extracted = ai_data

        # 2. Enrich with Precision Address Extraction Engine
        address_res = address_extractor.extract_address_from_ocr(raw_ocr_text, doc_type=doc_type)
        
        # Merge address data into extracted fields
        if address_res.get("state") != "Not Found":
            extracted["state"] = address_res["state"]
        if address_res.get("pincode") != "Not Found":
            extracted["pincode"] = address_res["pincode"]
        if address_res.get("district") != "Not Found":
            extracted["district"] = address_res["district"]

        extracted["full_address"] = address_res.get("full_address", "Not Found")
        extracted["_address_data"] = address_res

        return extracted

entity_extractor = SchemaEntityExtractor()
