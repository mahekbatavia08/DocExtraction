"""
excel_routes.py
────────────────
FastAPI Router for Standalone Excel Module:
- GET /api/excel/download : Download persistent Excel workbook (document_extraction.xlsx)
- GET /api/excel/records  : Retrieve JSON records stored in Excel
- GET /api/excel/summary  : Retrieve extraction performance summary metrics
- POST /api/excel/export  : Export arbitrary JSON records into custom Excel buffer
"""

import time
import os
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, FileResponse

from backend.services.excel_service import excel_service, EXCEL_FILE_PATH

router = APIRouter(prefix="/api/excel", tags=["Excel Data Management"])

@router.get("/download")
async def download_excel_workbook():
    """Download persistent document_extraction.xlsx workbook attachment."""
    if not os.path.exists(EXCEL_FILE_PATH):
        raise HTTPException(status_code=404, detail="No Excel records found yet. Process a document first.")

    filename = f"document_extraction_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
    return FileResponse(
        path=EXCEL_FILE_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )

@router.get("/records")
async def get_excel_records():
    """Retrieve list of JSON records stored in the main Excel sheet."""
    records = excel_service.get_records()
    return {
        "count": len(records),
        "records": records
    }

@router.get("/summary")
async def get_excel_summary():
    """Retrieve aggregated performance metrics from Excel summary sheet."""
    summary = excel_service.get_summary()
    return {
        "count": len(summary),
        "summary": summary
    }

@router.post("/export")
async def export_custom_excel(documents: List[Dict[str, Any]]):
    """Export custom list of documents into in-memory Excel file buffer."""
    excel_bytes = excel_service.export_custom_buffer(documents)
    filename = f"custom_extraction_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
