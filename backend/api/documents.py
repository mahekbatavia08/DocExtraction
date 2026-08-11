"""
documents.py
────────────
FastAPI API router for SQLite Database CRUD operations:
- POST /api/documents/upload
- GET /api/documents
- GET /api/documents/{id}
- DELETE /api/documents/{id}
- GET /api/documents/{id}/fields
- GET /api/documents/{id}/logs
- GET /api/contacts
- GET /api/contacts/{id}
"""

import time
import base64
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, status
from pydantic import BaseModel

from backend.services.document_service import document_service
from backend.services.universal_pipeline import run_universal_pipeline
from backend.services.ocr_service import ocr_service
from backend.utils.image_processing import decode_image_bytes, render_pdf_to_images, encode_image_to_base64
from backend.utils.logger import logger

router = APIRouter(prefix="/api", tags=["Database Documents"])

class UploadPayload(BaseModel):
    image_base64: Optional[str] = None
    filename: Optional[str] = "uploaded_document.png"
    document_type: Optional[str] = None

@router.post("/documents/upload")
async def upload_and_save_document(
    file: Optional[UploadFile] = File(None),
    filename: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None)
):
    """
    Backend Flow:
    Upload -> Create document record -> Process OCR -> Extract fields -> Validate fields ->
    Calculate confidence -> Save OCR result -> Save extracted fields -> Save processing logs ->
    Return database record ID & complete record.
    """
    start_time = time.time()
    fname = filename or (file.filename if file else "uploaded_document")
    file_bytes = None
    image_data_base64 = ""
    pipeline_res = None

    stage_logs = []
    def add_log(stage: str, msg: str, duration: float = 0.0):
        stage_logs.append({
            "stage": stage,
            "message": msg,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": round(duration, 3)
        })

    t0 = time.time()
    add_log("Upload", f"Received document '{fname}'. Creating document record.", time.time() - t0)

    try:
        if file:
            file_bytes = await file.read()
            # Generate base64 thumbnail preview if it's an image
            if file.content_type.startswith("image/") or fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                image_data_base64 = f"data:{file.content_type or 'image/png'};base64," + base64.b64encode(file_bytes).decode('utf-8')
        
        t1 = time.time()
        # Process through Universal OCR Pipeline
        if file_bytes:
            if fname.lower().endswith((".xlsx", ".xls", ".csv")):
                pipeline_res = run_universal_pipeline(file_bytes=file_bytes, filename=fname)
            elif fname.lower().endswith(".pdf") or (file and file.content_type == "application/pdf"):
                pages = render_pdf_to_images(file_bytes)
                if pages:
                    image_data_base64 = "data:image/png;base64," + encode_image_to_base64(pages[0])
                    pipeline_res = run_universal_pipeline(img=pages[0], filename=fname)
            else:
                img = decode_image_bytes(file_bytes)
                image_data_base64 = "data:image/png;base64," + encode_image_to_base64(img)
                pipeline_res = run_universal_pipeline(img=img, filename=fname)

        if not pipeline_res:
            raise HTTPException(status_code=400, detail="Invalid file buffer or unsupported format.")

        ocr_duration = round(time.time() - t1, 3)
        add_log("Process OCR", f"Deep OCR inference completed in {ocr_duration}s.", ocr_duration)

        # Extract values
        raw_ocr_text = pipeline_res.get("raw_text", "")
        extracted_fields = pipeline_res.get("fields", {})
        doc_type = document_type or pipeline_res.get("document_type", "Unknown")
        overall_confidence = float(pipeline_res.get("confidence", 0.95))

        t2 = time.time()
        add_log("Extract Fields", f"Extracted {len(extracted_fields)} key-value entities.", round(time.time() - t2, 3))

        t3 = time.time()
        add_log("Validate Fields", "Validated rules & masked sensitive parameters (Aadhaar / Payment Cards).", round(time.time() - t3, 3))

        total_duration = round(time.time() - start_time, 3)

        # Save to SQLite database
        doc_id = document_service.save_document_result(
            filename=fname,
            file_type=file.content_type if file else "image/png",
            document_type=doc_type,
            raw_ocr_text=raw_ocr_text,
            extracted_fields=extracted_fields,
            processing_time=total_duration,
            overall_confidence=overall_confidence,
            processing_status="completed",
            image_data=image_data_base64,
            stage_logs=stage_logs
        )

        saved_doc = document_service.get_document_by_id(doc_id)
        return {
            "success": True,
            "id": doc_id,
            "document_id": doc_id,
            "message": "Document processed and saved to database successfully.",
            "document": saved_doc,
            "pipeline_result": pipeline_res
        }

    except Exception as e:
        logger.log_step("Upload DB Error", str(e))
        total_duration = round(time.time() - start_time, 3)
        add_log("Failure", f"Processing error: {str(e)}", total_duration)

        # Save error record into DB as specified in requirements
        doc_id = document_service.save_document_result(
            filename=fname,
            file_type="unknown",
            document_type=document_type or "Unknown",
            raw_ocr_text=f"Error processing document: {str(e)}",
            extracted_fields={},
            processing_time=total_duration,
            overall_confidence=0.0,
            processing_status="failed",
            image_data=image_data_base64,
            stage_logs=stage_logs
        )

        return {
            "success": False,
            "id": doc_id,
            "document_id": doc_id,
            "error": str(e),
            "document": document_service.get_document_by_id(doc_id)
        }

@router.get("/documents")
async def get_documents(
    search: Optional[str] = Query(None, description="Search term for filename, type, or raw text"),
    document_type: Optional[str] = Query(None, description="Filter by document type e.g. PAN Card, Invoice"),
    sort_by: str = Query("date", description="Sort field: date, confidence, filename, type"),
    order: str = Query("desc", description="Sort order: asc, desc")
):
    """Retrieve list of all database documents with search, filtering, and sorting."""
    documents = document_service.get_documents(
        search=search,
        document_type=document_type,
        sort_by=sort_by,
        order=order
    )
    return {
        "count": len(documents),
        "documents": documents
    }

from fastapi.responses import Response
from backend.services.excel_service import excel_service

@router.get("/documents/export/excel")
async def export_documents_excel(
    document_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Export processed documents to a clean Excel spreadsheet (.xlsx)."""
    documents = document_service.get_documents(search=search, document_type=document_type)
    excel_bytes = excel_service.export_documents_to_excel(documents)
    
    filename = f"extracted_documents_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/documents/stats")
async def get_documents_stats():
    """Retrieve aggregated stats for Database History Dashboard cards."""
    return document_service.get_dashboard_stats()

@router.get("/documents/{id}")
async def get_document_by_id(id: int):
    """Get single document detail with extracted fields, processing logs, and contact info."""
    doc = document_service.get_document_by_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {id} not found.")
    return doc

@router.delete("/documents/{id}")
async def delete_document_by_id(id: int):
    """Delete document by ID."""
    deleted = document_service.delete_document(id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document with ID {id} not found.")
    return {"success": True, "message": f"Document ID {id} deleted successfully."}

@router.get("/documents/{id}/fields")
async def get_document_fields(id: int):
    """Get extracted fields for document ID."""
    return document_service.get_document_fields(id)

@router.get("/documents/{id}/logs")
async def get_document_logs(id: int):
    """Get processing logs for document ID."""
    return document_service.get_document_logs(id)

@router.get("/contacts")
async def get_contacts(search: Optional[str] = Query(None)):
    """Get all extracted business contacts."""
    contacts = document_service.get_contacts(search=search)
    return {
        "count": len(contacts),
        "contacts": contacts
    }

@router.get("/contacts/{id}")
async def get_contact_by_id(id: int):
    """Get business contact detail by ID."""
    contact = document_service.get_contact_by_id(id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact with ID {id} not found.")
    return contact
