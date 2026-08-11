import time
from typing import List, Dict, Any
from backend.models.schemas import StatsResponse, HealthResponse
from backend.utils.logger import logger

class MetricsService:
    def __init__(self):
        self.start_time = time.time()
        self.total_images_processed = 0
        self.total_processing_time = 0.0
        self.recent_activities: List[Dict[str, Any]] = []
        self.ocr_engine_loaded = False
        self.engine_type = "PaddleOCR"

    def record_ocr_request(self, image_name: str, processing_time: float, text_blocks: int, confidence: float):
        self.total_images_processed += 1
        self.total_processing_time += processing_time
        
        activity = {
            "id": self.total_images_processed,
            "timestamp": time.strftime("%H:%M:%S"),
            "image_name": image_name,
            "processing_time": round(processing_time, 3),
            "text_blocks": text_blocks,
            "confidence": round(confidence * 100, 1)
        }
        self.recent_activities.insert(0, activity)
        # Keep last 20 activities
        if len(self.recent_activities) > 20:
            self.recent_activities.pop()

    def get_stats(self) -> StatsResponse:
        avg_time = (
            self.total_processing_time / self.total_images_processed 
            if self.total_images_processed > 0 else 0.0
        )
        return StatsResponse(
            total_images_processed=self.total_images_processed,
            avg_processing_time=round(avg_time, 3),
            ocr_status="Active" if self.ocr_engine_loaded else "Initializing",
            current_model=f"{self.engine_type} (PP-OCRv4 / Multilingual)",
            server_status="Online",
            recent_activity=self.recent_activities
        )

    def get_health(self) -> HealthResponse:
        uptime = time.time() - self.start_time
        return HealthResponse(
            status="healthy",
            ocr_engine_loaded=self.ocr_engine_loaded,
            engine_type=self.engine_type,
            uptime_seconds=round(uptime, 1)
        )

metrics_service = MetricsService()
