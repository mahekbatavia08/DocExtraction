"""
ollama_service.py
──────────────────
Dedicated Ollama API Client with installed model verification, dynamic fallback support,
and clean structured JSON response extraction.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from backend.config import OLLAMA_HOST, LLM_TIMEOUT
from backend.utils.logger import logger

EXTRACTION_SYSTEM_PROMPT = """You are an expert AI document information extraction engine.
CRITICAL RULES:
1. Extract ONLY information that is explicitly present in the provided OCR text.
2. NEVER invent, infer, autocomplete, or hallucinate missing address components, names, or numbers.
3. Do NOT invent fields like street, road, house number, taluka, or village if they are not explicitly present.
4. Return the address as ONE single clean string (e.g. "12 Shanti Nagar, Surat, Gujarat - 395006").
5. Return ONLY a raw valid JSON object matching the exact requested schema. Do NOT wrap in explanation or prose.
"""

class OllamaService:
    def __init__(self):
        self.host = OLLAMA_HOST
        self._cached_models: List[str] = []
        self._last_check: float = 0.0

    def get_installed_models(self) -> List[str]:
        """Fetch list of installed models from local Ollama server (/api/tags)."""
        import time
        now = time.time()
        if self._cached_models and (now - self._last_check) < 15.0:
            return self._cached_models

        try:
            url = f"{self.host}/api/tags"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                self._cached_models = models
                self._last_check = now
                return models
        except Exception as e:
            logger.log_step("Ollama Offline Warning", f"Could not list models: {e}")
            return []

    def resolve_available_model(self, target_model: str) -> Optional[str]:
        """
        Check if target_model is installed in Ollama.
        Supports exact name (e.g. 'qwen2:4b') or family match (e.g. 'qwen3:4b' for 'qwen').
        Returns resolved model string if available, or None if not installed.
        """
        installed = self.get_installed_models()
        if not installed:
            return None

        # 1. Exact match
        for m in installed:
            if m == target_model or m.startswith(f"{target_model}:"):
                return m

        # 2. Base model name match (e.g. 'qwen' in 'qwen3:4b')
        base_name = target_model.split(":")[0].split("-")[0].lower()
        for m in installed:
            if base_name in m.lower():
                return m

        return None

    def query_model(self, model_name: str, ocr_text: str, schema_instruction: str = "") -> Optional[Dict[str, Any]]:
        """
        Queries Ollama with specified model_name.
        Returns parsed JSON dict, or None if call fails, times out, or produces unparseable output.
        """
        resolved_model = self.resolve_available_model(model_name)
        if not resolved_model:
            logger.log_step("Model Bypass", f"Model '{model_name}' is not installed in Ollama. Skipping.")
            return None

        full_prompt = (
            f"{EXTRACTION_SYSTEM_PROMPT}\n"
            f"{schema_instruction}\n\n"
            f"PROVIDED DOCUMENT OCR TEXT:\n{ocr_text}\n\n"
            f"JSON Output:"
        )

        payload = {
            "model": resolved_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.9
            }
        }

        try:
            url = f"{self.host}/api/generate"
            req_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_bytes, headers={"Content-Type": "application/json"}, method="POST")

            with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_response = result.get("response", "").strip()

                if not raw_response:
                    return None

                # Clean markdown backticks if returned
                json_str = raw_response
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()

                # Parse JSON
                parsed_json = json.loads(json_str)
                if isinstance(parsed_json, dict):
                    return parsed_json
                return None

        except Exception as err:
            logger.log_step("Model Query Error", f"Model '{model_name}' query error: {err}")
            return None

ollama_service = OllamaService()
