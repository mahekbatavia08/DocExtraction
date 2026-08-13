"""
azure_document_intelligence.py
───────────────────────────────
Enterprise Service wrapper for Azure AI Document Intelligence API.

Capabilities:
  - Connects securely to Azure AI Document Intelligence using Python SDK v1.0.2+
  - Supports Prebuilt Models:
      • prebuilt-read (General Document OCR)
      • prebuilt-layout (Layout, Tables, Paragraphs)
      • prebuilt-invoice (Invoices & Receipts)
      • prebuilt-businessCard (Business Cards)
      • prebuilt-idDocument (ID Cards, PAN Cards, Passports)
  - Extracts raw text, spatial polygon bounding boxes, tables, key-value pairs, and fields
  - Computes normalized confidence scores (0.0 to 1.0)
  - Graceful Fallback check if credentials are missing or API fails
"""

import time
import re
from typing import Dict, Any, List, Optional, Tuple

from backend.config import (
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
    AZURE_DOCUMENT_INTELLIGENCE_KEY,
    AZURE_DOCUMENT_INTELLIGENCE_MODEL,
    EXTRACTION_ENGINE
)
from backend.utils.logger import logger

class AzureDocumentIntelligenceService:

    def __init__(self):
        self.endpoint = AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
        self.key = AZURE_DOCUMENT_INTELLIGENCE_KEY
        self.default_model = AZURE_DOCUMENT_INTELLIGENCE_MODEL or "prebuilt-read"
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initializes Azure Document Intelligence Python SDK client if credentials are configured."""
        if not self.endpoint or not self.key:
            logger.log_step("Azure Document Intelligence", "Credentials not configured — running in Fallback/Local Mode.")
            return

        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential

            self.client = DocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
            logger.log_step("Azure Document Intelligence", f"Client initialized successfully (Endpoint: {self.endpoint})")
        except Exception as e:
            logger.log_step("Azure Client Error", f"Failed to initialize Azure Document Intelligence: {str(e)}")
            self.client = None

    def is_available(self) -> bool:
        """Returns True if Azure client is configured and available."""
        return self.client is not None and bool(self.endpoint) and bool(self.key)

    def select_azure_model(self, doc_type: str) -> str:
        """Selects optimal Azure prebuilt model based on document type."""
        dt = (doc_type or "").upper()
        if "INVOICE" in dt or "RECEIPT" in dt or "BILL" in dt:
            return "prebuilt-invoice"
        elif "BUSINESS" in dt or "CARD" in dt and "PAN" not in dt and "ID" not in dt and "AADHAAR" not in dt:
            return "prebuilt-businessCard"
        elif "PAN" in dt or "AADHAAR" in dt or "PASSPORT" in dt or "ID" in dt or "LICENSE" in dt:
            return "prebuilt-idDocument"
        return self.default_model

    def analyze_document(self, file_bytes: bytes, doc_type: str = "General Document") -> Dict[str, Any]:
        """
        Executes Azure AI Document Intelligence analysis on raw document bytes.
        Returns standardized dictionary output with fields, confidence scores, tables, and raw OCR bboxes.
        """
        if not self.is_available():
            raise ValueError("Azure Document Intelligence credentials are not configured.")

        start_time = time.time()
        model_id = self.select_azure_model(doc_type)

        logger.log_step("Azure AI Analysis", f"Sending document to Azure Document Intelligence (Model: '{model_id}')")

        try:
            poller = self.client.begin_analyze_document(
                model_id=model_id,
                analyze_request=file_bytes,
                content_type="application/octet-stream"
            )
            result = poller.result()
            proc_time = round(time.time() - start_time, 3)

            full_text = getattr(result, "content", "") or ""
            raw_tokens: List[Dict[str, Any]] = []
            extracted_fields: Dict[str, str] = {}
            confidence_scores: Dict[str, float] = {}
            conf_list: List[float] = []

            # 1. Parse Pages, Lines, Words & Spatial Polygon Bounding Boxes
            if hasattr(result, "pages") and result.pages:
                for page in result.pages:
                    w_page = getattr(page, "width", 1000.0) or 1000.0
                    h_page = getattr(page, "height", 1000.0) or 1000.0

                    lines = getattr(page, "lines", []) or []
                    for idx, line in enumerate(lines):
                        line_text = getattr(line, "content", "") or ""
                        if not line_text.strip():
                            continue

                        # Extract polygon coordinates
                        poly = getattr(line, "polygon", []) or []
                        bbox = []
                        if poly and len(poly) >= 8:
                            # 4 corners [x1,y1, x2,y2, x3,y3, x4,y4]
                            bbox = [
                                [float(poly[0]), float(poly[1])],
                                [float(poly[2]), float(poly[3])],
                                [float(poly[4]), float(poly[5])],
                                [float(poly[6]), float(poly[7])]
                            ]
                        else:
                            bbox = [[0.0, idx * 30.0], [w_page, idx * 30.0], [w_page, idx * 30.0 + 25.0], [0.0, idx * 30.0 + 25.0]]

                        xs = [pt[0] for pt in bbox]
                        ys = [pt[1] for pt in bbox]
                        x1, x2 = min(xs), max(xs)
                        y1, y2 = min(ys), max(ys)
                        bw = max(1.0, x2 - x1)
                        bh = max(1.0, y2 - y1)

                        # Estimate confidence from words if line confidence not directly present
                        words = getattr(line, "words", []) or []
                        word_confs = [getattr(w, "confidence", 0.95) for w in words if getattr(w, "confidence", None) is not None]
                        line_conf = sum(word_confs) / len(word_confs) if word_confs else 0.95
                        conf_list.append(line_conf)

                        raw_tokens.append({
                            "text": line_text.strip(),
                            "confidence": round(float(line_conf), 4),
                            "bbox": bbox,
                            "center_x": round(x1 + bw / 2.0, 2),
                            "center_y": round(y1 + bh / 2.0, 2),
                            "width": round(bw, 2),
                            "height": round(bh, 2)
                        })

            # 2. Parse Prebuilt Key-Value Fields & Structured Document Documents
            if hasattr(result, "documents") and result.documents:
                for doc in result.documents:
                    fields = getattr(doc, "fields", {}) or {}
                    for fname, fval in fields.items():
                        if fval is None:
                            continue
                        
                        val_str = ""
                        if hasattr(fval, "value_string") and fval.value_string:
                            val_str = fval.value_string
                        elif hasattr(fval, "content") and fval.content:
                            val_str = fval.content
                        elif hasattr(fval, "value") and fval.value is not None:
                            val_str = str(fval.value)
                        
                        conf = float(getattr(fval, "confidence", 0.95) or 0.95)
                        if val_str.strip():
                            # Clean field name key (CamelCase -> Capitalized)
                            clean_fname = re.sub(r'(?<!^)(?=[A-Z])', ' ', fname).title().strip()
                            extracted_fields[clean_fname] = val_str.strip()
                            confidence_scores[clean_fname.lower()] = round(conf, 2)

            # 3. Parse Key-Value Pairs (from layout model)
            if hasattr(result, "key_value_pairs") and result.key_value_pairs:
                for kv in result.key_value_pairs:
                    k_obj = getattr(kv, "key", None)
                    v_obj = getattr(kv, "value", None)
                    if k_obj and v_obj:
                        k_text = getattr(k_obj, "content", "").strip()
                        v_text = getattr(v_obj, "content", "").strip()
                        conf = float(getattr(kv, "confidence", 0.90) or 0.90)
                        if k_text and v_text and k_text not in extracted_fields:
                            extracted_fields[k_text] = v_text
                            confidence_scores[k_text.lower()] = round(conf, 2)

            # 4. Parse Tables & Line Items
            tables_data = []
            if hasattr(result, "tables") and result.tables:
                for table in result.tables:
                    t_info = {"rows": getattr(table, "row_count", 0), "cols": getattr(table, "column_count", 0), "cells": []}
                    cells = getattr(table, "cells", []) or []
                    for cell in cells:
                        t_info["cells"].append({
                            "row": getattr(cell, "row_index", 0),
                            "col": getattr(cell, "column_index", 0),
                            "text": getattr(cell, "content", "").strip()
                        })
                    tables_data.append(t_info)

            avg_conf = round(sum(conf_list) / len(conf_list), 4) if conf_list else 0.95

            logger.log_step(
                "Azure Analysis Success",
                f"Extracted {len(raw_tokens)} text tokens, {len(extracted_fields)} fields, {len(tables_data)} tables in {proc_time}s"
            )

            return {
                "success": True,
                "ocr_engine": "Azure Document Intelligence",
                "model_used": model_id,
                "raw_text": full_text,
                "fields": extracted_fields,
                "confidence_scores": confidence_scores,
                "overall_confidence": avg_conf,
                "raw_ocr_tokens": raw_tokens,
                "tables": tables_data,
                "processing_time": proc_time
            }

        except Exception as err:
            logger.log_step("Azure Analysis Failure", f"Azure API Error: {str(err)}")
            raise err

azure_document_intelligence = AzureDocumentIntelligenceService()
