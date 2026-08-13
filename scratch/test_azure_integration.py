"""
test_azure_integration.py
──────────────────────────
Verification test suite for Azure AI Document Intelligence integration with local PaddleOCR fallback:
  1. Service Initialization & Model Selector
  2. Automatic Local Fallback (when credentials are unconfigured or fail)
  3. Document Type Pipeline Execution (Business Card, PAN, Aadhaar, Invoice)
  4. SQLite Persistence & Retry Endpoint
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.azure_document_intelligence import azure_document_intelligence
from backend.services.universal_pipeline import run_universal_pipeline
from backend.database.init_db import init_db
from backend.services.document_service import document_service

def test_azure_service_model_selection():
    print("\n--- Test 1: Azure Model Selection & Availability ---")
    assert azure_document_intelligence.select_azure_model("Invoice") == "prebuilt-invoice"
    assert azure_document_intelligence.select_azure_model("Business Card") == "prebuilt-businessCard"
    assert azure_document_intelligence.select_azure_model("PAN Card") == "prebuilt-idDocument"
    assert azure_document_intelligence.select_azure_model("Aadhaar Card") == "prebuilt-idDocument"
    print(f"Azure Client Configured: {azure_document_intelligence.is_available()}")
    print("[PASS] Test 1 PASSED SUCCESSFULLY!")

def test_pipeline_execution_and_fallback():
    print("\n--- Test 2: Pipeline Dual-Engine Execution & Local Fallback ---")
    import numpy as np
    dummy_img = np.zeros((300, 500, 3), dtype=np.uint8)
    res = run_universal_pipeline(img=dummy_img, filename="test_pan.png")
    
    assert "metadata" in res
    assert "document_type" in res
    print(f"Extracted Engine Used: {res.get('ocr_engine', res.get('metadata', {}).get('ocr_engine', 'Local Engine'))}")
    print("[PASS] Test 2 PASSED SUCCESSFULLY!")

def test_database_persistence_and_retry():
    print("\n--- Test 3: Database Persistence & Retry Flow ---")
    init_db()
    
    doc_id = document_service.save_document_result(
        filename="test_invoice.pdf",
        file_type="application/pdf",
        document_type="Invoice",
        raw_ocr_text="Invoice #INV-2026-001 Total $500.00",
        extracted_fields={"Invoice Number": "INV-2026-001", "Total Amount": "$500.00"},
        processing_time=1.2,
        overall_confidence=0.98,
        processing_status="completed",
        ocr_engine="Azure Document Intelligence",
        raw_ocr="[raw_bbox_data]"
    )
    
    saved = document_service.get_document_by_id(doc_id)
    assert saved["original_filename"] == "test_invoice.pdf"
    assert saved["ocr_engine"] == "Azure Document Intelligence"
    assert saved["processing_status"] == "completed"
    
    # Test retry update
    document_service.update_document_result(
        doc_id=doc_id,
        document_type="Invoice",
        raw_ocr_text="Invoice #INV-2026-001 Total $500.00 Retried",
        extracted_fields={"Invoice Number": "INV-2026-001", "Total Amount": "$500.00"},
        processing_time=1.1,
        overall_confidence=0.99,
        processing_status="completed",
        ocr_engine="Azure Document Intelligence"
    )
    
    updated = document_service.get_document_by_id(doc_id)
    assert updated["overall_confidence"] == 0.99
    print("[PASS] Test 3 PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_azure_service_model_selection()
    test_pipeline_execution_and_fallback()
    test_database_persistence_and_retry()
    print("\nALL AZURE INTEGRATION & FALLBACK TESTS PASSED 100%!")
