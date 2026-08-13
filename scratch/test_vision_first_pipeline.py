"""
test_vision_first_pipeline.py
───────────────────────────────
Verification test script for Vision-First 10-Model Queue execution.
"""

import sys
import os
import cv2
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.universal_pipeline import run_universal_pipeline
from backend.services.openrouter_service import openrouter_service, GENERAL_DOCUMENT_VISION_PROMPT
from backend.utils.logger import logger

def test_pipeline():
    print("\n--- TEST 1: Synthetic Document Image Creation ---")
    img = np.ones((400, 800, 3), dtype=np.uint8) * 255
    cv2.putText(img, "INVOICE #INV-99823", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(img, "Customer: Acme Corp", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "Total Amount: $1,250.00", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    _, img_buf = cv2.imencode(".jpg", img)
    file_bytes = img_buf.tobytes()

    print("\n--- TEST 2: Testing openrouter_service module & prompt ---")
    print(f"Vision models queue count: {len(openrouter_service.models)}")
    print(f"Top 3 models: {openrouter_service.models[:3]}")

    print("\n--- TEST 3: Running Pipeline in OCR Fallback Mode (No API key) ---")
    res_fallback = run_universal_pipeline(img=img, file_bytes=file_bytes, filename="test_invoice.jpg")
    print(f"Fallback Engine Used: {res_fallback.get('ocr_engine')}")
    assert res_fallback.get('success') is True

    print("\n--- TEST 4: Mocking 10-Model Vision First Success ---")
    import backend.services.universal_pipeline as up_mod
    original_key = up_mod.OPENROUTER_API_KEY
    up_mod.OPENROUTER_API_KEY = "sk-or-v1-mock-key"

    def mock_extract_vision(bytes_in, ocr_text="", filename=""):
        return {
            "document_type": "Invoice",
            "overall_confidence": 0.98,
            "raw_text": "INVOICE #INV-99823\nCustomer: Acme Corp\nTotal Amount: $1,250.00",
            "fields": {
                "Invoice Number": "INV-99823",
                "Customer Name": "Acme Corp",
                "Total Amount": "$1,250.00"
            },
            "tables": [],
            "model_used": "nvidia/nemotron-4-340b-instruct:free"
        }, [{"model": "nvidia/nemotron-4-340b-instruct:free", "status": "success"}]

    original_method = openrouter_service.extract_document_vision
    openrouter_service.extract_document_vision = mock_extract_vision

    try:
        res_vision = run_universal_pipeline(img=img, file_bytes=file_bytes, filename="test_invoice.jpg")
        print(f"Vision-First Engine Used: {res_vision.get('ocr_engine')}")
        print(f"Extracted Fields: {res_vision.get('fields')}")
        print(f"Metadata Model: {res_vision.get('metadata', {}).get('model_used')}")

        assert "OpenRouter Vision LLM" in res_vision.get('ocr_engine')
        assert res_vision.get('fields', {}).get('Invoice Number') == "INV-99823"
        assert res_vision.get('fields', {}).get('Customer Name') == "Acme Corp"
        print("\nSUCCESS: All Vision-First & Fallback pipeline tests passed cleanly!")

    finally:
        up_mod.OPENROUTER_API_KEY = original_key
        openrouter_service.extract_document_vision = original_method

if __name__ == "__main__":
    test_pipeline()
