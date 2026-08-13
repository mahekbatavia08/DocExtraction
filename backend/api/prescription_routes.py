"""
prescription_routes.py
───────────────────────
FastAPI router exposing:
  POST /api/prescription/extract

Runtime-selectable pipeline (via PIPELINE_MODE env var):
  'prescription' (default) → Unified 7-stage PrescriptionPipeline:
      Preprocessing → Classify → PaddleOCR/NVIDIA-HTR → Merge
      → NVIDIA VLM → Medical NER → Validation → Final JSON
  'legacy'                 → Original OpenRouter 10-model fallback queue

API key is NEVER exposed to the frontend.
"""

import io
import time
import numpy as np
import cv2
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException

from backend.services.openrouter_service import openrouter_service
from backend.services.prescription_validator import (
    normalize_prescription,
    validate_prescription_result,
    build_local_fallback,
)
from backend.services.medical_prescription_extractor import medical_prescription_extractor
from backend.services.ocr_service import ocr_service
from backend.utils.image_processing import (
    decode_image_bytes,
    render_pdf_to_images,
    preprocess_document_image,
    preprocess_prescription_image,
    encode_image_to_base64,
)
from backend.services.medical_abbreviations import medical_abbreviation_expander
from backend.utils.logger import logger
from backend.config import OPENROUTER_API_KEY, PIPELINE_MODE
from backend.services.prescription_pipeline import run_prescription_pipeline

router = APIRouter(prefix="/api/prescription", tags=["Prescription OCR"])


def _image_to_jpeg_bytes(img: np.ndarray, max_dim: int = 2048) -> bytes:
    """Resize if needed and encode image to JPEG bytes for vision model."""
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return buf.tobytes()


@router.post("/extract")
async def extract_prescription(file: UploadFile = File(...)):
    """
    POST /api/prescription/extract

    Accepts: image (JPG/PNG/WEBP/BMP) or PDF
    Returns: Structured prescription JSON with model metadata.

    Pipeline (controlled by PIPELINE_MODE env var):
      'prescription' → Unified 7-stage PrescriptionPipeline (default)
      'legacy'       → Original OpenRouter 10-model fallback queue
    """
    t_start = time.time()

    # ── 1. Validate file type ────────────────────────────────────────────────
    filename = file.filename or "prescription"
    content_type = (file.content_type or "").lower()
    fname_lower = filename.lower()

    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp",
                     "image/tiff", "application/pdf"}
    ALLOWED_EXT = (".jpg", ".jpeg", ".png", ".pdf", ".webp", ".bmp", ".tiff")

    if content_type not in ALLOWED_TYPES and not any(fname_lower.endswith(e) for e in ALLOWED_EXT):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

    contents = await file.read()
    if len(contents) < 100:
        raise HTTPException(status_code=400, detail="File too small — likely empty or corrupt")
    if len(contents) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=400, detail="File too large (max 20 MB)")

    # ── NEW PIPELINE: Delegate to unified 7-stage PrescriptionPipeline ────────
    if PIPELINE_MODE == "prescription":
        logger.log_step("Prescription Extract",
                        f"PIPELINE_MODE=prescription -> delegating to unified pipeline ({filename})")
        try:
            result = run_prescription_pipeline(image_bytes=contents, filename=filename)
        except Exception as exc:
            logger.log_step("Prescription Pipeline Error", str(exc))
            raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

        if not result.get("success"):
            raise HTTPException(
                status_code=422,
                detail=result.get("error", "Prescription pipeline failed")
            )

        prescription = result.get("prescription") or {}
        validation = result.get("validation", {})
        meta = result.get("metadata", {})
        stages = result.get("pipeline_stages", {})

        return {
            "success": True,
            "needs_manual_review": prescription.get("needs_manual_review", False),
            "has_handwriting": result.get("has_handwriting", False),
            "data": prescription,
            "ner_entities": result.get("ner_entities", {}),
            "processing": {
                "ocr_model": stages.get("ocr_printed", "paddleocr"),
                "htr_model": stages.get("ocr_handwritten", "skipped"),
                "vision_model": stages.get("vlm_reasoning", "none"),
                "model_used": stages.get("vlm_reasoning", "none"),
                "pipeline_mode": "prescription",
                "quality_grade": validation.get("grade", "unknown"),
                "validation_issues": validation.get("issues", []),
                "total_time_ms": meta.get("processing_time_ms", 0),
                "medicine_count": len([
                    m for m in prescription.get("medicines", []) if m.get("name")
                ]),
                "overall_confidence": prescription.get("overall_confidence", 0.0),
                "audit_trail": meta.get("audit_trail", []),
                "vlm_logs": meta.get("vlm_logs", []),
            }
        }

    # ── LEGACY PIPELINE: Original OpenRouter / NVIDIA direct flow ─────────────
    logger.log_step("Prescription Extract",
                    f"PIPELINE_MODE=legacy -> using original OpenRouter pipeline ({filename})")

    # ── 2. Decode image ───────────────────────────────────────────────────────
    try:
        if fname_lower.endswith(".pdf") or content_type == "application/pdf":
            from backend.utils.image_processing import extract_digital_pdf_text
            digital_text = extract_digital_pdf_text(contents)
            pages = render_pdf_to_images(contents)
            if not pages:
                raise ValueError("No readable pages in PDF")
            img = pages[0]
            logger.log_step("Prescription Extract", f"PDF -> image, digital_text={len(digital_text)} chars")
        else:
            img = decode_image_bytes(contents)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Cannot decode image: {e}")

    # ── 3. Preprocess — use cursive-optimized pipeline for prescriptions ────────
    preprocessed = preprocess_prescription_image(img, upscale_factor=2.5)
    img_bytes = _image_to_jpeg_bytes(preprocessed)
    logger.log_step("Prescription Extract", f"Cursive-Preprocessed: {preprocessed.shape[1]}x{preprocessed.shape[0]}")

    # ── 4. Try Primary Engine: NVIDIA AI NIM Service (Nemotron OCR v2 + Nemotron Nano 12B VL) ──
    from backend.services.nvidia_service import nvidia_service
    from backend.services.medical_ner import medical_ner

    nvidia_result = None
    attempt_logs = []
    used_nvidia = False

    if nvidia_service.is_configured():
        logger.log_step("Prescription Extract", "Executing Primary Engine: NVIDIA AI Services (Nemotron OCR v2 + Nemotron Nano 12B VL)...")
        nvidia_result, attempt_logs = nvidia_service.extract_prescription_nvidia(img_bytes, filename=filename)
        if nvidia_result:
            used_nvidia = True

    # ── 5. Fallback Engine: PaddleOCR / OpenRouter / Local NER if NVIDIA skipped/failed ──
    ocr_text = ""
    ocr_time_ms = 0
    rx_fields = {}
    rx_medicines = []
    used_openrouter = False
    openrouter_result = None

    if not used_nvidia:
        log_audit_msg = "NVIDIA AI API key not configured" if not nvidia_service.is_configured() else "NVIDIA AI pipeline failed"
        logger.log_step("Prescription Fallback", f"{log_audit_msg} — executing PaddleOCR / OpenRouter fallback engine...")

        t_ocr = time.time()
        if not ocr_service.is_initialized:
            ocr_service.initialize()

        ocr_resp = ocr_service.process_image(preprocessed, image_name=filename)
        ocr_text = ocr_resp.full_text or ""
        ocr_time_ms = round((time.time() - t_ocr) * 1000)

        raw_ocr_items = [(item.coordinates, item.text, item.confidence) for item in ocr_resp.results]
        rx_data = medical_prescription_extractor.extract_prescription_data(raw_ocr_items, raw_full_text=ocr_text)
        rx_fields = rx_data.get("fields", {})
        rx_medicines = rx_data.get("medicines", [])

        if OPENROUTER_API_KEY:
            openrouter_result, attempt_logs = openrouter_service.extract_prescription(
                image_bytes=img_bytes,
                ocr_text=ocr_text,
                filename=filename
            )
            used_openrouter = openrouter_result is not None

    # ── 6. Normalization & Medical NER Processing ────────────────────────────
    total_time_ms = round((time.time() - t_start) * 1000)

    if used_nvidia and nvidia_result:
        # Run Medical NER Entity Classification on medicines
        if nvidia_result.get("medicines"):
            nvidia_result["medicines"] = medical_ner.process_entities(nvidia_result["medicines"])

        # Run Medical Abbreviation Expansion on all medicines (bd→twice daily, 1-0-1→morning+night, etc.)
        if nvidia_result.get("medicines"):
            nvidia_result["medicines"] = medical_abbreviation_expander.expand_medicines_list(
                nvidia_result["medicines"]
            )
        # Expand diagnosis abbreviations (HTN→Hypertension, DM→Diabetes Mellitus, etc.)
        if nvidia_result.get("diagnosis"):
            nvidia_result["diagnosis"] = medical_abbreviation_expander.expand_diagnoses_list(
                nvidia_result["diagnosis"]
            )

        final = normalize_prescription(nvidia_result)
        is_ok, grade, issues = validate_prescription_result(final)
        ocr_model_name = nvidia_result.get("ocr_model", nvidia_service.ocr_model)
        vision_model_name = nvidia_result.get("vision_model", nvidia_service.primary_vision_model)
        fallback_used = any(l.get("fallback_used") for l in attempt_logs)
    elif used_openrouter and openrouter_result:
        if not openrouter_result.get("raw_text"):
            openrouter_result["raw_text"] = ocr_text
        _merge_local_ner(openrouter_result, rx_fields, rx_medicines)
        if openrouter_result.get("medicines"):
            openrouter_result["medicines"] = medical_ner.process_entities(openrouter_result["medicines"])
        final = normalize_prescription(openrouter_result)
        is_ok, grade, issues = validate_prescription_result(final)
        ocr_model_name = "PaddleOCR"
        vision_model_name = openrouter_result.get("model_used", "openrouter")
        fallback_used = openrouter_result.get("fallback_attempt", 0) > 1
    else:
        final = build_local_fallback(
            ocr_text=ocr_text,
            rx_fields=rx_fields,
            medicines=rx_medicines,
            model_name="local_crnn_ner",
            attempt=len(attempt_logs)
        )
        if final.get("medicines"):
            final["medicines"] = medical_ner.process_entities(final["medicines"])
        is_ok, grade, issues = validate_prescription_result(final)
        ocr_model_name = "PaddleOCR"
        vision_model_name = "local_crnn_ner"
        fallback_used = True

    final["processing_time_ms"] = total_time_ms
    success = grade in ("high", "medium", "low")

    return {
        "success": success,
        "needs_manual_review": final.get("needs_manual_review", False),
        "data": final,
        "processing": {
            "ocr_model": ocr_model_name,
            "vision_model": vision_model_name,
            "model_used": vision_model_name,
            "used_nvidia": used_nvidia,
            "used_openrouter": used_openrouter,
            "fallback_used": fallback_used,
            "quality_grade": grade,
            "validation_issues": issues,
            "ocr_time_ms": ocr_time_ms,
            "total_time_ms": total_time_ms,
            "medicine_count": len([m for m in final.get("medicines", []) if m.get("name")]),
            "overall_confidence": final.get("overall_confidence", 0.0),
            "attempt_logs": attempt_logs
        }
    }


def _merge_local_ner(vision_result: dict, rx_fields: dict, rx_medicines: list):
    """
    Merge local NER fields into vision result where vision left nulls.
    Never overwrites values the vision model already found.
    """
    doctor = vision_result.get("doctor", {}) or {}
    if not doctor.get("name") and rx_fields.get("Doctor Name"):
        doctor["name"] = rx_fields["Doctor Name"]
    if not doctor.get("registration_number") and rx_fields.get("BMDC Registration No"):
        doctor["registration_number"] = rx_fields["BMDC Registration No"]
    vision_result["doctor"] = doctor

    patient = vision_result.get("patient", {}) or {}
    if not patient.get("name") and rx_fields.get("Patient Name"):
        patient["name"] = rx_fields["Patient Name"]
    if not patient.get("age"):
        ag = rx_fields.get("Age / Gender", "")
        if "/" in str(ag):
            patient["age"] = ag.split("/")[0].strip()
    vision_result["patient"] = patient

    if not vision_result.get("prescription_date") and rx_fields.get("Prescription Date"):
        vision_result["prescription_date"] = rx_fields["Prescription Date"]

    if not vision_result.get("diagnosis") and rx_fields.get("Diagnosis / Chief Complaint"):
        vision_result["diagnosis"] = [rx_fields["Diagnosis / Chief Complaint"]]

    # If vision found 0 medicines, use local NER medicines
    vision_meds = vision_result.get("medicines", [])
    named_vision = [m for m in vision_meds if m.get("name")]
    if not named_vision and rx_medicines:
        vision_result["medicines"] = [
            {
                "name": m.get("Brand Name"),
                "strength": m.get("Strength") if m.get("Strength") != "N/A" else None,
                "dosage": m.get("Dosage Pattern"),
                "frequency": m.get("Dosage Pattern"),
                "duration": m.get("Duration"),
                "route": "oral",
                "instructions": m.get("Timing"),
                "confidence": float(str(m.get("Match Confidence", "70")).replace("%", "")) / 100.0,
                "needs_review": False
            }
            for m in rx_medicines if m.get("Brand Name")
        ]
