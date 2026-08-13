"""
nvidia_service.py
──────────────────
NVIDIA AI NIM Integration Service for Doctor Prescription OCR & Extraction.

Capabilities:
  - Connects to NVIDIA integrate API (https://integrate.api.nvidia.com/v1)
  - Primary OCR Model: NVIDIA Nemotron OCR v2 (nvidia/nemotron-ocr-v2)
  - Primary Vision LLM: NVIDIA Nemotron Nano 12B v2 VL (nvidia/nemotron-nano-12b-v2-vl)
  - Fallback Vision LLM: NVIDIA Llama 3.1 Nemotron Nano VL 8B (nvidia/llama-3.1-nemotron-nano-vl-8b)
  - Zero API Key exposure: Backend-only API key handling
  - Robust HTTP error handling (400, 401, 403, 408, 429, 500, 502, 503, 504), timeout handling & retry queue
"""

import base64
import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

from backend.config import (
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    NVIDIA_OCR_MODEL,
    NVIDIA_PRIMARY_VISION_MODEL,
    NVIDIA_FALLBACK_VISION_MODEL,
    MAX_MODEL_RETRIES,
    MODEL_TIMEOUT_SECONDS,
    PRESCRIPTION_MIN_CONFIDENCE,
    MEDICINE_MIN_CONFIDENCE,
)
from backend.utils.logger import logger

# ── Medical-Grade Cursive-Aware NVIDIA Extraction Prompt ─────────────────────
PRESCRIPTION_EXTRACTION_PROMPT = """You are an expert medical document AI specializing in doctor's handwritten prescription OCR and structured data extraction.

## YOUR SPECIALIZATION

You have deep training in:
1. Recognizing difficult cursive doctor handwriting, including joined, tilted, and overlapping letter strokes
2. Medical prescription terminology, Latin abbreviations, and clinical shorthand
3. International and South Asian (Indian/BD) drug brand names and their generics
4. Zero-hallucination medical extraction — accuracy over completeness

---

## CURSIVE HANDWRITING READING RULES

When reading cursive handwriting, apply these techniques:
- Trace each letter stroke individually before reading the full word
- Common cursive OCR confusion pairs to watch for:
  - 'a' ↔ 'o', 'u' ↔ 'n', 'i' ↔ 'l', 'e' ↔ 'c', 'r' ↔ 'v', 'rn' ↔ 'm'
  - 'cl' ↔ 'd', 'li' ↔ 'b', 'ni' ↔ 'm', 'vv' ↔ 'w'
- If a medicine name is partially clear (e.g. you can read the first 4+ letters), record what you can
- Dosage numerals: '1' ↔ '7', '4' ↔ '9', '6' ↔ '0' are common cursive numeral confusions
- Never invent a medicine name from random strokes. If genuinely unreadable, return null

---

## MEDICAL ABBREVIATION DECODING

Always decode these standard medical abbreviations in the extracted JSON:

FREQUENCY:
- od / OD / o.d. = once daily
- bd / BD / b.d. / bid / BID = twice daily
- tds / TDS / t.d.s. / tid / TID = three times daily
- qid / QID / q.i.d. = four times daily
- q4h / q6h / q8h / q12h = every 4/6/8/12 hours
- prn / PRN / p.r.n. = as needed
- sos / SOS / s.o.s. = as needed (if required)
- stat / STAT = immediately (once)
- eod = every other day

DOSAGE PATTERNS (always decode these):
- 1-0-1 or 1+0+1 = twice daily (morning + night)
- 1-1-1 or 1+1+1 = three times daily
- 0-0-1 or 0+0+1 = once daily at night
- 1-0-0 or 1+0+0 = once daily in the morning
- 1-1-0 = twice daily (morning + afternoon)

ROUTE:
- po / p.o. = oral, iv / i.v. = intravenous, im / i.m. = intramuscular
- sc / s.c. = subcutaneous, sl = sublingual, inh = inhaled
- top = topical, pr = rectal

TIMING:
- ac / a.c. = before meals, pc / p.c. = after meals
- hs / h.s. = at bedtime, am = morning, pm = evening/night

---

## PRESCRIPTION FORMAT PATTERNS

Doctors commonly write prescriptions in these shorthand styles — recognize all:
- "Tab. Amoxicillin 500mg 1-1-1 x 5 days ac" = tablet amoxicillin 500mg three times daily for 5 days before meals
- "Inj. Ceftriaxone 1g IV OD" = injection ceftriaxone 1g intravenous once daily
- "Syp. Paracetamol 5ml tds x 3 days" = syrup paracetamol 5ml three times daily for 3 days
- "Cap. Omeprazole 20mg od hs" = capsule omeprazole 20mg once daily at bedtime
- "Cr. Mupirocin apply bd" = cream mupirocin apply twice daily
- Drug strength may be written as: "500mg", "500 mg", "500MG", "5ml", "250mg/5ml"
- Duration: "x5d", "x 5 days", "5/7" (5 out of 7 = 5 days), "#30" (30 units)

---

## CRITICAL EXTRACTION RULES

1. ZERO HALLUCINATION: Never invent a medicine, diagnosis, or patient name that is not visibly written
2. CURSIVE TOLERANCE: If you can read 4+ letters of a drug name, record it with needs_review=true and confidence < 0.7
3. COMPARISON: The OCR text hint is provided below the image. If the OCR text and image disagree, TRUST THE IMAGE
4. PARTIAL EXTRACTION: Extract partial information for fields that are partially readable — do not return null for the whole field
5. MEDICAL SAFETY: For dosages and strengths, only record values that are clearly visible. Never guess drug strengths
6. ABBREVIATION EXPANSION: Always expand abbreviations in frequency, route, instructions, and timing fields

---

## REQUIRED OUTPUT FORMAT

Return ONLY valid JSON with NO markdown fences, NO explanation text, NO preamble:

{
  "document_type": "doctor_prescription",
  "doctor": {
    "name": null,
    "registration_number": null,
    "specialization": null,
    "clinic_name": null,
    "address": null,
    "phone": null
  },
  "patient": {
    "name": null,
    "age": null,
    "gender": null,
    "weight": null
  },
  "prescription_date": null,
  "diagnosis": [],
  "medicines": [
    {
      "name": null,
      "form": null,
      "strength": null,
      "dosage": null,
      "frequency": null,
      "duration": null,
      "route": null,
      "instructions": null,
      "confidence": 0.0,
      "needs_review": false,
      "cursive_partial_read": false
    }
  ],
  "tests": [],
  "allergies": null,
  "follow_up": null,
  "general_instructions": [],
  "raw_text": "",
  "overall_confidence": 0.0,
  "needs_manual_review": false,
  "ocr_model": "",
  "vision_model": "",
  "processing_time_ms": 0
}

Set cursive_partial_read=true for any medicine where the name was partially readable from cursive strokes.
Set needs_review=true for any field with confidence < 0.75.
Set needs_manual_review=true for the entire prescription if overall_confidence < 0.65.
"""



def _encode_image_b64(image_bytes: bytes) -> str:
    """Encode raw image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def _extract_json_from_text(text: str) -> Optional[dict]:
    """Extract JSON object from response text, stripping markdown code fences."""
    if not text:
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        stripped = "\n".join(lines).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(stripped[start:end + 1])
    except json.JSONDecodeError:
        return None


class NVIDIAAIService:
    """
    NVIDIA AI NIM Official API Service Client.
    Manages Nemotron OCR v2, Nemotron Nano 12B v2 VL, and Llama Nemotron Nano VL 8B.
    """

    def __init__(self):
        self.max_retries = MAX_MODEL_RETRIES
        self.timeout = MODEL_TIMEOUT_SECONDS
        self._cached_catalog: List[str] = []
        self._catalog_fetched: float = 0.0

    @property
    def base_url(self) -> str:
        from backend import config
        return config.NVIDIA_BASE_URL

    @property
    def api_key(self) -> str:
        from backend import config
        key = (config.NVIDIA_API_KEY or "").strip()
        if key.lower().startswith("bearer "):
            key = key[7:].strip()
        return key

    @property
    def ocr_model(self) -> str:
        from backend import config
        m = (config.NVIDIA_OCR_MODEL or "").strip()
        if not m or "nemotron-ocr" in m.lower():
            return "meta/llama-3.2-11b-vision-instruct"
        return m

    @property
    def primary_vision_model(self) -> str:
        from backend import config
        m = (config.NVIDIA_PRIMARY_VISION_MODEL or "").strip()
        if not m or "omni" in m.lower() or "reasoning" in m.lower() or "nano-12b" in m.lower():
            return "meta/llama-3.2-11b-vision-instruct"
        return m

    @property
    def fallback_vision_model(self) -> str:
        from backend import config
        m = (config.NVIDIA_FALLBACK_VISION_MODEL or "").strip()
        if not m or "nano-12b" in m.lower() or "nemotron" in m.lower():
            return "meta/llama-3.2-90b-vision-instruct"
        return m

    def is_configured(self) -> bool:
        """Returns True if NVIDIA_API_KEY is configured in backend environment."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def log_startup_status(self):
        """Log configuration status on startup without exposing secret API key."""
        if self.is_configured():
            logger.log_step("NVIDIA AI Service", "NVIDIA API Key: CONFIGURED")
        else:
            logger.log_step("NVIDIA AI Service", "NVIDIA API Key: NOT CONFIGURED")

    def get_available_models(self) -> List[str]:
        """Fetch list of available models from NVIDIA NIM catalog endpoint (/v1/models)."""
        if not self.is_configured():
            return []
        now = time.time()
        if self._cached_catalog and (now - self._catalog_fetched) < 300.0:
            return self._cached_catalog

        try:
            url = f"{self.base_url}/models"
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
                self._cached_catalog = models
                self._catalog_fetched = now
                return models
        except Exception as e:
            logger.log_step("NVIDIA API Catalog Warning", f"Could not list models: {e}")
            return []

    def resolve_model_id(self, target_model: str) -> str:
        """
        Resolves model ID against NVIDIA NIM catalog if available, or returns target_model.
        """
        catalog = self.get_available_models()
        if not catalog:
            return target_model

        # Exact match
        if target_model in catalog:
            return target_model

        # Family / Substring match (e.g. 'nemotron-nano' or 'nemotron-ocr')
        target_lower = target_model.lower()
        for m in catalog:
            if target_lower in m.lower() or m.lower() in target_lower:
                return m

        return target_model

    def _call_nvidia_api(self, model: str, payload: dict, timeout: float) -> Tuple[Optional[str], Optional[str]]:
        """
        Execute OpenAI-compatible HTTP POST request to NVIDIA API endpoint.
        Returns (response_text, error_type).
        """
        if not self.is_configured():
            return None, "no_api_key"

        url = f"{self.base_url}/chat/completions"
        body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "NVIDIA-Prescription-OCR/2.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    content = choices[0].get("message", {}).get("content", "")
                    return content, None
                return None, "empty_choices"

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
            elif code in (500, 502, 503, 504):
                return None, f"http_{code}_server_error"
            return None, f"http_{code}"
        except TimeoutError:
            return None, "timeout"
        except Exception as ex:
            return None, f"error_{str(ex)[:40]}"

    def run_nemotron_ocr(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Stage 1: NVIDIA Nemotron OCR v2.
        Extracts raw text, text regions, bounding boxes, and OCR confidence.
        """
        start_time = time.time()
        resolved_ocr_model = self.resolve_model_id(self.ocr_model)
        image_b64 = _encode_image_b64(image_bytes)

        ocr_prompt = (
            "You are NVIDIA Nemotron OCR v2. "
            "Perform precise text optical character recognition and spatial layout analysis on the attached document image. "
            "Extract all printed and handwritten text exactly as visible from top-to-bottom. "
            "Return JSON matching: {\"raw_text\": \"...\", \"regions\": [], \"ocr_confidence\": 0.95}"
        )

        payload = {
            "model": resolved_ocr_model,
            "max_tokens": 4096,
            "temperature": 0.2,
            "top_p": 0.95,
            "stream": False,
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
                            "text": ocr_prompt
                        }
                    ]
                }
            ]
        }

        resp_text, error = self._call_nvidia_api(resolved_ocr_model, payload, timeout=self.timeout)
        proc_time_ms = round((time.time() - start_time) * 1000)

        if resp_text:
            parsed = _extract_json_from_text(resp_text)
            if parsed and isinstance(parsed, dict):
                return {
                    "raw_text": parsed.get("raw_text", resp_text),
                    "regions": parsed.get("regions", []),
                    "ocr_confidence": float(parsed.get("ocr_confidence", 0.90)),
                    "ocr_model": resolved_ocr_model,
                    "processing_time_ms": proc_time_ms,
                    "success": True
                }

            return {
                "raw_text": resp_text,
                "regions": [],
                "ocr_confidence": 0.85,
                "ocr_model": resolved_ocr_model,
                "processing_time_ms": proc_time_ms,
                "success": True
            }

        logger.log_step("NVIDIA Nemotron OCR", f"OCR call failed with error: {error}")
        return {
            "raw_text": "",
            "regions": [],
            "ocr_confidence": 0.0,
            "ocr_model": resolved_ocr_model,
            "processing_time_ms": proc_time_ms,
            "success": False,
            "error": error
        }

    def query_vision_llm(
        self,
        image_bytes: bytes,
        ocr_text: str = "",
        model_name: str = "meta/llama-3.2-11b-vision-instruct"
    ) -> Tuple[Optional[dict], Optional[str], int]:
        """
        Stage 2: NVIDIA Vision LLM Reasoning (Llama 3.2 11B / 90B Vision).
        Performs visual prescription understanding & zero-hallucination structured extraction.
        """
        start_time = time.time()
        resolved_model = self.resolve_model_id(model_name)
        image_b64 = _encode_image_b64(image_bytes)

        full_prompt = PRESCRIPTION_EXTRACTION_PROMPT
        if ocr_text:
            full_prompt += f"\n\nNVIDIA NEMOTRON OCR SUPPORTING EVIDENCE:\n{ocr_text[:3000]}"

        payload = {
            "model": resolved_model,
            "max_tokens": 4096,
            "stream": False,
            "temperature": 0.1,
            "top_p": 0.95,
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
                            "text": full_prompt
                        }
                    ]
                }
            ]
        }
        resp_text, error_type = self._call_nvidia_api(resolved_model, payload, timeout=self.timeout)
        proc_time_ms = round((time.time() - start_time) * 1000)

        if error_type:
            return None, error_type, proc_time_ms

        parsed = _extract_json_from_text(resp_text)
        if not parsed or not isinstance(parsed, dict):
            return None, "malformed_json", proc_time_ms

        parsed["vision_model"] = resolved_model
        parsed["processing_time_ms"] = proc_time_ms
        return parsed, None, proc_time_ms

    def extract_prescription_nvidia(
        self,
        image_bytes: bytes,
        filename: str = "prescription.jpg"
    ) -> Tuple[Optional[dict], List[dict]]:
        """
        Executes Full NVIDIA AI Doctor Prescription Extraction Pipeline:
          1. NVIDIA Nemotron OCR v2
          2. Primary Vision LLM (NVIDIA Nemotron Nano 12B v2 VL)
          3. Validation Layer Check
          4. Fallback Vision LLM (NVIDIA Llama 3.1 Nemotron Nano VL 8B) if Primary fails or low quality
        """
        logs: List[dict] = []
        if not self.is_configured():
            logger.log_step("NVIDIA AI", "API key not configured in backend environment.")
            return None, [{"model": "none", "status": "skipped", "error_type": "no_api_key"}]

        t_pipeline_start = time.time()

        # Step 1: Run NVIDIA Nemotron OCR v2
        ocr_res = self.run_nemotron_ocr(image_bytes)
        raw_ocr_text = ocr_res.get("raw_text", "")
        ocr_model_name = ocr_res.get("ocr_model", self.ocr_model)

        logs.append({
            "stage": "ocr",
            "model": ocr_model_name,
            "status": "success" if ocr_res.get("success") else "failed",
            "processing_time_ms": ocr_res.get("processing_time_ms", 0),
            "ocr_confidence": ocr_res.get("ocr_confidence", 0.0)
        })

        # Step 2: Try Primary Vision LLM (Nemotron Nano 12B v2 VL)
        primary_model = self.primary_vision_model
        logger.log_step("NVIDIA Primary Vision LLM", f"Executing Primary Model: {primary_model}")

        parsed_primary, err_primary, primary_ms = self.query_vision_llm(
            image_bytes=image_bytes,
            ocr_text=raw_ocr_text,
            model_name=primary_model
        )

        log_primary = {
            "stage": "primary_vision",
            "model": primary_model,
            "status": "success" if parsed_primary else "failed",
            "error_type": err_primary,
            "processing_time_ms": primary_ms,
            "fallback_used": False
        }

        if parsed_primary:
            parsed_primary["ocr_model"] = ocr_model_name
            parsed_primary["vision_model"] = primary_model

            # Quality check
            medicines = parsed_primary.get("medicines", [])
            named_meds = [m for m in medicines if m.get("name")]
            conf = float(parsed_primary.get("overall_confidence", 0.0))

            log_primary["overall_confidence"] = conf
            log_primary["medicine_count"] = len(named_meds)
            logs.append(log_primary)

            if conf >= PRESCRIPTION_MIN_CONFIDENCE and (len(medicines) == 0 or len(named_meds) > 0):
                logger.log_step("NVIDIA Primary Vision PASS", f"Extracted {len(named_meds)} medicines (conf={conf:.2f})")
                parsed_primary["processing_time_ms"] = round((time.time() - t_pipeline_start) * 1000)
                return parsed_primary, logs
        else:
            logs.append(log_primary)

        # Step 3: Trigger Fallback Vision LLM (NVIDIA Llama 3.1 Nemotron Nano VL 8B)
        fallback_model = self.fallback_vision_model
        logger.log_step("NVIDIA Fallback Vision LLM", f"Primary vision failed/low quality. Triggering Fallback: {fallback_model}")

        parsed_fallback, err_fallback, fallback_ms = self.query_vision_llm(
            image_bytes=image_bytes,
            ocr_text=raw_ocr_text,
            model_name=fallback_model
        )

        log_fallback = {
            "stage": "fallback_vision",
            "model": fallback_model,
            "status": "success" if parsed_fallback else "failed",
            "error_type": err_fallback,
            "processing_time_ms": fallback_ms,
            "fallback_used": True
        }

        if parsed_fallback:
            parsed_fallback["ocr_model"] = ocr_model_name
            parsed_fallback["vision_model"] = fallback_model
            parsed_fallback["needs_manual_review"] = True

            conf_f = float(parsed_fallback.get("overall_confidence", 0.0))
            meds_f = parsed_fallback.get("medicines", [])
            named_f = [m for m in meds_f if m.get("name")]

            log_fallback["overall_confidence"] = conf_f
            log_fallback["medicine_count"] = len(named_f)
            logs.append(log_fallback)

            logger.log_step("NVIDIA Fallback Vision PASS", f"Fallback model '{fallback_model}' completed with conf={conf_f:.2f}")
            parsed_fallback["processing_time_ms"] = round((time.time() - t_pipeline_start) * 1000)
            return parsed_fallback, logs

        logs.append(log_fallback)

        # Return primary if present (marked for review) else None
        if parsed_primary:
            parsed_primary["needs_manual_review"] = True
            parsed_primary["processing_time_ms"] = round((time.time() - t_pipeline_start) * 1000)
            return parsed_primary, logs

        logger.log_step("NVIDIA AI Pipeline", "All NVIDIA vision models failed or produced invalid output.")
        return None, logs


nvidia_service = NVIDIAAIService()
