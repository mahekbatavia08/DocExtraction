# NVIDIA AI Doctor Prescription OCR & Extraction Integration

## Architecture Overview

This module provides an enterprise-grade Doctor Prescription OCR and Structured Information Extraction pipeline powered by **NVIDIA NIM API Services** (Nemotron OCR v2 & Nemotron Nano Vision LLMs).

```text
Doctor Prescription Image / PDF
              ↓
   Image Preprocessing & Quality Check
              ↓
    NVIDIA Nemotron OCR v2 (Primary OCR)
              ↓
        OCR Text & Layout
              ↓
 NVIDIA Nemotron Nano 12B v2 VL (Primary Vision LLM)
              ↓
 Medical Information Extraction & Zero-Hallucination
              ↓
  Medical NER & Entity Classification Layer
              ↓
Validation & Confidence Scoring (< 65% triggers review)
              ↓
    ├── Pass (Confidence >= 65%) → Return Structured JSON
    │
    └── Fallback Triggered (Failure / Low Quality / Timeout)
              ↓
 NVIDIA Llama 3.1 Nemotron Nano VL 8B (Fallback Vision LLM)
              ↓
    └── Secondary Fallback → Local PaddleOCR + CRNN / NER Engine
```

---

## 1. NVIDIA AI Models Used

* **Primary OCR Model**: `nvidia/nemotron-ocr-v2` (NVIDIA Nemotron OCR v2 for high-precision text recognition & spatial layout bounding boxes)
* **Primary Vision-Language Model**: `nvidia/nemotron-nano-12b-v2-vl` (NVIDIA Nemotron Nano 12B v2 VL for vision-language document reasoning)
* **Fallback Vision Model**: `nvidia/llama-3.1-nemotron-nano-vl-8b` (NVIDIA Llama 3.1 Nemotron Nano VL 8B for secondary fallback execution)

---

## 2. API & Environment Configuration

Configure the backend `.env` file (the key is **never** sent to or exposed in the frontend):

```env
NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_OCR_MODEL=nvidia/nemotron-ocr-v2
NVIDIA_PRIMARY_VISION_MODEL=nvidia/nemotron-nano-12b-v2-vl
NVIDIA_FALLBACK_VISION_MODEL=nvidia/llama-3.1-nemotron-nano-vl-8b
MAX_MODEL_RETRIES=1
MODEL_TIMEOUT_SECONDS=45
PRESCRIPTION_MIN_CONFIDENCE=0.65
MEDICINE_MIN_CONFIDENCE=0.65
```

---

## 3. Required JSON Schema

```json
{
  "document_type": "doctor_prescription",
  "doctor": {
    "name": "Dr. Sarah Jenkins",
    "registration_number": "BMDC-99123",
    "specialization": "Cardiologist"
  },
  "patient": {
    "name": "John Doe",
    "age": "45",
    "gender": "Male"
  },
  "prescription_date": "2026-08-13",
  "diagnosis": ["Hypertension", "Type 2 Diabetes"],
  "medicines": [
    {
      "name": "Paracetamol",
      "strength": "500 mg",
      "dosage": "1 tablet",
      "frequency": "1-0-1",
      "duration": "5 days",
      "route": "oral",
      "instructions": "After meals",
      "confidence": 0.95,
      "needs_review": false
    }
  ],
  "tests": ["HbA1c", "Lipid Profile"],
  "general_instructions": ["Rest for 3 days", "Drink plenty of water"],
  "raw_text": "...",
  "overall_confidence": 0.95,
  "needs_manual_review": false,
  "ocr_model": "nvidia/nemotron-ocr-v2",
  "vision_model": "nvidia/nemotron-nano-12b-v2-vl",
  "processing_time_ms": 3421
}
```

---

## 4. Medical NER & Entity Classification Layer

Implemented in [medical_ner.py](file:///d:/PaddleOCR-main/PaddleOCR-main/backend/services/medical_ner.py), this layer categorizes extracted tokens into:
* `DOCTOR`, `PATIENT`, `MEDICINE`, `STRENGTH`, `DOSAGE`, `FREQUENCY`, `DURATION`, `ROUTE`, `DIAGNOSIS`, `TEST`, `INSTRUCTION`, `DATE`.

**Zero-Hallucination Policy**: If a handwritten medicine name is unclear (e.g. `Amoxi...`), it is never guessed or hallucinated as `Amoxicillin`. It is extracted as `Amoxi...` with `confidence < 0.65` and `needs_review = true`.

---

## 5. API Endpoints

* **POST `/api/prescription/extract`**: Upload multipart file (`image/jpeg`, `image/png`, `application/pdf`). Returns normalized prescription extraction data with NVIDIA AI model processing metadata.
* **GET `/api/nvidia/health`**: Health check verifying backend NVIDIA API key status (`nvidia_configured`, `api_reachable`, `ocr_model_available`, `vision_model_available`) without exposing secrets.
