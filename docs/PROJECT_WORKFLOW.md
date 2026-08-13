# Document Extraction & Vision Reasoning Workflow

This document illustrates the end-to-end processing pipeline for all document types (Prescriptions, ID Cards, Business Cards, Invoices) handled by the application.

---

## 1. Doctor Prescription NVIDIA AI Processing Flow

```text
Upload
 ↓
Preprocessing
 ↓
Nemotron OCR v2
 ↓
OCR validation
 ↓
Nemotron Nano 12B VL
 ↓
Medical NER
 ↓
Validation
 ↓
Confidence
 ↓
Fallback if required (NVIDIA Llama Nemotron Nano VL 8B / Local Engine)
 ↓
Structured JSON
 ↓
Frontend
```

---

## 2. Complete Processing Stage Breakdown

| Stage | Component | Description / Model | Output |
|---|---|---|---|
| 1. Upload | `POST /api/prescription/extract` | Validates MIME type, size limit (20MB), multi-page PDF conversion | Image Buffer |
| 2. Preprocess | `preprocess_document_image` | Low-res detection, CLAHE contrast, orientation check | Enhanced Image |
| 3. Primary OCR | `nvidia_service.run_nemotron_ocr` | **NVIDIA Nemotron OCR v2** (`nvidia/nemotron-ocr-v2`) | Raw OCR Text & Bounding Boxes |
| 4. Vision Reasoning | `nvidia_service.query_vision_llm` | **NVIDIA Nemotron Nano 12B v2 VL** (`nvidia/nemotron-nano-12b-v2-vl`) | Structured Prescription JSON |
| 5. Medical NER | `medical_ner.process_entities` | Entity Classification & Dosage/Frequency Normalization | Normalized Medicines List |
| 6. Validation | `prescription_validator.validate_prescription_result` | Verifies confidence >= 0.65 threshold & schema integrity | Quality Grade: High/Medium/Low |
| 7. Fallback | `nvidia_service.extract_prescription_nvidia` | **NVIDIA Llama 3.1 Nemotron Nano VL 8B** (`nvidia/llama-3.1-nemotron-nano-vl-8b`) | Fallback Extraction (if Primary fails) |
| 8. Standard Output | FastAPI API Response | Formatted JSON Schema response for Frontend UI | Standardized Response |

