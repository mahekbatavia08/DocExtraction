"""
test_universal_pipeline.py
───────────────────────────
Unit tests for the Universal AI Document Processing System (Zero-Error Mode):
- Verhoeff Aadhaar Checksum Algorithm
- PAN Card Regex & Entity Structure Rules
- Invoice Arithmetic Verification
- Document Classification & Origin Detection
- 8-Stage Pipeline Execution & Security Redaction
"""

import unittest
import numpy as np
import cv2

from backend.utils.validators import (
    validate_verhoeff,
    mask_aadhaar_number,
    validate_pan_number,
    audit_invoice_arithmetic,
    normalize_date
)
from backend.services.classifier_service import classify_document
from backend.services.universal_pipeline import run_universal_pipeline

class TestUniversalPipeline(unittest.TestCase):

    def test_verhoeff_algorithm(self):
        from backend.utils.validators import generate_verhoeff_checksum
        valid_uid = generate_verhoeff_checksum("23456789012")  # Generates 12-digit valid Verhoeff UID
        invalid_uid = "123456789012"

        self.assertTrue(validate_verhoeff(valid_uid))
        self.assertFalse(validate_verhoeff(invalid_uid))

        masked = mask_aadhaar_number(valid_uid)
        self.assertTrue(masked.startswith("XXXX XXXX "))

    def test_pan_card_validation(self):
        # Valid Individual PAN (4th letter 'P')
        pan_res = validate_pan_number("ABCPK1234F")
        self.assertTrue(pan_res["is_valid"])
        self.assertEqual(pan_res["entity_type"], "Individual Person")

        # Company PAN (4th letter 'C')
        company_pan = validate_pan_number("ABCCK1234F")
        self.assertTrue(company_pan["is_valid"])
        self.assertEqual(company_pan["entity_type"], "Company")

        # Invalid PAN
        invalid_pan = validate_pan_number("INVALID123")
        self.assertFalse(invalid_pan["is_valid"])

    def test_invoice_arithmetic_audit(self):
        sample_fields = {
            "Subtotal": "$100.00",
            "Tax / GST": "$18.00",
            "Discount": "$5.00",
            "Grand Total": "$113.00"
        }
        audit = audit_invoice_arithmetic(sample_fields, raw_text="")
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["computed_grand_total"], 113.00)

        # Discrepancy test
        bad_fields = {
            "Subtotal": "$100.00",
            "Tax / GST": "$18.00",
            "Grand Total": "$999.00"
        }
        bad_audit = audit_invoice_arithmetic(bad_fields, raw_text="")
        self.assertEqual(bad_audit["status"], "DISCREPANCY_FOUND")

    def test_document_classification(self):
        text_pan = "INCOME TAX DEPARTMENT GOVT OF INDIA PERMANENT ACCOUNT NUMBER ABCPE1234F"
        cls_pan = classify_document(text_pan, filename="pan_scan.jpg")
        self.assertEqual(cls_pan["document_type"], "PAN Card")

        text_aadhaar = "UNIQUE IDENTIFICATION AUTHORITY OF INDIA AADHAAR 1234 5678 9012"
        cls_aadhaar = classify_document(text_aadhaar, filename="aadhaar.png")
        self.assertEqual(cls_aadhaar["document_type"], "Aadhaar Card")

        text_invoice = "TAX INVOICE Subtotal: $100.00 GST: $18.00 Grand Total: $118.00"
        cls_inv = classify_document(text_invoice, filename="invoice.pdf")
        self.assertEqual(cls_inv["document_type"], "Invoice / Billing Receipt")

    def test_universal_pipeline_execution(self):
        img = np.ones((500, 800, 3), dtype=np.uint8) * 255
        output = run_universal_pipeline(img=img, filename="pan_scan.jpg")
        self.assertIn("metadata", output)
        self.assertIn("validation", output)
        self.assertIn("audit_log", output)
        self.assertIn("security", output)

if __name__ == "__main__":
    unittest.main()
