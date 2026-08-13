"""
config.py
─────────
System configuration and environment variable settings for Multi-Model Fallback AI System.
"""

import os

# Auto-load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

# Multi-Model Hierarchy (Environment Configurable)
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", os.getenv("OLLAMA_MODEL", "qwen2:4b"))
BACKUP_MODEL_1 = os.getenv("BACKUP_MODEL_1", "gemma3:4b")
BACKUP_MODEL_2 = os.getenv("BACKUP_MODEL_2", "llama3.2:3b")

# Validation & Execution Thresholds
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "80.0"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "2.5"))

# Azure AI Document Intelligence Credentials & Mode
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "").strip()
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "").strip()
AZURE_DOCUMENT_INTELLIGENCE_MODEL = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_MODEL", "prebuilt-read").strip()
EXTRACTION_ENGINE = os.getenv("EXTRACTION_ENGINE", "auto").strip().lower()  # 'azure', 'local', 'auto'

# ─── OpenRouter 10-Model Prescription Vision Fallback System ───────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip().rstrip("/")

PRESCRIPTION_MODEL_TIMEOUT = float(os.getenv("PRESCRIPTION_MODEL_TIMEOUT", "45"))
PRESCRIPTION_MAX_RETRIES = int(os.getenv("PRESCRIPTION_MAX_RETRIES", "1"))
PRESCRIPTION_MIN_CONFIDENCE = float(os.getenv("PRESCRIPTION_MIN_CONFIDENCE", "0.65"))
MIN_MEDICINE_CONFIDENCE = float(os.getenv("MIN_MEDICINE_CONFIDENCE", "0.65"))
MEDICINE_MIN_CONFIDENCE = float(os.getenv("MEDICINE_MIN_CONFIDENCE", os.getenv("MIN_MEDICINE_CONFIDENCE", "0.65")))

# 10 OpenRouter Vision Models Queue (Ordered by priority, preferring :free variants)
PRESCRIPTION_VISION_MODELS = [
    "nvidia/nemotron-4-340b-instruct:free",
    "qwen/qwen-2.5-vl-72b-instruct:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-3-4b-it:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
    "qwen/qwen-2.5-vl-7b-instruct:free",
    "moonshotai/kimi-vl-a3b-thinking:free",
    "google/gemma-3-27b:free",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "meta-llama/llama-3.2-90b-vision-instruct"
]

# ─── NVIDIA AI NIM Official API Services Config ──────────────────────────────
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").strip().rstrip("/")

# Official NVIDIA Nemotron / Llama Model Identifiers (Validated in NVIDIA Catalog)
NVIDIA_OCR_MODEL = os.getenv("NVIDIA_OCR_MODEL", "meta/llama-3.2-11b-vision-instruct").strip()
NVIDIA_PRIMARY_VISION_MODEL = os.getenv("NVIDIA_PRIMARY_VISION_MODEL", "meta/llama-3.2-11b-vision-instruct").strip()
NVIDIA_FALLBACK_VISION_MODEL = os.getenv("NVIDIA_FALLBACK_VISION_MODEL", "meta/llama-3.2-90b-vision-instruct").strip()



MAX_MODEL_RETRIES = int(os.getenv("MAX_MODEL_RETRIES", os.getenv("PRESCRIPTION_MAX_RETRIES", "1")))
MODEL_TIMEOUT_SECONDS = float(os.getenv("MODEL_TIMEOUT_SECONDS", os.getenv("PRESCRIPTION_MODEL_TIMEOUT", "45")))

# ─── Prescription Pipeline Mode Config ───────────────────────────────────────
# HTR_ENGINE: which engine handles the handwritten OCR branch
#   'nvidia'  → NVIDIA Nemotron-OCR-v2 (default, already configured, handles cursive)
#   'easyocr' → EasyOCR local fallback
HTR_ENGINE = os.getenv("HTR_ENGINE", "nvidia").strip().lower()

# PIPELINE_MODE: controls which high-level pipeline is run on /api/prescription/extract
#   'prescription' → new unified PrescriptionPipeline orchestrator (diagram-aligned)
#   'legacy'       → old OpenRouter 10-model queue (previous behavior)
PIPELINE_MODE = os.getenv("PIPELINE_MODE", "prescription").strip().lower()
