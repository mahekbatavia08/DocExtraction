from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class OCRResultItem(BaseModel):
    id: int
    text: str
    raw_text: Optional[str] = None
    corrected_text: Optional[str] = None
    confidence: float
    is_low_confidence: bool = False
    coordinates: List[List[float]] = Field(
        ..., 
        description="4 corner points of text bounding box [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]"
    )
    bbox: List[List[float]] = Field(
        ..., 
        description="4 corner points of text bounding box [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]"
    )

class PANDetails(BaseModel):
    is_pan_card: bool = False
    name: Optional[str] = None
    father_name: Optional[str] = None
    dob: Optional[str] = None
    pan_number: Optional[str] = None
    confidence: float = 0.0

class OCRResponse(BaseModel):
    success: bool
    processing_time: float
    image_size: List[int] = Field(..., description="[width, height]")
    results: List[OCRResultItem]
    pan_details: Optional[PANDetails] = None
    extracted_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extracted key-value entities e.g. Name, DOB, Phone, Address")
    full_text: Optional[str] = None
    image_name: Optional[str] = None
    detected_blocks_count: int = 0
    memory_usage_mb: float = 0.0
    annotated_image_base64: Optional[str] = None
    overall_confidence: float = 0.0
    model_version: str = "PaddleOCR PP-OCRv4 Engine"
    timestamp: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    ocr_engine_loaded: bool
    engine_type: str
    uptime_seconds: float

class StatsResponse(BaseModel):
    total_images_processed: int
    avg_processing_time: float
    ocr_status: str
    current_model: str
    server_status: str
    recent_activity: List[Dict[str, Any]] = []
