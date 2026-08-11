"""
ai_schemas.py
─────────────
Pydantic schema definitions for local Ollama AI integration, document classification,
entity extraction, address block validation, and evidence reporting.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AIServiceStatus(BaseModel):
    is_available: bool = False
    ollama_host: str = "http://localhost:11434"
    configured_model: str = "qwen2.5:1.5b"
    active_models: List[str] = []
    message: str = "Local AI Status"

class LocationFieldEvidence(BaseModel):
    value: str = "Not Found"
    source: str = "Unverified"
    confidence: float = 0.0
    matched_candidate: Optional[str] = None

AddressEvidenceDict = Dict[str, LocationFieldEvidence]

class AddressBlockSchema(BaseModel):
    full_address: str = "Not Found"
    city: str = "Not Found"
    district: str = "Not Found"
    state: str = "Not Found"
    pincode: str = "Not Found"
    address_confidence: float = 0.0
    city_confidence: float = 0.0
    district_confidence: float = 0.0
    state_confidence: float = 0.0
    location_mismatch: bool = False
    mismatch_reason: Optional[str] = None
    extraction_evidence: Optional[Dict[str, Any]] = None
    debug_info: Optional[Dict[str, Any]] = None

class AIDocumentClassification(BaseModel):
    document_type: str = "UNKNOWN"
    confidence: float = 0.0
    reasoning: Optional[str] = None

class AIExtractionResult(BaseModel):
    document_type: str = "UNKNOWN"
    ai_status: str = "success"  # "success", "failed", "offline"
    ai_error: Optional[str] = None
    classification_confidence: float = 0.0
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    address_data: Optional[AddressBlockSchema] = None
    validation_passed: bool = True
    validation_status: str = "PASS"
    warnings: List[str] = Field(default_factory=list)
