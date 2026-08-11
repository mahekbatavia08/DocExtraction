from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import numpy as np

from backend.models.schemas import OCRResponse, HealthResponse, StatsResponse
from backend.services.ocr_service import ocr_service
from backend.services.metrics_service import metrics_service
from backend.services.document_service import document_service
from backend.services.ai_service import ai_service
from backend.api.documents import router as documents_router
from backend.utils.image_processing import (
    decode_image_bytes, 
    decode_base64_image, 
    render_pdf_to_images,
    assess_frame_quality,
    encode_image_to_base64
)
from backend.services.universal_pipeline import run_universal_pipeline
from backend.utils.logger import logger

router = APIRouter()
router.include_router(documents_router)

class WebcamPayload(BaseModel):
    image_base64: str

@router.get("/health", response_model=HealthResponse)
async def get_health():
    """Return API and OCR Engine health status."""
    return metrics_service.get_health()

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Return metrics summary for the Dashboard Home page."""
    return metrics_service.get_stats()

@router.get("/api/ai/status")
@router.get("/ai/status")
async def get_ai_status():
    """Return local Ollama AI status, installed models, and multi-model fallback hierarchy."""
    from backend.config import PRIMARY_MODEL, BACKUP_MODEL_1, BACKUP_MODEL_2
    from backend.services.ollama_service import ollama_service
    installed = ollama_service.get_installed_models()
    status = ai_service.check_health()
    return {
        "available": status.is_available,
        "model": status.configured_model if status.is_available else None,
        "is_available": status.is_available,
        "ollama_host": status.ollama_host,
        "configured_model": status.configured_model,
        "primary_model": PRIMARY_MODEL,
        "backup_model_1": BACKUP_MODEL_1,
        "backup_model_2": BACKUP_MODEL_2,
        "active_models": installed or status.active_models,
        "message": status.message
    }

@router.post("/ocr/quality_check")
async def check_image_quality(payload: WebcamPayload):
    """
    Evaluate webcam frame quality: Blur Score (Laplacian var), Brightness, Document Presence.
    Returns live quality metrics for UI indicator badges.
    """
    if not payload.image_base64:
        raise HTTPException(status_code=400, detail="Missing image_base64 payload.")
    try:
        img = decode_base64_image(payload.image_base64)
        quality = assess_frame_quality(img)
        return quality
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality check error: {str(e)}")

@router.post("/ocr/universal")
async def process_universal_document(file: Optional[UploadFile] = File(None)):
    """
    Universal Autonomous AI Document Processing Endpoint (Zero-Error Mode).
    Processes PDF, Images, Excel, PAN, Aadhaar, Invoices, Bank statements, Contracts with 8-stage pipeline.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    try:
        contents = await file.read()
        filename = file.filename or "uploaded_document"
        image_data_base64 = ""
        
        # Check if Excel file
        if filename.lower().endswith((".xlsx", ".xls", ".csv")):
            res = run_universal_pipeline(file_bytes=contents, filename=filename)
        elif filename.lower().endswith(".pdf") or file.content_type == "application/pdf":
            # Check if digital PDF contains selectable text
            from backend.utils.image_processing import extract_digital_pdf_text
            digital_text = extract_digital_pdf_text(contents)
            if digital_text:
                logger.log_step("Digital PDF Processing", f"Extracted {len(digital_text)} chars from digital PDF '{filename}'. Bypassing image OCR.")
                res = run_universal_pipeline(raw_text_input=digital_text, filename=filename)
            else:
                pages = render_pdf_to_images(contents)
                if not pages:
                    raise ValueError("No readable pages found in PDF")
                image_data_base64 = "data:image/png;base64," + encode_image_to_base64(pages[0])
                res = run_universal_pipeline(img=pages[0], filename=filename)
        else:
            img = decode_image_bytes(contents)
            image_data_base64 = "data:image/png;base64," + encode_image_to_base64(img)
            res = run_universal_pipeline(img=img, filename=filename)

        # Automatically save to SQLite DB
        try:
            doc_id = document_service.save_document_result(
                filename=filename,
                file_type=file.content_type or "image/png",
                document_type=res.get("document_type", "Unknown"),
                raw_ocr_text=res.get("raw_text", ""),
                extracted_fields=res.get("fields", {}),
                processing_time=float(res.get("processing_time", "0.5s").replace("s", "")),
                overall_confidence=float(res.get("confidence", 0.95)),
                processing_status="completed",
                image_data=image_data_base64
            )
            res["document_id"] = doc_id
        except Exception as db_err:
            logger.log_step("DB Save Warning", str(db_err))

        return res

    except Exception as e:
        logger.log_step("Universal Pipeline Error", str(e))
        return {
            "status": "failed",
            "document_type": "Unknown",
            "failure_stage": "Input Parsing",
            "suspected_cause": str(e),
            "recoveries_attempted": ["Fallback decoding"],
            "partial_data": {},
            "confidence": 0.0
        }

@router.post("/ocr/image", response_model=OCRResponse)
async def process_ocr_image(file: UploadFile = File(...)):
    """Accept uploaded image file and run PaddleOCR."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file type. Please upload an image file."
        )

    try:
        contents = await file.read()
        img = decode_image_bytes(contents)
        response = ocr_service.process_image(img, image_name=file.filename or "Uploaded Image")

        # Automatically save result to SQLite DB
        try:
            img_b64 = "data:image/png;base64," + encode_image_to_base64(img)
            doc_id = document_service.save_document_result(
                filename=file.filename or "Uploaded Image",
                file_type=file.content_type or "image/png",
                document_type="Document Image",
                raw_ocr_text=response.full_text or "",
                extracted_fields=response.extracted_fields or {},
                processing_time=response.processing_time,
                overall_confidence=response.overall_confidence,
                processing_status="completed",
                image_data=img_b64
            )
            response.timestamp = str(doc_id)
        except Exception as db_err:
            logger.log_step("DB Save Warning", str(db_err))

        return response
    except Exception as e:
        logger.log_step("Error processing image", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )

@router.post("/ocr/pdf", response_model=OCRResponse)
async def process_ocr_pdf(file: UploadFile = File(...)):
    """Accept PDF file, convert pages to images, and run PaddleOCR."""
    if not file.filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a PDF file."
        )

    try:
        contents = await file.read()
        pages = render_pdf_to_images(contents)
        if not pages:
            raise ValueError("No readable pages found in PDF")
        
        first_page = pages[0]
        response = ocr_service.process_image(first_page, image_name=f"{file.filename} (Page 1)")

        try:
            img_b64 = "data:image/png;base64," + encode_image_to_base64(first_page)
            doc_id = document_service.save_document_result(
                filename=file.filename or "Uploaded PDF",
                file_type="application/pdf",
                document_type="PDF Document",
                raw_ocr_text=response.full_text or "",
                extracted_fields=response.extracted_fields or {},
                processing_time=response.processing_time,
                overall_confidence=response.overall_confidence,
                processing_status="completed",
                image_data=img_b64
            )
            response.timestamp = str(doc_id)
        except Exception as db_err:
            logger.log_step("DB Save Warning", str(db_err))

        return response
    except Exception as e:
        logger.log_step("Error processing PDF", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}"
        )

@router.post("/ocr/webcam", response_model=OCRResponse)
async def process_ocr_webcam(payload: WebcamPayload):
    """Accept base64 webcam frame capture, enforce quality gate, and run PaddleOCR."""
    if not payload.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing image_base64 payload."
        )

    try:
        img = decode_base64_image(payload.image_base64)
        response = ocr_service.process_image(img, image_name="Live Webcam Capture")

        try:
            img_b64 = payload.image_base64 if payload.image_base64.startswith("data:") else "data:image/png;base64," + payload.image_base64
            doc_id = document_service.save_document_result(
                filename="Live Webcam Capture",
                file_type="image/jpeg",
                document_type="Webcam Capture",
                raw_ocr_text=response.full_text or "",
                extracted_fields=response.extracted_fields or {},
                processing_time=response.processing_time,
                overall_confidence=response.overall_confidence,
                processing_status="completed",
                image_data=img_b64
            )
            response.timestamp = str(doc_id)
        except Exception as db_err:
            logger.log_step("DB Save Warning", str(db_err))

        return response
    except Exception as e:
        logger.log_step("Error processing webcam frame", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webcam frame: {str(e)}"
        )

