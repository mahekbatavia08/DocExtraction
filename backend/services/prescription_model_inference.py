"""
prescription_model_inference.py
─────────────────────────────────
Loads the trained PrescriptionCRNN .pt model and runs
inference on word-image crops to classify medicine brand names.

Used by medical_prescription_extractor.py when a trained model exists.
Falls back to fuzzy-matching if model file is not found.
"""

import os
import torch
import torch.nn as nn
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import json
from typing import Tuple, Optional

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "prescription_crnn.pt")
MODEL_PATH = os.path.normpath(MODEL_PATH)

IMG_W, IMG_H = 128, 32


class PrescriptionCRNN(nn.Module):
    """CRNN aligned with Kaggle notebook — must match training architecture exactly."""
    def __init__(self, num_classes: int, dropout: float = 0.50):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3,  32, 3, padding=1), nn.BatchNorm2d(32),  nn.ReLU(True), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64),  nn.ReLU(True), nn.MaxPool2d(2),
            nn.Conv2d(64,128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(True), nn.MaxPool2d(2),
        )
        flat = 128 * (IMG_H // 8) * (IMG_W // 8)   # 8192
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(flat, 1024), nn.ReLU(True), nn.Dropout(dropout),
            nn.Linear(1024, num_classes),
        )

    def forward(self, x):
        return self.head(self.features(x))


class PrescriptionModelInference:
    """
    Singleton inference wrapper.
    Loads once, then provides classify_word() and classify_image().
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load(self) -> bool:
        """Load model weights from disk. Returns True if successful."""
        if self._loaded:
            return True
        if not os.path.exists(MODEL_PATH):
            return False
        try:
            ckpt = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
            nc   = ckpt["num_classes"]
            dp   = ckpt.get("dropout", 0.50)
            self.model = PrescriptionCRNN(nc, dp)
            self.model.load_state_dict(ckpt["model_state"])
            self.model.eval()

            self.idx_to_class  = ckpt["idx_to_class"]
            self.medicine_db   = ckpt["medicine_db"]
            self.test_accuracy = ckpt.get("test_accuracy", 0.0)
            self.val_accuracy  = ckpt.get("val_accuracy",  0.0)
            self.top5_accuracy = ckpt.get("top5_accuracy", 0.0)
            self.macro_f1      = ckpt.get("macro_f1",      0.0)
            self._loaded       = True
            print(f"[MODEL] Prescription CRNN loaded — "
                  f"Test={self.test_accuracy*100:.1f}%  "
                  f"Val={self.val_accuracy*100:.1f}%  "
                  f"Top5={self.top5_accuracy*100:.1f}%  "
                  f"F1={self.macro_f1*100:.1f}%")
            return True
        except Exception as e:
            print(f"[MODEL] Failed to load: {e}")
            return False

    def _text_to_image(self, text: str) -> np.ndarray:
        """Render text as a 32×128 clean (no augmentation) image, normalised to [0,1]."""
        bg  = (248, 248, 248)
        img = Image.new("RGB", (IMG_W, IMG_H), bg)
        d   = ImageDraw.Draw(img)
        try:
            font_path = "C:/Windows/Fonts/calibri.ttf"
            font = ImageFont.truetype(font_path, 14) if os.path.exists(font_path) else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        try:
            bb = d.textbbox((0, 0), text, font=font)
            tw, th = bb[2]-bb[0], bb[3]-bb[1]
        except AttributeError:
            tw, th = font.getsize(text)
        x = max(1, (IMG_W - tw) // 2)
        y = max(1, (IMG_H - th) // 2)
        d.text((x, y), text, fill=(15, 15, 25), font=font)
        arr = np.array(img, dtype=np.float32) / 255.0
        return arr  # (H, W, 3)

    def classify_word(self, text: str, top_k: int = 3) -> Tuple[str, str, float, list]:
        """
        Classify a medicine brand name text word using the trained CRNN.

        Returns:
            brand       : best matching brand name
            generic     : generic name from medicine_db
            confidence  : top-1 confidence (%)
            top_k_list  : list of (brand, generic, conf%) for top_k predictions
        """
        if not self._loaded and not self.load():
            return text, "Unknown", 0.0, []

        arr    = self._text_to_image(text)
        tensor = torch.from_numpy(arr.transpose(2, 0, 1)).unsqueeze(0)  # (1,3,H,W)

        with torch.no_grad():
            logits = self.model(tensor)
            probs  = torch.softmax(logits, dim=1)[0]
            topk   = torch.topk(probs, k=min(top_k, len(probs)))

        top_k_list = []
        for idx, prob in zip(topk.indices.tolist(), topk.values.tolist()):
            brand   = self.idx_to_class[idx]
            generic = self.medicine_db.get(brand, "Unknown")
            top_k_list.append((brand, generic, round(prob * 100, 1)))

        best_brand, best_generic, best_conf = top_k_list[0]
        return best_brand, best_generic, best_conf, top_k_list

    def classify_image_array(self, img_arr: np.ndarray, top_k: int = 3) -> Tuple[str, str, float, list]:
        """
        Classify a pre-cropped image array (H×W×3, uint8 or float32).
        Automatically resizes to 32×128 if needed.
        """
        if not self._loaded and not self.load():
            return "Unknown", "Unknown", 0.0, []

        arr = img_arr.astype(np.float32)
        if arr.max() > 1.0:
            arr = arr / 255.0

        if arr.shape[:2] != (IMG_H, IMG_W):
            arr_u8 = (arr * 255).astype(np.uint8)
            arr_u8 = cv2.resize(arr_u8, (IMG_W, IMG_H))
            arr    = arr_u8.astype(np.float32) / 255.0

        if arr.ndim == 2:
            arr = np.stack([arr]*3, axis=-1)
        elif arr.shape[2] == 1:
            arr = np.repeat(arr, 3, axis=2)

        tensor = torch.from_numpy(arr.transpose(2, 0, 1)).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(tensor)
            probs  = torch.softmax(logits, dim=1)[0]
            topk   = torch.topk(probs, k=min(top_k, len(probs)))

        top_k_list = []
        for idx, prob in zip(topk.indices.tolist(), topk.values.tolist()):
            brand   = self.idx_to_class[idx]
            generic = self.medicine_db.get(brand, "Unknown")
            top_k_list.append((brand, generic, round(prob * 100, 1)))

        best_brand, best_generic, best_conf = top_k_list[0]
        return best_brand, best_generic, best_conf, top_k_list

    @property
    def is_ready(self) -> bool:
        return self._loaded

    @property
    def model_stats(self) -> dict:
        if not self._loaded:
            return {}
        return {
            "test_accuracy": round(self.test_accuracy * 100, 2),
            "val_accuracy":  round(self.val_accuracy  * 100, 2),
            "top5_accuracy": round(self.top5_accuracy * 100, 2),
            "macro_f1":      round(self.macro_f1      * 100, 2),
            "model_path":    MODEL_PATH,
        }


# Singleton
prescription_model = PrescriptionModelInference()
