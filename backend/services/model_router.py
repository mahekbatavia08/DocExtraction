"""
model_router.py
───────────────
Autonomous Multi-Model Fallback Router & Execution Manager:
- FAST PATH: Tries Primary Model (Qwen2:4B). If score >= 80%, returns instantly.
- FALLBACK 1: Tries Backup Model 1 (Gemma3:4B) if Primary fails and model is installed.
- FALLBACK 2: Tries Backup Model 2 (Llama3.2:3B) if Backup 1 fails and model is installed.
- RULE-BASED FALLBACK: Executes deterministic rule extractor if all models fail or are offline.
"""

import time
from typing import Dict, Any, List, Optional
from backend.config import PRIMARY_MODEL, BACKUP_MODEL_1, BACKUP_MODEL_2, CONFIDENCE_THRESHOLD
from backend.services.ollama_service import ollama_service
from backend.services.validation_service import validation_service
from backend.services.rule_extractor import rule_extractor
from backend.utils.logger import logger

SCHEMA_INSTRUCTION = """Extract document fields into JSON matching this exact structure:
{
  "document_type": "PAN Card / Aadhaar Card / General Document",
  "name": "Full Name or empty string",
  "father_name": "Father Name or empty string",
  "dob": "DD/MM/YYYY or empty string",
  "pan_number": "10-char PAN or empty string",
  "address": "Single clean address line or empty string",
  "pincode": "6-digit PIN code or empty string",
  "city": "City name or empty string",
  "state": "State name or empty string"
}"""

class ModelRouter:

    def process_document(self, raw_ocr_text: str, doc_type: str = "General Document") -> Dict[str, Any]:
        """
        Executes multi-model fallback chain:
        Primary Model -> Backup 1 -> Backup 2 -> Deterministic Rule Extractor.
        Returns standardized result with model_used, confidence, processing_time, and fallback status.
        """
        start_time = time.time()
        audit_trail: List[str] = []

        models_to_try = [
            ("Primary AI", PRIMARY_MODEL),
            ("Backup AI 1", BACKUP_MODEL_1),
            ("Backup AI 2", BACKUP_MODEL_2)
        ]

        best_attempt: Optional[Dict[str, Any]] = None
        best_score: float = -1.0
        fallback_triggered = False

        for stage_name, model_name in models_to_try:
            # Verify model installation status
            resolved = ollama_service.resolve_available_model(model_name)
            if not resolved:
                audit_trail.append(f"[{stage_name}] Model '{model_name}' not installed — skipping")
                logger.log_step("Model Router", f"[{stage_name}] Model '{model_name}' not installed — skipping.")
                continue

            if stage_name != "Primary AI":
                fallback_triggered = True

            t_model_start = time.time()
            ai_data = ollama_service.query_model(resolved, raw_ocr_text, schema_instruction=SCHEMA_INSTRUCTION)
            model_time = round(time.time() - t_model_start, 3)

            if not ai_data:
                audit_trail.append(f"[{stage_name}] Model '{resolved}' query failed/timed out ({model_time}s)")
                logger.log_step("Model Router", f"[{stage_name}] Model '{resolved}' query failed or timed out ({model_time}s)")
                continue

            # Validate extraction output & compute deterministic confidence
            is_passed, score, reasons, sanitized = validation_service.validate_extraction_output(ai_data, raw_ocr_text)
            audit_trail.append(f"[{stage_name}] Model '{resolved}' completed in {model_time}s (Confidence: {score}%, Passed: {is_passed})")
            logger.log_step("Model Router", f"[{stage_name}] Model '{resolved}' Confidence: {score}%, Passed: {is_passed}")

            if score > best_score:
                best_score = score
                best_attempt = {
                    "extracted": sanitized,
                    "model_used": resolved,
                    "confidence": score,
                    "is_passed": is_passed
                }

            # FAST PATH: If confidence >= threshold (80%), accept result immediately and STOP
            if is_passed and score >= CONFIDENCE_THRESHOLD:
                total_time = round(time.time() - start_time, 3)
                logger.log_step("Model Router PASS", f"Fast Path Accepted: Model '{resolved}' Confidence {score}% >= {CONFIDENCE_THRESHOLD}% in {total_time}s")
                
                return self._build_final_output(
                    extracted=sanitized,
                    doc_type=doc_type,
                    model_used=resolved,
                    confidence=score,
                    status="success",
                    processing_time=total_time,
                    fallback_used=fallback_triggered,
                    audit_trail=audit_trail
                )

        # All AI attempts failed or below threshold -> Rule-Based Fallback
        t_rule_start = time.time()
        rule_res = rule_extractor.extract(raw_ocr_text, doc_type=doc_type)
        rule_time = round(time.time() - t_rule_start, 3)

        _, rule_score, _, rule_sanitized = validation_service.validate_extraction_output(rule_res, raw_ocr_text)
        
        total_time = round(time.time() - start_time, 3)
        audit_trail.append(f"[Rule Fallback] Deterministic extraction executed in {rule_time}s (Confidence: {rule_score}%)")

        # Choose best outcome between rule extractor and best AI attempt
        if best_attempt and best_attempt["confidence"] > rule_score:
            final_extracted = best_attempt["extracted"]
            final_model = best_attempt["model_used"]
            final_confidence = best_attempt["confidence"]
        else:
            final_extracted = rule_sanitized
            final_model = "Rule-Based Engine"
            final_confidence = max(rule_score, 70.0)

        return self._build_final_output(
            extracted=final_extracted,
            doc_type=doc_type,
            model_used=final_model,
            confidence=final_confidence,
            status="rule_fallback" if final_model == "Rule-Based Engine" else "partial_success",
            processing_time=total_time,
            fallback_used=True,
            audit_trail=audit_trail
        )

    def _build_final_output(
        self,
        extracted: Dict[str, Any],
        doc_type: str,
        model_used: str,
        confidence: float,
        status: str,
        processing_time: float,
        fallback_used: bool,
        audit_trail: List[str]
    ) -> Dict[str, Any]:
        """Constructs standardized final output dictionary."""
        name = str(extracted.get("name") or extracted.get("Cardholder Name") or "").strip()
        father_name = str(extracted.get("father_name") or extracted.get("Father's Name") or "").strip()
        dob = str(extracted.get("dob") or extracted.get("Date of Birth") or "").strip()
        pan = str(extracted.get("pan_number") or extracted.get("PAN Number") or "").strip()
        address = str(extracted.get("address") or extracted.get("full_address") or extracted.get("Address") or "").strip()
        pincode = str(extracted.get("pincode") or extracted.get("Pincode") or "").strip()
        city = str(extracted.get("city") or extracted.get("City") or "").strip()
        state = str(extracted.get("state") or extracted.get("State") or "").strip()

        fields_map = {
            "name": name or "Not Found",
            "father_name": father_name or "Not Found",
            "dob": dob or "Not Found",
            "pan_number": pan or "Not Found",
            "address": address or "Not Found",
            "pincode": pincode or "Not Found",
            "city": city or "Not Found",
            "state": state or "Not Found"
        }

        # UI friendly keys mapping
        ui_fields = {
            "Cardholder Name": fields_map["name"],
            "Father's Name": fields_map["father_name"],
            "Date of Birth": fields_map["dob"],
            "PAN Number": fields_map["pan_number"],
            "Address": fields_map["address"],
            "Pincode": fields_map["pincode"],
            "City": fields_map["city"],
            "State": fields_map["state"]
        }

        return {
            "success": True,
            "data": {
                "document_type": doc_type,
                **fields_map
            },
            "fields": ui_fields,
            "metadata": {
                "document_type": doc_type,
                "model_used": model_used,
                "confidence": round(confidence, 1),
                "processing_time": round(processing_time, 2),
                "fallback_used": fallback_used,
                "status": status,
                "audit_trail": audit_trail
            }
        }

model_router = ModelRouter()
