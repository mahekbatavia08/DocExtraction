import time
import sys
import psutil
from datetime import datetime
from typing import List, Dict, Any

class TerminalLogger:
    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def server_started(cls, host: str, port: int):
        print(f"\n==========================================")
        print(f"[{cls._timestamp()}] [SERVER] Server Started at http://{host}:{port}")
        print(f"==========================================\n", flush=True)

    @classmethod
    def log_step(cls, step: str, details: str = ""):
        message = f"[{cls._timestamp()}] [STEP] {step}"
        if details:
            message += f" | {details}"
        try:
            print(message, flush=True)
        except UnicodeEncodeError:
            encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
            safe_msg = message.encode(encoding, errors='replace').decode(encoding, errors='replace')
            print(safe_msg, flush=True)

    @classmethod
    def log_ocr_request(
        cls, 
        image_name: str, 
        image_size: tuple, 
        text_blocks: int, 
        ocr_time: float, 
        avg_confidence: float, 
        memory_mb: float,
        results: List[Dict[str, Any]] = None
    ):
        print(f"\n------------------------------------------")
        print(f"[{cls._timestamp()}] [OCR LOG]")
        print(f"  > Image Name      : {image_name}")
        print(f"  > Image Size      : {image_size[0]}x{image_size[1]} px")
        print(f"  > Running PaddleOCR...")
        print(f"  > Detected Blocks : {text_blocks}")
        print(f"  > Processing Time : {ocr_time:.3f} sec")
        print(f"  > Avg Confidence  : {avg_confidence * 100:.1f}%")
        print(f"  > Memory Usage    : {memory_mb:.2f} MB")
        
        if results and len(results) > 0:
            print(f"  > Extracted Real Text Lines:")
            for res in results[:20]: # Print up to 20 recognized text blocks
                print(f"     [#{res.get('id')}] '{res.get('text')}' (Conf: {res.get('confidence', 0)*100:.1f}%)")
        else:
            print(f"  > Extracted Real Text Lines: None detected")

        print(f"  > Response Sent")
        print(f"------------------------------------------\n", flush=True)

    @staticmethod
    def get_memory_usage_mb() -> float:
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

logger = TerminalLogger()
