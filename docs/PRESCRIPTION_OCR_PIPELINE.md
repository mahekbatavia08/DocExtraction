# Doctor Prescription OCR Pipeline (10-Model OpenRouter Fallback System)

This document describes the architecture, configuration, fallback queue, JSON schema, and validation rules for the Doctor Prescription Extraction Engine.

---

## 1. Pipeline Architecture

```
         USER UPLOAD (Image / PDF)
                    │
                    ▼
          Validation & Preprocessing
         (Format check, 2x CLAHE, Upscale)
                    │
                    ▼
         EasyOCR / PaddleOCR Layer
       (Extracted Text + Bounding Boxes)
                    │
                    ▼
 ┌──────────────────────────────────────────────┐
 │       OpenRouter 10-Vision Model Queue        │
 ├──────────────────────────────────────────────┤
 │  1. NVIDIA Nemotron-4 340B Instruct (:free)   │
 │  2. Qwen2.5-VL 72B Instruct (:free)           │
 │  3. Gemma 3 27B IT (:free)                    │
 │  4. Gemma 3 4B IT (:free)                     │
 │  5. Mistral Small 24B Instruct (:free)        │
 │  6. Qwen2.5-VL 7B Instruct (:free)            │
 │  7. Kimi VL A3B Thinking (:free)              │
 │  8. Gemma 3 27B (:free)                       │
 │  9. Llama 3.2 11B Vision Instruct (:free)     │
 │ 10. Llama 3.2 90B Vision Instruct             │
 └──────────────────────┬───────────────────────┘
                        │
                        ▼
           Medical Output Validation
        (Schema, Confidence, Hallucination)
                        │
       ┌────────────────┴────────────────┐
       ▼                                 ▼
   PASS (Grade: High/Med)          FAIL / LOW CONF
       │                                 │
       ▼                                 ▼
 Return Structured JSON          Try Next Model in Queue
                                         │
                                         ▼
                               (If all 10 fail)
                                         │
                                         ▼
                              Local CRNN + NER Engine
                             (needs_manual_review=true)
```

---

## 2. Configuration (`backend/config.py` & `.env`)

The OpenRouter fallback queue is configured via environment variables:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
PRESCRIPTION_MODEL_TIMEOUT=45
PRESCRIPTION_MAX_RETRIES=1
PRESCRIPTION_MIN_CONFIDENCE=0.65
MIN_MEDICINE_CONFIDENCE=0.65
```

### Model Queue Configuration:

```python
PRESCRIPTION_VISION_MODELS = [
    "nvidia/nemotron-4-340b-instruct:free",
    "qwen/qwen-2.5-vl-72b-instruct:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-3-4b-it:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
    "qwen/qwen-2.5-vl-7b-instruct:free",
    "moonshotai/kimi-vl-a3b-thinking:free",
    "google/gemma-3-27b:free",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "meta-llama/llama-3.2-90b-vision-instruct"
]
```

---

## 3. Standard Prescription JSON Schema

Every successful vision model returns this exact JSON structure:

```json
{
  "document_type": "doctor_prescription",
  "doctor": {
    "name": "Dr. Rahim Ahmed",
    "registration_number": "BMDC Reg No: 74512",
    "specialization": "MBBS, FCPS"
  },
  "patient": {
    "name": "Kanhaiya Kumar",
    "age": "34Y",
    "gender": "Male"
  },
  "prescription_date": "12/08/2026",
  "diagnosis": [
    "Acute Upper Respiratory Tract Infection"
  ],
  "medicines": [
    {
      "name": "Azipen",
      "strength": "500mg",
      "dosage": "1+0+0",
      "frequency": "1+0+0",
      "duration": "5 Days",
      "route": "oral",
      "instructions": "After Food",
      "confidence": 0.95,
      "needs_review": false
    }
  ],
  "tests": [],
  "general_instructions": [],
  "raw_text": "...",
  "overall_confidence": 0.92,
  "needs_manual_review": false,
  "model_used": "nvidia/nemotron-4-340b-instruct:free",
  "fallback_attempt": 1
}
```

---

## 4. Critical Medical Safety & Non-Hallucination Rules

1. **Never Invent Data**: If a field is not visibly present in the image, return `null`.
2. **Uncertain Text**: If handwriting is unreadable or confidence < 0.65, return closest visible text with `needs_review: true`.
3. **Manual Review Trigger**: Set `needs_manual_review: true` if `overall_confidence < 0.65` or any medicine has `needs_review: true`.
4. **No Direct Frontend API Calls**: All OpenRouter requests pass through `POST /api/prescription/extract` on the backend. The API key is never exposed to the client.

---

## 5. API Endpoint Reference

### `POST /api/prescription/extract`

- **Content-Type**: `multipart/form-data`
- **Body**: `file` (image or PDF page)
- **Response**:
```json
{
  "success": true,
  "needs_manual_review": false,
  "data": { ... },
  "processing": {
    "model_used": "nvidia/nemotron-4-340b-instruct:free",
    "fallback_attempt": 1,
    "fallback_used": false,
    "used_openrouter": true,
    "quality_grade": "high",
    "ocr_time_ms": 120,
    "total_time_ms": 1450,
    "attempt_logs": [ ... ]
  }
}
```

---

## 6. How to Change or Add Models

1. Open `backend/config.py`.
2. Add or reorder model identifiers in `PRESCRIPTION_VISION_MODELS`.
3. Restart backend service.
