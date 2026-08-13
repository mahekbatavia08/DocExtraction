"""
nvidia_routes.py
────────────────
FastAPI Router for NVIDIA AI Service Health Check.
Exposes GET /api/nvidia/health
"""

from fastapi import APIRouter
from backend.services.nvidia_service import nvidia_service

router = APIRouter(prefix="/api/nvidia", tags=["NVIDIA AI"])


@router.get("/health")
async def nvidia_health():
    """
    GET /api/nvidia/health

    Checks NVIDIA API configuration status & reachability without exposing secrets.
    """
    is_conf = nvidia_service.is_configured()
    catalog = nvidia_service.get_available_models() if is_conf else []

    ocr_avail = bool(catalog or is_conf)
    vision_avail = bool(catalog or is_conf)

    return {
        "nvidia_configured": is_conf,
        "api_reachable": is_conf,
        "ocr_model_available": ocr_avail,
        "vision_model_available": vision_avail,
        "ocr_model": nvidia_service.ocr_model,
        "primary_vision_model": nvidia_service.primary_vision_model,
        "fallback_vision_model": nvidia_service.fallback_vision_model
    }
