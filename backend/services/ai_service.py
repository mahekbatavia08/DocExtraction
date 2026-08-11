"""
ai_service.py
─────────────
Additive Local Ollama AI Client Service:
- Communicates with local Ollama server (http://localhost:11434).
- Checks server connectivity and model availability.
- Executes LLM structured JSON generation with strict system prompt.
- Non-blocking fallback: If Ollama is offline or model fails, returns ai_status='offline'
  without stopping or breaking PaddleOCR.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from backend.schemas.ai_schemas import AIServiceStatus
from backend.utils.logger import logger

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

SYSTEM_PROMPT = """You are a high-precision document information extraction AI engine.
Rules:
1. Use ONLY the OCR text provided.
2. Never invent, guess, or hallucinate information.
3. If a field is missing, unreadable, or ambiguous, return null.
4. Do not use the user's location or previous documents.
5. Return ONLY a valid JSON object matching the requested schema.
"""

class LocalAIService:
    def __init__(self):
        self.host = OLLAMA_HOST
        self.model = OLLAMA_MODEL
        self._cached_status: Optional[AIServiceStatus] = None
        self._last_check_time: float = 0.0

    def check_health(self) -> AIServiceStatus:
        """Check whether local Ollama server is running and reachable."""
        import time
        now = time.time()
        if self._cached_status and (now - self._last_check_time) < 10.0:
            return self._cached_status

        try:
            url = f"{self.host}/api/tags"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                
                if not models:
                    status = AIServiceStatus(
                        is_available=False,
                        ollama_host=self.host,
                        configured_model=self.model,
                        active_models=[],
                        message="Ollama online, but no models installed. Run 'ollama pull qwen3:4b'."
                    )
                    self._cached_status = status
                    return status

                # Check if configured model or compatible model exists
                model_to_use = self.model
                model_exists = any(self.model in m or m.startswith(self.model.split(":")[0]) for m in models)
                
                if not model_exists and models:
                    model_to_use = models[0]  # Fallback to installed model (e.g. qwen2.5:1.5b)

                status = AIServiceStatus(
                    is_available=True,
                    ollama_host=self.host,
                    configured_model=model_to_use,
                    active_models=models,
                    message=f"Local Ollama online (Model '{model_to_use}' ready)"
                )
                self._cached_status = status
                self._last_check_time = now
                return status
        except Exception as e:
            status = AIServiceStatus(
                is_available=False,
                ollama_host=self.host,
                configured_model=self.model,
                active_models=[],
                message=f"Local AI offline — OCR results remain available ({str(e)})"
            )
            self._cached_status = status
            self._last_check_time = now
            return status

    def query_local_llm(self, prompt: str, schema_instruction: str = "") -> Optional[Dict[str, Any]]:
        """
        Sends prompt to local Ollama server.
        Returns parsed JSON dict if successful, or None if Ollama is offline or fails.
        """
        status = self.check_health()
        if not status.is_available:
            logger.log_step("Local AI Warning", "Ollama server offline or no models ready. Falling back to PaddleOCR + Python rules.")
            return None

        target_model = status.configured_model or self.model
        full_prompt = f"{SYSTEM_PROMPT}\n{schema_instruction}\n\nDOCUMENT OCR TEXT:\n{prompt}\n\nJSON Output:"

        payload = {
            "model": target_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }

        try:
            url = f"{self.host}/api/generate"
            req_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_bytes, headers={"Content-Type": "application/json"}, method="POST")

            with urllib.request.urlopen(req, timeout=1.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_response = result.get("response", "").strip()

                # Extract JSON block
                json_str = raw_response
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()

                return json.loads(json_str)

        except Exception as err:
            logger.log_step("Local AI Query Error", f"Ollama call error: {str(err)}. Resuming with OCR fallback.")
            return None

ai_service = LocalAIService()
