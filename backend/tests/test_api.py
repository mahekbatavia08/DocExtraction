import unittest
from fastapi.testclient import TestClient
import numpy as np
import cv2
import base64

from backend.app import app

class TestBackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("ocr_engine_loaded", data)

    def test_stats_endpoint(self):
        response = self.client.get("/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_images_processed", data)
        self.assertIn("avg_processing_time", data)

    def test_webcam_endpoint(self):
        # Create a clean white canvas with high contrast bold text
        img = np.ones((400, 800, 3), dtype=np.uint8) * 255
        cv2.putText(img, "INCOME TAX DEPARTMENT", (50, 100), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 0), 3)
        cv2.putText(img, "ABCDE1234F", (50, 200), cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 0, 0), 3)
        
        _, buffer = cv2.imencode(".jpg", img)
        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

        response = self.client.post("/ocr/webcam", json={"image_base64": b64_str})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("results", data)
        self.assertIn("pan_details", data)
        # Check presence of coordinates in response
        if len(data["results"]) > 0:
            self.assertIn("coordinates", data["results"][0])
            self.assertIn("text", data["results"][0])
            self.assertIn("confidence", data["results"][0])

    def test_quality_check_endpoint(self):
        img = np.ones((400, 800, 3), dtype=np.uint8) * 255
        cv2.putText(img, "TEST QUALITY", (50, 100), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 0), 3)
        _, buffer = cv2.imencode(".jpg", img)
        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

        response = self.client.post("/ocr/quality_check", json={"image_base64": b64_str})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("is_acceptable", data)
        self.assertIn("blur_score", data)
        self.assertIn("brightness", data)

    def test_regex_validation(self):
        from backend.services.ocr_service import ocr_service
        sample_texts = [
            "GOVT OF INDIA",
            "PAN: ABCDE1234F",
            "AADHAAR: 1234 5678 9012",
            "DOB: 15/08/1995"
        ]
        validated = ocr_service._validate_ocr_fields_with_regex(sample_texts)
        self.assertEqual(validated.get("Validated PAN"), "ABCDE1234F")
        self.assertEqual(validated.get("Validated Aadhaar"), "1234 5678 9012")
        self.assertIn("15/08/1995", validated.get("Validated Date(s)", ""))

if __name__ == "__main__":
    unittest.main()
