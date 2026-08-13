"""
prescription_pipeline.py
─────────────────────────
Unified Prescription Processing Pipeline Orchestrator.

Implements the 7-stage prescription pipeline exactly as specified:

    PRESCRIPTION
         │
         ▼
  Image Preprocessing          ← Stage 1
         │
   ┌─────┴──────┐
   ▼            ▼
Printed      Handwritten       ← Stage 2: classify
   │            │
   ▼            ▼
PaddleOCR   NVIDIA             ← Stage 3a/3b: route OCR
           Nemotron-OCR-v2
   │            │
   └─────┬──────┘
         ▼
    NVIDIA VLM                 ← Stage 4: reasoning layer
         │
         ▼
   Medical NER                 ← Stage 5
         │
         ▼
Medicine validation            ← Stage 6
         │
         ▼
    Final JSON                 ← Stage 7
"""

import time
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from backend.utils.logger import logger
from backend.utils.image_processing import (
    decode_image_bytes,
    preprocess_prescription_image,
    preprocess_handwritten_document,
)
from backend.services.classifier_service import classify_document
from backend.services.ocr_service import ocr_service
from backend.services.nvidia_service import nvidia_service
from backend.services.medical_ner import medical_ner
from backend.services.medical_abbreviations import medical_abbreviation_expander
from backend.services.prescription_validator import (
    normalize_prescription,
    validate_prescription_result,
    build_local_fallback,
)
from backend.services.medical_prescription_extractor import medical_prescription_extractor
from backend.config import HTR_ENGINE, PRESCRIPTION_MIN_CONFIDENCE


# ── Helpers ───────────────────────────────────────────────────────────────────

def _img_to_jpeg_bytes(img: np.ndarray, max_dim: int = 2048) -> bytes:
    """Resize if needed and encode OpenCV BGR image to JPEG bytes."""
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return buf.tobytes()


def _detect_handwriting(img: np.ndarray, classifier_result: Dict[str, Any]) -> bool:
    """
    Returns True if the image is likely to contain significant handwritten content.
    Uses two signals:
      1. Classifier subtype keyword match (fast, zero cost)
      2. Image Laplacian variance heuristic (high irregular variance → handwriting)
    """
    # Signal 1: Classifier keyword
    subtype = str(classifier_result.get("subtype", "")).lower()
    if "handwritten" in subtype or "handwriting" in subtype:
        return True

    # Signal 2: Texture variance heuristic
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Below ~500: clean printed document | Above ~500: handwriting present
    return laplacian_var > 500.0


def _merge_ocr_outputs(
    paddle_tokens: List[Tuple],
    nvidia_text: str,
    has_handwriting: bool,
) -> str:
    """
    Merge PaddleOCR token list and NVIDIA OCR raw text into a single clean string.

    - Printed path: PaddleOCR is primary; NVIDIA text fills unique lines.
    - Handwritten path: NVIDIA is primary (better cursive reading);
      PaddleOCR printed text is appended as supporting context.
    """
    paddle_text = (
        "\n".join(tok[1] for tok in paddle_tokens if tok[1].strip())
        if paddle_tokens else ""
    )

    primary, secondary = (
        (nvidia_text.strip(), paddle_text.strip()) if has_handwriting
        else (paddle_text.strip(), nvidia_text.strip())
    )

    if not primary and not secondary:
        return ""
    if not secondary:
        return primary
    if not primary:
        return secondary

    # Append lines from secondary not already in primary
    primary_lines_lower = {l.strip().lower() for l in primary.splitlines() if l.strip()}
    extra_lines = [
        l for l in secondary.splitlines()
        if l.strip() and l.strip().lower() not in primary_lines_lower
    ]
    extra = "\n".join(extra_lines)
    return primary + ("\n" + extra if extra else "")


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run_prescription_pipeline(
    image_bytes: bytes,
    filename: str = "prescription.jpg",
) -> Dict[str, Any]:
    """
    Execute the 7-stage prescription processing pipeline.

    Args:
        image_bytes: Raw bytes of an image (JPG/PNG/WEBP/BMP) or PDF.
        filename:    Original filename (used for PDF detection and logging).

    Returns:
        Standardized prescription JSON dict with full audit log.
    """
    t_total = time.time()
    audit: List[str] = []

    def log(stage: str, msg: str = "") -> None:
        entry = f"[{stage}] {msg}" if msg else f"[{stage}]"
        audit.append(entry)
        logger.log_step(stage, msg)

    # ── Stage 0: PDF rendering ────────────────────────────────────────────────
    if filename.lower().endswith(".pdf"):
        try:
            from backend.utils.image_processing import render_pdf_to_images
            pages = render_pdf_to_images(image_bytes)
            if pages:
                image_bytes = _img_to_jpeg_bytes(pages[0])
                log("Stage 0: PDF Render", f"Rendered {len(pages)} page(s); using page 1")
            else:
                log("Stage 0: PDF Render", "render_pdf_to_images returned empty list")
        except Exception as exc:
            log("Stage 0: PDF Render Error", str(exc))

    # ── Stage 1: Image Preprocessing ─────────────────────────────────────────
    log("Stage 1: Preprocessing", "Decoding and preprocessing image")
    try:
        img_raw = decode_image_bytes(image_bytes)
    except Exception as exc:
        return _error_result(f"Image decode failed: {exc}", audit, t_total)

    try:
        img_preprocessed = preprocess_prescription_image(img_raw)
        log("Stage 1: Preprocessing",
            f"Shape after preprocess: {img_preprocessed.shape[1]}×{img_preprocessed.shape[0]}")
    except Exception as exc:
        img_preprocessed = img_raw
        log("Stage 1: Preprocessing Warning",
            f"preprocess_prescription_image failed ({exc}); using raw image")

    # ── Stage 2: Classify — Printed vs Handwritten ───────────────────────────
    log("Stage 2: Classification", "Detecting printed vs handwritten content")

    # Run OCR on a small thumbnail for fast classifier text signal
    classify_text = ""
    try:
        h, w = img_preprocessed.shape[:2]
        if max(h, w) > 640:
            scale = 640.0 / max(h, w)
            thumb = cv2.resize(img_preprocessed, (int(w * scale), int(h * scale)))
        else:
            thumb = img_preprocessed
        thumb_ocr = ocr_service.process_image(thumb, image_name="thumb_classify")
        classify_text = getattr(thumb_ocr, "full_text", "") or ""
    except Exception as exc:
        log("Stage 2: Classification Warning", f"Thumbnail OCR failed: {exc}")

    classifier_result = classify_document(
        classify_text, filename=filename, image_shape=img_preprocessed.shape[:2]
    )
    has_handwriting = _detect_handwriting(img_preprocessed, classifier_result)

    log("Stage 2: Classification",
        f"doc_type='{classifier_result['document_type']}' | "
        f"has_handwriting={has_handwriting}")

    # Apply handwriting-optimized preprocessing if handwriting detected
    if has_handwriting:
        try:
            img_preprocessed = preprocess_handwritten_document(img_preprocessed)
            log("Stage 2: Handwriting Preprocessing",
                "Applied CLAHE + bilateral filter + deskew")
        except Exception as exc:
            log("Stage 2: Handwriting Preprocessing Warning", str(exc))

    jpeg_bytes = _img_to_jpeg_bytes(img_preprocessed)

    # ── Stage 3a: PaddleOCR (Printed text branch) ────────────────────────────
    log("Stage 3a: PaddleOCR", "Extracting printed text")
    paddle_tokens: List[Tuple] = []
    paddle_text = ""
    try:
        paddle_result = ocr_service.process_image(img_preprocessed, image_name=filename)
        if hasattr(paddle_result, "items") and paddle_result.items:
            paddle_tokens = [
                (getattr(item, "bbox", []), item.text, item.confidence)
                for item in paddle_result.items
            ]
        paddle_text = getattr(paddle_result, "full_text", "") or \
                      "\n".join(t[1] for t in paddle_tokens)
        log("Stage 3a: PaddleOCR",
            f"{len(paddle_tokens)} tokens | {len(paddle_text)} chars")
    except Exception as exc:
        log("Stage 3a: PaddleOCR Error", str(exc))

    # ── Stage 3b: HTR Branch (Handwritten text) ──────────────────────────────
    nvidia_ocr_text = ""
    htr_model_used = "none"

    if has_handwriting:
        log("Stage 3b: HTR",
            f"Running handwriting recognition via HTR_ENGINE='{HTR_ENGINE}'")

        if HTR_ENGINE == "nvidia" and nvidia_service.is_configured():
            try:
                ocr_res = nvidia_service.run_nemotron_ocr(jpeg_bytes)
                nvidia_ocr_text = ocr_res.get("raw_text", "")
                htr_model_used = ocr_res.get("ocr_model", "nvidia-nemotron-ocr-v2")
                log("Stage 3b: NVIDIA Nemotron-OCR-v2",
                    f"{len(nvidia_ocr_text)} chars | "
                    f"confidence={ocr_res.get('ocr_confidence', 0):.2f}")
            except Exception as exc:
                log("Stage 3b: NVIDIA OCR Error", str(exc))
                nvidia_ocr_text = paddle_text
                htr_model_used = "paddle_fallback"

        elif HTR_ENGINE == "easyocr":
            # EasyOCR already ran inside Stage 3a via ocr_service
            nvidia_ocr_text = paddle_text
            htr_model_used = "easyocr"
            log("Stage 3b: EasyOCR", "Using EasyOCR output captured in Stage 3a")

        else:
            log("Stage 3b: HTR Fallback",
                "NVIDIA not configured / unknown engine — reusing PaddleOCR output")
            nvidia_ocr_text = paddle_text
            htr_model_used = "paddle_fallback"
    else:
        log("Stage 3b: HTR", "Skipped — printed document; PaddleOCR is primary")

    # ── Stage 3c: Merge OCR outputs ──────────────────────────────────────────
    merged_text = _merge_ocr_outputs(paddle_tokens, nvidia_ocr_text, has_handwriting)
    log("Stage 3c: OCR Merge",
        f"Merged text: {len(merged_text)} chars "
        f"(paddle={len(paddle_text)}, nvidia_htr={len(nvidia_ocr_text)})")

    # Medical abbreviation expansion
    try:
        merged_text = medical_abbreviation_expander.expand(merged_text)
        log("Abbrev Expansion", "Medical abbreviations expanded")
    except Exception as exc:
        log("Abbrev Expansion Warning", str(exc))

    # ── Stage 4: NVIDIA VLM Reasoning Layer ──────────────────────────────────
    log("Stage 4: NVIDIA VLM", "Invoking vision-language reasoning layer")
    vlm_result: Optional[Dict[str, Any]] = None
    vlm_logs: List[Dict] = []
    vlm_model_used = "none"

    if nvidia_service.is_configured():
        try:
            vlm_result, vlm_logs = nvidia_service.extract_prescription_nvidia(
                jpeg_bytes, filename=filename
            )
            if vlm_result:
                vlm_model_used = vlm_result.get("vision_model", "nvidia-vlm")
                conf = float(vlm_result.get("overall_confidence", 0.0))
                meds = vlm_result.get("medicines", [])
                log("Stage 4: NVIDIA VLM",
                    f"{len(meds)} medicines extracted | "
                    f"overall_confidence={conf:.2f} | model={vlm_model_used}")
            else:
                log("Stage 4: NVIDIA VLM",
                    "VLM returned None — will fall back to NER-only")
        except Exception as exc:
            log("Stage 4: NVIDIA VLM Error", str(exc))
    else:
        log("Stage 4: NVIDIA VLM", "NVIDIA API key not configured — skipping VLM")

    # Inject merged OCR text into VLM result if raw_text is empty
    if vlm_result and not vlm_result.get("raw_text"):
        vlm_result["raw_text"] = merged_text

    # ── Stage 5: Medical NER ─────────────────────────────────────────────────
    log("Stage 5: Medical NER", "Running named entity recognition on merged OCR text")
    ner_entities: Dict[str, Any] = {}
    try:
        ner_entities = medical_ner.extract_entities_from_text(merged_text)
        log("Stage 5: Medical NER",
            f"MEDICINE={len(ner_entities.get('MEDICINE', []))} | "
            f"DOCTOR={len(ner_entities.get('DOCTOR', []))} | "
            f"DIAGNOSIS={len(ner_entities.get('DIAGNOSIS', []))} | "
            f"TEST={len(ner_entities.get('TEST', []))}")
    except Exception as exc:
        log("Stage 5: Medical NER Error", str(exc))

    # Enrich VLM result with NER entities where VLM fields are null
    if vlm_result:
        _enrich_vlm_result_with_ner(vlm_result, ner_entities)

    # ── Stage 6: Medicine Validation ─────────────────────────────────────────
    log("Stage 6: Medicine Validation", "Normalizing and validating prescription")

    if vlm_result:
        raw_for_validation = vlm_result
    else:
        # All VLM models failed → local CRNN/NER extractor
        log("Stage 6: Local NER Fallback",
            "VLM unavailable — running local CRNN/NER extraction")
        try:
            local_rx = medical_prescription_extractor.extract_prescription_data(
                [], raw_full_text=merged_text
            )
            raw_meds = []
            if local_rx.get("tables"):
                raw_meds = local_rx["tables"][0].get("rows", [])
            raw_for_validation = build_local_fallback(
                ocr_text=merged_text,
                rx_fields=local_rx.get("fields", {}),
                medicines=raw_meds,
                model_name="local_ner_crnn",
                attempt=1,
            )
        except Exception as exc:
            log("Stage 6: Local NER Error", str(exc))
            raw_for_validation = {
                "raw_text": merged_text,
                "medicines": [],
                "overall_confidence": 0.0,
            }

    # Normalize individual medicines through NER normalizer
    if raw_for_validation.get("medicines"):
        try:
            raw_for_validation["medicines"] = medical_ner.process_entities(
                raw_for_validation["medicines"]
            )
            log("Stage 6: NER Normalize",
                f"Normalized {len(raw_for_validation['medicines'])} medicines")
        except Exception as exc:
            log("Stage 6: NER Normalize Warning", str(exc))

    # Full schema normalization + confidence grading
    normalized = normalize_prescription(raw_for_validation)
    is_acceptable, grade, issues = validate_prescription_result(normalized)
    log("Stage 6: Validation",
        f"grade={grade} | acceptable={is_acceptable} | issues={len(issues)}")

    # ── Stage 7: Final JSON ───────────────────────────────────────────────────
    total_ms = round((time.time() - t_total) * 1000)
    log("Stage 7: Final JSON", f"Pipeline complete in {total_ms}ms")

    return {
        "success": True,
        "document_type": "doctor_prescription",
        "pipeline_stages": {
            "preprocessing":     "applied",
            "ocr_printed":       "paddleocr",
            "ocr_handwritten":   htr_model_used if has_handwriting else "skipped",
            "vlm_reasoning":     vlm_model_used,
            "medical_ner":       "applied",
            "validation_grade":  grade,
        },
        "has_handwriting": has_handwriting,
        "prescription": normalized,
        "ner_entities": ner_entities,
        "validation": {
            "grade": grade,
            "is_acceptable": is_acceptable,
            "issues": issues,
        },
        "metadata": {
            "filename": filename,
            "classifier": classifier_result,
            "htr_engine": HTR_ENGINE if has_handwriting else "n/a",
            "processing_time_ms": total_ms,
            "audit_trail": audit,
            "vlm_logs": vlm_logs,
        },
    }


# ── Private Helpers ───────────────────────────────────────────────────────────

def _enrich_vlm_result_with_ner(
    vlm_result: Dict[str, Any],
    ner_entities: Dict[str, Any],
) -> None:
    """
    Fill null fields in VLM result using NER entity lists.
    Modifies vlm_result in-place. Never overwrites non-null VLM values.
    """
    doctor = vlm_result.get("doctor") or {}
    patient = vlm_result.get("patient") or {}

    if not doctor.get("name") and ner_entities.get("DOCTOR"):
        doctor["name"] = ner_entities["DOCTOR"][0]
        vlm_result["doctor"] = doctor

    if not patient.get("name") and ner_entities.get("PATIENT"):
        patient["name"] = ner_entities["PATIENT"][0]
        vlm_result["patient"] = patient

    if not vlm_result.get("diagnosis") and ner_entities.get("DIAGNOSIS"):
        vlm_result["diagnosis"] = ner_entities["DIAGNOSIS"]

    if not vlm_result.get("tests") and ner_entities.get("TEST"):
        vlm_result["tests"] = ner_entities["TEST"]

    if not vlm_result.get("general_instructions") and ner_entities.get("INSTRUCTION"):
        vlm_result["general_instructions"] = ner_entities["INSTRUCTION"]


def _error_result(
    message: str, audit: List[str], t_start: float
) -> Dict[str, Any]:
    """Build a standardized pipeline error result."""
    return {
        "success": False,
        "error": message,
        "prescription": None,
        "ner_entities": {},
        "validation": {"grade": "rejected", "is_acceptable": False, "issues": [message]},
        "metadata": {
            "processing_time_ms": round((time.time() - t_start) * 1000),
            "audit_trail": audit,
            "vlm_logs": [],
        },
    }
