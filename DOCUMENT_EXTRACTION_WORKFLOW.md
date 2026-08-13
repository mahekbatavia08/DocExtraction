# Vision-Based Document Extraction Workflow & Architecture Documentation

This document explains the end-to-end architecture, data flow, APIs, JSON schema, 4-tier confidence system, validation process, and human review loop of the **Vision-Based Document Understanding Pipeline**.

---

## 1. System Architecture

```text
                  DOCUMENT IMAGE / PDF / CAMERA
                                │
                                ▼
         Stage 1: Preprocessing & Handwriting Optimization
         (Deskewing, CLAHE Contrast, Bilateral Noise Filtering)
                                │
                                ▼
         Stage 2: Deep OCR Extraction (Azure AI / PaddleOCR)
            Tokens: {text, bbox, confidence, page, line, word}
                                │
                                ▼
         Stage 3: Spatial Layout Analysis Engine
       (Rows, Columns, Tables, Headers, Label-Value Pairing)
                                │
                                ▼
         Stage 4: Vision-Language Reasoning Layer
  (Triggered on handwriting, low conf <80%, tables, conflicts)
    (Visual OCR correction: "Harshlta" -> "Harshita", Zero Hallucination)
                                │
                                ▼
         Stage 5: 4-Tier Confidence & Schema Normalization
      • 90-100: Verified
      • 70-89: High Confidence
      • 50-69: Needs Review (needs_review = true)
      • < 50: Uncertain (value: null, needs_review = true)
                                │
                                ▼
         Stage 6: SQLite Storage & Human Review UI
   (Crop overlay, raw OCR vs Vision value, editable user feedback)
                                │
                                ▼
         Stage 7: Multi-Table Excel Export
                                │
                                ▼
         Stage 8: Benchmark Accuracy Evaluation
   (OCR-Only vs OCR+Layout vs OCR+Layout+Vision comparison)
```

---

## 2. Detailed Data Flow

1. **Upload & Preprocessing**:
   - Accepts image files (`.png`, `.jpg`, `.jpeg`, `.webp`), PDFs, or direct camera captures.
   - Applies adaptive upscaling and CLAHE contrast enhancement for blurry images.
   - Applies specialized handwriting preprocessing (`preprocess_handwritten_document`) when handwriting is detected.

2. **OCR Token Extraction**:
   - Primary Engine: **Azure AI Document Intelligence** (`prebuilt-read`, `prebuilt-layout`, `prebuilt-invoice`, `prebuilt-idDocument`, `prebuilt-businessCard`).
   - Fallback Engine: Local **PaddleOCR PP-OCRv5** / **EasyOCR**.
   - Output format per token:
     ```json
     {
       "text": "Kanhaiya",
       "bbox": [120, 250, 300, 290],
       "confidence": 0.91,
       "page": 1,
       "line": 3,
       "word": 2
     }
     ```

3. **Spatial Layout Analysis**:
   - Preserves token coordinates `[x1, y1, x2, y2]`.
   - Clusters tokens into spatial rows and vertical columns.
   - Detects form field label-value pairs (nearest left or above label matching value).
   - Extracts table grid structures (rows, columns, headers, empty cells, merged cells).

4. **Vision Reasoning Layer**:
   - Dual-stage triggering: Executes Vision model (`minicpm-v`, `llava`, `qwen2-vl` or Azure Vision) when:
     - Handwriting is detected
     - Overall OCR confidence < 80%
     - Complex table structure is present
     - Required fields are missing or validation rules raise warnings
   - Visually verifies OCR text against image (e.g. corrects `"Harshlta"` → `"Harshita"`).
   - Applies **Zero-Hallucination Policy**: If text is unreadable or ambiguous, sets `value: null` and `needs_review: true`.

---

## 3. Standardized Output JSON Schema

```json
{
  "success": true,
  "document_type": "PAN Card",
  "ocr_engine": "Azure Document Intelligence",
  "has_handwriting": false,
  "vision_reasoning_used": true,
  "fields": {
    "PAN Number": "ABCDE1234F",
    "Cardholder Name": "Harshita Kumar"
  },
  "structured_fields": {
    "Cardholder Name": {
      "value": "Harshita Kumar",
      "raw_text": "Harshlta Kumar",
      "confidence": 92.5,
      "tier": "verified",
      "bbox": [120, 250, 300, 290],
      "page": 1,
      "needs_review": false
    }
  },
  "tables": [
    {
      "table_name": "Invoice Line Items",
      "headers": ["Item Description", "Qty", "Price", "Total"],
      "rows": [
        ["Laptop", "2", "$1,000", "$2,000"]
      ]
    }
  ],
  "validation": {
    "passed_rules": ["PAN Regex PASS", "Verhoeff Checksum PASS"],
    "failed_rules": [],
    "status": "PASS"
  },
  "confidence": 92.5,
  "processing_time": "1.25s"
}
```

---

## 4. 4-Tier Confidence System

| Score Range | Tier Label | System Action | `needs_review` |
| :--- | :--- | :--- | :--- |
| **90 – 100** | `verified` | Automatic approval | `false` |
| **70 – 89** | `high_confidence` | Accepted with standard logging | `false` |
| **50 – 69** | `needs_review` | Highlighted in UI for Human Verification | `true` |
| **Below 50** | `uncertain` | Set `value: null`, flagged for manual entry | `true` |

---

## 5. Human Review Workflow

1. **Detection**: Any extracted field with `confidence < 70` or `needs_review = true` is flagged with a **Review Required** chip in the dashboard.
2. **Review Modal**:
   - The user opens `HumanReviewModal.tsx`.
   - The UI presents the document crop overlay centered on the field bounding box `[x1, y1, x2, y2]`.
   - Displays raw OCR text vs Vision value side-by-side with confidence score.
3. **Correction & Persistence**:
   - The user approves or types corrected text and clicks **Approve & Save Field**.
   - Sends `POST /api/documents/{id}/review` payload:
     ```json
     {
       "field_name": "Cardholder Name",
       "corrected_value": "Harshita Kumar",
       "approved": true
     }
     ```
   - Updates the SQLite database record and updates `processing_status = 'verified'`.

---

## 6. Multi-Table Excel Export

- The Excel Export module (`excel_service.py`) generates a multi-sheet spreadsheet:
  - Sheet 1 (`Extracted Documents`): Standardized 15-column document record table.
  - Sheet 2 (`Extracted Tables`): Structure-preserved multi-table sheet with headers, document filename, table names, and row/column cell mappings.
