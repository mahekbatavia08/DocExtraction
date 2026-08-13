"""
openrouter_service.py
─────────────────────
10-Model OpenRouter Vision Fallback Queue for Doctor Prescription OCR.

Architecture:
  PaddleOCR (text + bounding boxes)
  +
  Vision LLM Queue (10 models, automatic fallback)
  +
  Prescription Validator (safety checks, confidence scoring)

Each model gets up to PRESCRIPTION_MAX_RETRIES attempts.
On failure/low-confidence the next model is tried automatically.
API key is NEVER sent to the frontend.
"""

import base64
import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

from backend.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    PRESCRIPTION_VISION_MODELS,
    PRESCRIPTION_MODEL_TIMEOUT,
    PRESCRIPTION_MAX_RETRIES,
    PRESCRIPTION_MIN_CONFIDENCE,
    MIN_MEDICINE_CONFIDENCE,
)
from backend.utils.logger import logger

# ── Centralized extraction prompts ───────────────────────────────────────────
PRESCRIPTION_EXTRACTION_PROMPT = """You are a medical document OCR and information extraction system.

Analyze the provided doctor prescription image carefully.

Extract ONLY information that is visibly present in the document.
Do NOT infer, diagnose, autocomplete, or guess any medical information.
Pay special attention to handwritten medicine names, dosage, strength, frequency, duration and instructions.
If handwriting is unclear, preserve the closest visible text and mark needs_review=true.
If a field is not present or cannot be reliably read, return null for that field.

Return ONLY valid JSON matching this exact schema — no text outside the JSON:

{
  "document_type": "doctor_prescription",
  "doctor": {
    "name": null,
    "registration_number": null,
    "specialization": null
  },
  "patient": {
    "name": null,
    "age": null,
    "gender": null
  },
  "prescription_date": null,
  "diagnosis": [],
  "medicines": [
    {
      "name": null,
      "strength": null,
      "dosage": null,
      "frequency": null,
      "duration": null,
      "route": null,
      "instructions": null,
      "confidence": 0.0,
      "needs_review": false
    }
  ],
  "tests": [],
  "general_instructions": [],
  "raw_text": "",
  "overall_confidence": 0.0,
  "needs_manual_review": false,
  "model_used": "",
  "fallback_attempt": 0
}

For every medicine provide a confidence score between 0 and 1.
Never hallucinate medicine names, dosages, frequencies, durations, or diagnoses.
If a medicine name is uncertain, set confidence < 0.7 and needs_review = true.
"""

GENERAL_DOCUMENT_VISION_PROMPT = """You are a state-of-the-art vision document understanding AI system.

Analyze the attached document image carefully. Perform complete visual text extraction, key-value field identification, table parsing, and document classification directly from the image.

STRICT ACCURACY RULES:
1. Extract ONLY text and information that is visibly present in the document.
2. NEVER invent, infer, guess, or hallucinate missing dates, names, ID numbers, amounts, address details, or fields.
3. Pay meticulous attention to handwritten notes, fine print, table cells, stamps, headers, logos, and form fields.
4. If a field or text is blurry or uncertain, extract the best readable portion and mark needs_review = true.
5. Return ONLY a valid JSON object matching this exact schema:

{
  "document_type": "<PAN Card / Aadhaar Card / Driving License / Passport / Business Card / Invoice / Receipt / Doctor Prescription / General Document>",
  "overall_confidence": 0.95,
  "needs_manual_review": false,
  "raw_text": "<Full raw text transcribed accurately from top-to-bottom>",
  "fields": {
    "<FieldName1>": "<Extracted Value 1>",
    "<FieldName2>": "<Extracted Value 2>"
  },
  "tables": [
    {
      "table_name": "<Table Header or Section Name>",
      "headers": ["<Col1>", "<Col2>"],
      "rows": [["<Cell1>", "<Cell2>"]]
    }
  ],
  "doctor": {
    "name": null,
    "registration_number": null,
    "specialization": null
  },
  "patient": {
    "name": null,
    "age": null,
    "gender": null
  },
  "medicines": []
}

Ensure all extracted key-value pairs are stored in the "fields" dict (e.g. {"Name": "John Doe", "PAN Number": "ABCDE1234F", "Total Amount": "150.00"}).
For medical prescriptions, also populate the "doctor", "patient", and "medicines" objects appropriately.
"""


def _encode_image_b64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string for OpenRouter vision API."""
    return base64.b64encode(image_bytes).decode("utf-8")


def _build_openrouter_payload(model: str, image_b64: str, ocr_text: str = "", prompt: str = GENERAL_DOCUMENT_VISION_PROMPT) -> dict:
    """Build the OpenRouter chat completion payload with vision + optional OCR context."""
    combined_prompt = prompt
    if ocr_text:
        combined_prompt += f"\n\nAdditional OCR text extracted (use as supporting reference):\n{ocr_text[:3000]}"

    return {
        "model": model,
        "max_tokens": 2048,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}",
                            "detail": "high"
                        }
                    },
                    {
                        "type": "text",
                        "text": combined_prompt
                    }
                ]
            }
        ]
    }


def _call_openrouter(model: str, payload: dict, timeout: float) -> Tuple[Optional[str], Optional[str]]:
    """
    Make a single HTTP call to OpenRouter.
    Returns (response_text, error_type).
    error_type is None on success.
    """
    if not OPENROUTER_API_KEY:
        return None, "no_api_key"

    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "PrescriptionOCR"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
            return content, None

    except urllib.error.HTTPError as e:
        code = e.code
        if code == 400:
            return None, "http_400"
        elif code == 401:
            return None, "http_401_unauthorized"
        elif code == 403:
            return None, "http_403_forbidden"
        elif code == 408:
            return None, "http_408_timeout"
        elif code == 429:
            return None, "http_429_rate_limit"
        elif code in (500, 502, 503):
            return None, f"http_{code}_server_error"
        return None, f"http_{code}"
    except TimeoutError:
        return None, "timeout"
    except Exception as ex:
        return None, f"error_{str(ex)[:40]}"


def _extract_json_from_text(text: str) -> Optional[dict]:
    """Extract JSON object from model response, handling markdown code fences."""
    if not text:
        return None
    # Remove markdown code fences
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        stripped = "\n".join(lines).strip()
    # Find first { ... }
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(stripped[start:end+1])
    except json.JSONDecodeError:
        return None


class OpenRouterPrescriptionService:
    """
    10-Model OpenRouter Vision Fallback Queue.

    Usage:
        result, logs = openrouter_service.extract_prescription(
            image_bytes=img_bytes,
            ocr_text=paddle_text,
            filename="prescription.jpg"
        )
    """

    def __init__(self):
        self.models = PRESCRIPTION_VISION_MODELS
        self.timeout = PRESCRIPTION_MODEL_TIMEOUT
        self.max_retries = PRESCRIPTION_MAX_RETRIES
        self.min_confidence = PRESCRIPTION_MIN_CONFIDENCE
        self.min_medicine_conf = MIN_MEDICINE_CONFIDENCE

    def _validate_result(self, result: dict) -> Tuple[bool, str]:
        """
        Validates extracted prescription JSON.
        Returns (is_valid, rejection_reason).
        """
        # Schema check
        if not isinstance(result, dict):
            return False, "not_dict"
        if result.get("document_type") != "doctor_prescription":
            # Accept anyway if medicines present
            pass

        # Raw text presence
        raw_text = result.get("raw_text", "")
        medicines = result.get("medicines", [])

        # Accept if overall confidence meets threshold
        overall = float(result.get("overall_confidence", 0.0))
        if overall < self.min_confidence and len(medicines) == 0:
            return False, f"low_confidence_{overall:.2f}_no_medicines"

        # Reject if medicines list exists but all have null names
        if medicines:
            named = [m for m in medicines if m.get("name") is not None]
            if len(named) == 0:
                return False, "all_medicine_names_null"

            # Check medicine confidence
            conf_vals = [float(m.get("confidence", 0)) for m in named]
            avg_med_conf = sum(conf_vals) / len(conf_vals) if conf_vals else 0
            if avg_med_conf < self.min_medicine_conf and len(named) == 1:
                return False, f"medicine_confidence_too_low_{avg_med_conf:.2f}"

        return True, "ok"

    def extract_prescription(
        self,
        image_bytes: bytes,
        ocr_text: str = "",
        filename: str = "prescription.jpg"
    ) -> Tuple[Optional[dict], List[dict]]:
        """
        Runs 10-model fallback queue.

        Returns:
            result: Validated prescription JSON dict (or None if all models failed)
            logs: List of per-attempt log entries
        """
        if not OPENROUTER_API_KEY:
            logger.log_step("OpenRouter", "API key not configured — skipping vision model queue.")
            return None, [{"model": "none", "status": "skipped", "error_type": "no_api_key"}]

        image_b64 = _encode_image_b64(image_bytes)
        all_logs: List[dict] = []
        best_low_conf_result = None
        best_low_conf_score = 0.0

        for attempt_idx, model in enumerate(self.models, start=1):
            for retry in range(1, self.max_retries + 2):  # 1 initial + max_retries
                log_entry: Dict[str, Any] = {
                    "model": model,
                    "attempt": attempt_idx,
                    "retry": retry,
                    "status": "pending",
                    "api_time_ms": 0,
                    "fallback_used": attempt_idx > 1
                }
                t_start = time.time()

                logger.log_step("OpenRouter Attempt", f"Model {attempt_idx}/{len(self.models)}: {model} (retry {retry})")

                payload = _build_openrouter_payload(model, image_b64, ocr_text)
                response_text, error_type = _call_openrouter(model, payload, self.timeout)

                elapsed_ms = round((time.time() - t_start) * 1000)
                log_entry["api_time_ms"] = elapsed_ms

                if error_type:
                    log_entry["status"] = "failed"
                    log_entry["error_type"] = error_type
                    log_entry["fallback_to_next"] = True
                    all_logs.append(log_entry)
                    logger.log_step("OpenRouter Failure", f"{model} -> {error_type} ({elapsed_ms}ms)")

                    # Rate limit: skip retries, go to next model immediately
                    if error_type in ("http_429_rate_limit", "http_401_unauthorized", "http_403_forbidden", "no_api_key"):
                        break

                    # Auth/config errors: stop queue entirely
                    if error_type == "http_401_unauthorized":
                        return None, all_logs

                    # On other errors, retry once then move on
                    continue

                # Parse JSON
                parsed = _extract_json_from_text(response_text)
                if not parsed:
                    log_entry["status"] = "invalid_json"
                    log_entry["error_type"] = "malformed_json"
                    log_entry["fallback_to_next"] = True
                    all_logs.append(log_entry)
                    logger.log_step("OpenRouter", f"{model} -> Invalid JSON response")
                    continue

                # Inject metadata
                parsed["model_used"] = model
                parsed["fallback_attempt"] = attempt_idx

                # Validate quality
                is_valid, reason = self._validate_result(parsed)
                overall_conf = float(parsed.get("overall_confidence", 0.0))
                med_count = len([m for m in parsed.get("medicines", []) if m.get("name")])

                log_entry.update({
                    "status": "success" if is_valid else "low_quality",
                    "overall_confidence": overall_conf,
                    "medicine_count": med_count,
                    "validation_reason": reason
                })
                all_logs.append(log_entry)

                if is_valid:
                    logger.log_step("OpenRouter Success", f"{model} -> confidence={overall_conf:.2f} medicines={med_count}")
                    return parsed, all_logs

                # Store best low-confidence result as emergency fallback
                if overall_conf > best_low_conf_score:
                    best_low_conf_score = overall_conf
                    best_low_conf_result = parsed

                logger.log_step("OpenRouter Fallback", f"{model} -> {reason} (conf={overall_conf:.2f}) -> trying next model")
                break  # Move to next model (don't retry on quality fail)

        # All models exhausted — return best available or None
        if best_low_conf_result:
            best_low_conf_result["needs_manual_review"] = True
            logger.log_step("OpenRouter", f"All models exhausted. Returning best result (conf={best_low_conf_score:.2f})")
            return best_low_conf_result, all_logs

        logger.log_step("OpenRouter", "All 10 models failed — manual review required")
        return None, all_logs

    def extract_document_vision(
        self,
        image_bytes: bytes,
        ocr_text: str = "",
        filename: str = "document.jpg"
    ) -> Tuple[Optional[dict], List[dict]]:
        """
        Executes the 10-Model OpenRouter Vision Fallback Queue directly on document image.
        Used in Vision-First mode.
        """
        if not OPENROUTER_API_KEY:
            logger.log_step("OpenRouter Vision", "API key not configured — skipping 10-model vision queue.")
            return None, [{"model": "none", "status": "skipped", "error_type": "no_api_key"}]

        image_b64 = _encode_image_b64(image_bytes)
        all_logs: List[dict] = []
        best_result = None
        best_score = 0.0

        for attempt_idx, model in enumerate(self.models, start=1):
            log_entry: Dict[str, Any] = {
                "model": model,
                "attempt": attempt_idx,
                "status": "pending",
                "api_time_ms": 0,
                "fallback_used": attempt_idx > 1
            }
            t_start = time.time()

            logger.log_step("OpenRouter Vision-First Attempt", f"Model {attempt_idx}/{len(self.models)}: {model}")

            payload = _build_openrouter_payload(model, image_b64, ocr_text, prompt=GENERAL_DOCUMENT_VISION_PROMPT)
            response_text, error_type = _call_openrouter(model, payload, self.timeout)

            elapsed_ms = round((time.time() - t_start) * 1000)
            log_entry["api_time_ms"] = elapsed_ms

            if error_type:
                log_entry["status"] = "failed"
                log_entry["error_type"] = error_type
                all_logs.append(log_entry)
                logger.log_step("OpenRouter Vision Failure", f"{model} -> {error_type} ({elapsed_ms}ms)")

                if error_type == "http_401_unauthorized":
                    return None, all_logs
                continue

            parsed = _extract_json_from_text(response_text)
            if not parsed or not isinstance(parsed, dict):
                log_entry["status"] = "invalid_json"
                all_logs.append(log_entry)
                logger.log_step("OpenRouter Vision", f"{model} -> Invalid JSON response")
                continue

            parsed["model_used"] = model
            parsed["fallback_attempt"] = attempt_idx

            fields = parsed.get("fields", {})
            raw_text = parsed.get("raw_text", "")
            doc_type = parsed.get("document_type", "General Document")
            conf = float(parsed.get("overall_confidence", 0.85))

            if conf > 1.0:
                conf = conf / 100.0 if conf > 1.0 else conf

            log_entry.update({
                "status": "success",
                "overall_confidence": conf,
                "fields_count": len(fields),
                "document_type": doc_type
            })
            all_logs.append(log_entry)

            if len(fields) > 0 or len(raw_text.strip()) > 10 or conf >= 0.65:
                logger.log_step("OpenRouter Vision Success", f"Model {model} extracted {len(fields)} fields directly from image (conf={conf:.2f})")
                return parsed, all_logs

            if conf > best_score:
                best_score = conf
                best_result = parsed

        if best_result:
            return best_result, all_logs

        return None, all_logs


openrouter_service = OpenRouterPrescriptionService()

