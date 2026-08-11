"""
config.py
─────────
System configuration and environment variable settings for Multi-Model Fallback AI System.
"""

import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

# Multi-Model Hierarchy (Environment Configurable)
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", os.getenv("OLLAMA_MODEL", "qwen2:4b"))
BACKUP_MODEL_1 = os.getenv("BACKUP_MODEL_1", "gemma3:4b")
BACKUP_MODEL_2 = os.getenv("BACKUP_MODEL_2", "llama3.2:3b")

# Validation & Execution Thresholds
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "80.0"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "2.5"))
