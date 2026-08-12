import re
import time
import numpy as np
import cv2
from typing import List, Dict, Any, Tuple, Optional

from backend.models.schemas import OCRResultItem, PANDetails, OCRResponse
from backend.utils.logger import logger
from backend.utils.image_processing import (
    encode_image_to_base64, 
    draw_bounding_boxes,
    enhance_image_for_ocr,
    detect_and_warp_document,
    upsample_image_for_ocr,
    assess_frame_quality,
    preprocess_document_image
)
from backend.services.metrics_service import metrics_service

class PaddleOCRService:
    def __init__(self):
        self.ocr_engine = None
        self.easyocr_reader = None
        self.engine_type = "PaddleOCR"
        self.is_initialized = False
        self._cache: Dict[str, OCRResponse] = {}

    def initialize(self):
        """Initialize OCR engines once on application startup."""
        if self.is_initialized:
            return

        logger.log_step("Server Started")
        logger.log_step("Loading OCR Engine...")

        # 1. Try EasyOCR Deep Learning Engine (PyTorch based)
        try:
            import easyocr
            logger.log_step("Initializing EasyOCR Deep Learning Engine...")
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
            self.engine_type = "PaddleOCR / EasyOCR Engine"
            logger.log_step("Deep Learning OCR Engine Loaded Successfully!")
        except Exception as e:
            logger.log_step("EasyOCR Loading Error", str(e))

        # 2. Try Native PaddleOCR with PP-OCRv5 advanced document orientation & unwarping flags
        try:
            from paddleocr import PaddleOCR
            self.ocr_engine = PaddleOCR(
                use_angle_cls=True, 
                use_doc_orientation_classify=True,
                use_doc_unwarping=True,
                use_textline_orientation=True,
                lang="en"
            )
            self.engine_type = "PaddleOCR (Native PP-OCRv5)"
            logger.log_step("Native PaddleOCR Engine Loaded with Orientation & Unwarping Flags!")
        except Exception as e:
            # Fallback if specific flags not supported in older version
            try:
                from paddleocr import PaddleOCR
                self.ocr_engine = PaddleOCR(use_angle_cls=True, lang="en")
                self.engine_type = "PaddleOCR (Native PP-OCR)"
                logger.log_step("Native PaddleOCR Engine Loaded!")
            except Exception as ex:
                logger.log_step("PaddleOCR Native Engine Unavailable", f"Reason: {str(ex)}")

        self.is_initialized = True
        metrics_service.ocr_engine_loaded = True
        metrics_service.engine_type = self.engine_type

    def _is_valid_ocr_text(self, text: str, conf: float, min_conf: float = 0.25) -> bool:
        """Filter out random noise, pixel artifacts, and low-confidence garbage text."""
        if not text or conf < min_conf:
            return False
        cleaned = text.strip()
        if len(cleaned) < 2 and not cleaned.isalnum():
            return False
        alphanumeric_count = sum(1 for c in cleaned if c.isalnum())
        if len(cleaned) > 2 and (alphanumeric_count / len(cleaned)) < 0.35:
            return False
        return True

    def _run_ocr_inference(self, img: np.ndarray) -> List[Tuple[List[List[float]], str, float]]:
        """
        Execute deep-learning OCR inference on OpenCV BGR image.
        Returns list of (bbox_points, recognized_text, confidence_score).
        Extracts 100% REAL recognized text from documents.
        """
        results: List[Tuple[List[List[float]], str, float]] = []

        # Strategy 1: EasyOCR Deep Learning Engine
        if self.easyocr_reader:
            try:
                ocr_out = self.easyocr_reader.readtext(
                    img, 
                    text_threshold=0.15, 
                    link_threshold=0.15, 
                    low_text=0.15,
                    canvas_size=1600
                )
                for item in ocr_out:
                    bbox_pts = [[float(pt[0]), float(pt[1])] for pt in item[0]]
                    text = str(item[1]).strip()
                    conf = float(item[2])
                    if self._is_valid_ocr_text(text, conf, min_conf=0.12):
                        results.append((bbox_pts, text, round(conf, 4)))
                if results:
                    return results
            except Exception as e:
                logger.log_step("EasyOCR inference error", str(e))

        # Strategy 2: Native PaddleOCR Engine
        if self.ocr_engine:
            try:
                ocr_out = self.ocr_engine.ocr(img, cls=True)
                if ocr_out and len(ocr_out) > 0 and ocr_out[0] is not None:
                    for line in ocr_out[0]:
                        bbox_pts = [[float(pt[0]), float(pt[1])] for pt in line[0]]
                        text = str(line[1][0]).strip()
                        conf = float(line[1][1])
                        if self._is_valid_ocr_text(text, conf):
                            results.append((bbox_pts, text, round(conf, 4)))
                    if results:
                        return results
            except Exception as e:
                logger.log_step("PaddleOCR inference error", str(e))

        # Strategy 3: Pytesseract Engine fallback
        try:
            import pytesseract
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = str(data['text'][i]).strip()
                conf = float(data['conf'][i]) / 100.0
                if self._is_valid_ocr_text(text, conf, min_conf=0.25):
                    x, y, w_box, h_box = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    bbox_pts = [
                        [float(x), float(y)],
                        [float(x + w_box), float(y)],
                        [float(x + w_box), float(y + h_box)],
                        [float(x), float(y + h_box)]
                    ]
                    results.append((bbox_pts, text, round(conf, 4)))
        except Exception:
            pass

        return results

    def _extract_pan_details(self, text_items: List[str]) -> PANDetails:
        """Automatically identify PAN card details (Name, Father Name, DOB, PAN Number)."""
        full_text = "\n".join(text_items).upper()
        pan_regex = r'[A-Z]{5}[0-9]{4}[A-Z]{1}'
        dob_regex = r'\b(0[1-9]|[12][0-9]|3[01])[/.-](0[1-9]|1[012])[/.-](19|20)\d\d\b'

        # 1. Search for 10-char PAN number pattern
        pan_match = re.search(pan_regex, full_text)

        # Fallback: check token by token stripping non-alphanumeric noise
        if not pan_match:
            for item in text_items:
                clean_item = re.sub(r'[^A-Z0-9]', '', item.upper())
                m = re.search(pan_regex, clean_item)
                if m:
                    pan_match = m
                    break

        # Fallback: check joined string without spaces
        if not pan_match:
            joined_clean = re.sub(r'[^A-Z0-9]', '', full_text)
            pan_match = re.search(pan_regex, joined_clean)

        # Check for PAN card indicator keywords if regex match not found directly
        has_keywords = any(kw in full_text for kw in [
            "INCOME TAX DEPARTMENT", "GOVT OF INDIA", "GOVT. OF INDIA",
            "PERMANENT ACCOUNT NUMBER", "CARD", "SIGNATURE"
        ])

        if not pan_match and not has_keywords:
            return PANDetails(is_pan_card=False)

        pan_number = pan_match.group(0) if pan_match else None

        # Clean/correct common OCR character confusions in 10-char PAN string
        if pan_number and len(pan_number) == 10:
            prefix = pan_number[:5].replace("0", "O").replace("8", "B").replace("5", "S").replace("1", "I")
            middle = pan_number[5:9].replace("O", "0").replace("D", "0").replace("B", "8").replace("S", "5").replace("I", "1").replace("L", "1")
            suffix = pan_number[9].replace("0", "O").replace("8", "B").replace("5", "S").replace("1", "I")
            pan_number = prefix + middle + suffix

        # 2. Search DOB
        dob_match = re.search(dob_regex, full_text)
        if not dob_match:
            dob_match = re.search(r'\b\d{2}[/.-]\d{2}[/.-]\d{4}\b', full_text)
        dob = dob_match.group(0) if dob_match else None

        # 3. Extract Name & Father's Name
        lines = [line.strip() for line in text_items if line.strip()]
        name = None
        father_name = None

        # Check inline regex first
        father_inline = re.search(r"(?:Father'?s?\s*Name|पिता\s*का\s*नाम)[:\s]+([A-Z\s]{3,})", full_text, re.IGNORECASE)
        if father_inline:
            father_name = father_inline.group(1).strip()

        for i, line in enumerate(lines):
            upper_line = line.upper()

            # Father's Name detection (handles 'पिता का नाम / Father's Name' header lines)
            if any(kw in upper_line for kw in ["FATHER", "PITA", "पिता"]):
                for offset in range(1, 3):
                    if i + offset < len(lines):
                        cand = lines[i + offset].strip()
                        if not re.search(r'\d', cand) and len(cand) > 2 and not any(kw in cand.upper() for kw in ["DATE", "BIRTH", "INCOME", "TAX", "GOVT", "SIGNATURE", "FATHER", "NAME", "PITA", "पिता"]):
                            if not father_name:
                                father_name = cand
                            break

            # Cardholder Name detection
            if ("NAME" in upper_line or "नाम" in line) and not any(kw in upper_line for kw in ["FATHER", "PITA", "पिता"]) and i + 1 < len(lines):
                cand = lines[i+1].strip()
                if not name and not re.search(r'\d', cand) and len(cand) > 2:
                    name = cand

        # Fallback clean lines position matching
        clean_lines = [
            l for l in lines 
            if len(l) > 2 
            and not re.search(r'\d', l) 
            and not any(kw in l.upper() for kw in ["INCOME", "TAX", "DEPARTMENT", "GOVT", "INDIA", "PERMANENT", "ACCOUNT", "NUMBER", "CARD", "SIGNATURE", "FATHER", "PITA", "पिता", "NAME", "नाम", "DATE", "BIRTH"])
        ]
        if not name and len(clean_lines) > 0:
            name = clean_lines[0]
        if not father_name and len(clean_lines) > 1:
            father_name = clean_lines[1]

        return PANDetails(
            is_pan_card=True,
            name=name or "N/A",
            father_name=father_name or "N/A",
            dob=dob or "N/A",
            pan_number=pan_number or "N/A",
            confidence=0.98 if pan_number else 0.85
        )

    def _extract_id_card_fields(self, text_items: List[str]) -> Dict[str, str]:
        """Extract key-value document attributes (Name, DOB, Blood Group, Phone, Address, STD, School)."""
        fields = {}
        full_text = "\n".join(text_items)

        # 1. School / Institution Header
        for item in text_items[:4]:
            if any(kw in item.upper() for kw in ["SCHOOL", "COLLEGE", "INSTITUTE", "UNIVERSITY", "CONVENT", "ACADEMY", "PRIMARY", "SECONDARY"]):
                fields["Institution / School"] = item
                break

        # 2. Date of Birth (D.O.B)
        dob_match = re.search(r'(?:D\.?O\.?B\.?|DATE OF BIRTH)[:\s]*([0-3]?\d[/.-][0-1]?\d[/.-](?:19|20)?\d\d)', full_text, re.IGNORECASE)
        if not dob_match:
            dob_match = re.search(r'\b(0[1-9]|[12]\d|3[01])[/.-](0[1-9]|1[0-2])[/.-](?:19|20)\d\d\b', full_text)
        if dob_match:
            fields["Date of Birth (DOB)"] = dob_match.group(1) if len(dob_match.groups()) > 0 else dob_match.group(0)

        # 3. Blood Group
        bg_match = re.search(r'BLOOD\s*GROUP[:\s]*([A-Z]{1,2}\s*[\+\-])', full_text, re.IGNORECASE)
        if not bg_match:
            bg_match = re.search(r'\b(A|B|AB|O)\s*[\+\-]\b', full_text, re.IGNORECASE)
        if bg_match:
            fields["Blood Group"] = bg_match.group(1).upper().replace(" ", "") if len(bg_match.groups()) > 0 else bg_match.group(0).upper().replace(" ", "")

        # 4. Phone / Mobile Number
        phone_match = re.search(r'(?:Ph|Phone|Mobile|Contact|Tel)[:\s]*(\+?\d{10,12})', full_text, re.IGNORECASE)
        if not phone_match:
            phone_match = re.search(r'\b[6-9]\d{9}\b', full_text)
        if phone_match:
            fields["Phone Number"] = phone_match.group(1) if len(phone_match.groups()) > 0 else phone_match.group(0)

        # 5. Address (including Aadhaar S/O, D/O, W/O, C/O and 6-digit Pincode patterns)
        addr_match = re.search(r'(?:Add|Address|S/O|D/O|W/O|C/O)[:\s]*([^\n]+)', full_text, re.IGNORECASE)
        if addr_match:
            fields["Address"] = addr_match.group(1).strip()
        else:
            pin_match = re.search(r'([^\n]+\b\d{6}\b)', full_text)
            if pin_match:
                fields["Address"] = pin_match.group(1).strip()

        # 5b. State & City
        states_list = ['Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi', 'Jammu & Kashmir', 'Ladakh', 'Chandigarh', 'Puducherry']
        for st in states_list:
            if re.search(r'\b' + re.escape(st) + r'\b', full_text, re.IGNORECASE):
                fields["State"] = st
                break
        
        dist_match = re.search(r'(?:Dist|District|City|Town)[:\s]*([A-Z\s]+)', full_text, re.IGNORECASE)
        if dist_match:
            fields["City"] = dist_match.group(1).strip()

        # 6. STD / Class
        std_match = re.search(r'STD[:\s]*([A-Z0-9\s-]+)', full_text, re.IGNORECASE)
        if std_match:
            fields["STD / Class"] = std_match.group(1).strip()

        # 7. Driver / Father / Guardian Name
        drv_match = re.search(r"(?:Driver'?s?\s*Name|Father'?s?\s*Name)[:\s]*([^\n]+)", full_text, re.IGNORECASE)
        if drv_match:
            fields["Guardian / Driver Name"] = drv_match.group(1).strip()

        # 8. Primary Name Candidate
        for line in text_items:
            clean_l = line.strip()
            if len(clean_l) > 4 and not re.search(r'\d', clean_l) and not any(kw in clean_l.upper() for kw in ["SCHOOL", "CONVENT", "ADD", "BLOOD", "STD", "DRIVER", "NAME", "PRIMARY", "SECTION"]):
                if "Cardholder Name" not in fields:
                    fields["Cardholder Name"] = clean_l
                    break

        return fields

    def _validate_ocr_fields_with_regex(self, text_items: List[str]) -> Dict[str, str]:
        r"""
        Validate extracted OCR fields using strict regex patterns:
        - PAN: [A-Z]{5}[0-9]{4}[A-Z]
        - Aadhaar: \b\d{4}\s?\d{4}\s?\d{4}\b (12 digits)
        - Dates: \b(0[1-9]|[12]\d|3[01])[/.-](0[1-9]|1[0-2])[/.-](?:19|20)?\d\d\b (DD/MM/YYYY)
        """
        validated = {}
        full_text = " ".join(text_items)

        # 1. PAN Regex
        pan_match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', full_text.upper())
        if pan_match:
            validated["Validated PAN"] = pan_match.group(0)

        # 2. Aadhaar Regex (12 digits)
        aadhaar_match = re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', full_text)
        if aadhaar_match:
            validated["Validated Aadhaar"] = aadhaar_match.group(0)

        # 3. Dates Regex (DD/MM/YYYY)
        date_matches = re.findall(r'\b(?:0[1-9]|[12]\d|3[01])[/.-](?:0[1-9]|1[0-2])[/.-](?:19|20)?\d\d\b', full_text)
        if date_matches:
            validated["Validated Date(s)"] = ", ".join(list(dict.fromkeys(date_matches)))

        return validated

    def process_image(self, img: np.ndarray, image_name: str = "Uploaded Image") -> OCRResponse:
        """
        Run high-precision OCR on OpenCV BGR image with caching, quality gating,
        preprocessing, and dictionary post-processing.
        """
        import hashlib
        start_time = time.time()

        # Step 0: Performance Optimization - Proportional Resizing for Oversized Input Frames (>1920px)
        h_orig, w_orig = img.shape[:2]
        max_dim = max(h_orig, w_orig)
        if max_dim > 1920:
            scale = 1920.0 / max_dim
            img = cv2.resize(img, (int(w_orig * scale), int(h_orig * scale)), interpolation=cv2.INTER_AREA)

        # Check Cache for identical image
        img_bytes = cv2.imencode('.jpg', img)[1].tobytes()
        img_hash = hashlib.sha256(img_bytes).hexdigest()
        if img_hash in self._cache:
            cached_res = self._cache[img_hash].model_copy()
            cached_res.processing_time = round(time.time() - start_time, 3)
            cached_res.image_name = image_name
            logger.log_step("Cache Hit", f"Returned cached OCR result for {image_name}")
            return cached_res

        # Step 1: Assess Frame Quality (Blur & Brightness & Doc Presence)
        quality = assess_frame_quality(img)
        logger.log_step("Quality Assessment", f"Blur Score: {quality['blur_score']}, Brightness: {quality['brightness']}, Doc Detected: {quality['document_detected']}")

        # Step 2: 4-Corner Document Detection & Perspective Warp
        warped_doc, was_warped = detect_and_warp_document(img)
        logger.log_step("Document Detection & Warp", f"Perspective Warped: {was_warped}")

        # Step 3 & 4: 2x High-Resolution Upscaling & Preprocessing (CLAHE, Denoising, Sharpening)
        target_doc = warped_doc if was_warped else img
        preprocessed_img = preprocess_document_image(target_doc, upscale_factor=2.0)
        logger.log_step("Preprocessing & 2x Upscaling", f"Enhanced Shape: {preprocessed_img.shape[1]}x{preprocessed_img.shape[0]}")

        # Step 5: Running Inference
        logger.log_step("Running PaddleOCR Inference...")
        best_img = preprocessed_img
        best_results = self._run_ocr_inference(preprocessed_img)

        # Fallback to target document if preprocessed yielded no boxes
        if not best_results:
            best_results = self._run_ocr_inference(target_doc)
            best_img = target_doc

        # Unmirror check for live webcam feed ONLY (never for normal uploaded document files)
        is_webcam = "webcam" in image_name.lower() or "frame_" in image_name.lower()
        if is_webcam:
            flipped_img = cv2.flip(preprocessed_img, 1)
            flipped_results = self._run_ocr_inference(flipped_img)

            pan_normal = self._extract_pan_details([res[1] for res in best_results])
            pan_flipped = self._extract_pan_details([res[1] for res in flipped_results])

            if pan_flipped.is_pan_card and not pan_normal.is_pan_card:
                best_img = flipped_img
                best_results = flipped_results
                best_pan = pan_flipped
            elif len(flipped_results) > len(best_results) + 3:
                best_img = flipped_img
                best_results = flipped_results
                best_pan = pan_flipped
            else:
                best_pan = pan_normal
        else:
            best_pan = self._extract_pan_details([res[1] for res in best_results])

        h, w, _ = best_img.shape
        raw_results = best_results

        # Dictionary / Context-based Post-Processing dictionary
        TYPO_DICTIONARY = {
            r'\bNNCOME\b': 'INCOME',
            r'\bTAX DEPARTMENI\b': 'TAX DEPARTMENT',
            r'\bDEPARTMENI\b': 'DEPARTMENT',
            r'\bGOVERNMEN1\b': 'GOVERNMENT',
            r'\bGOVT OF INDA\b': 'GOVT OF INDIA',
            r'\bPERMANEN1\b': 'PERMANENT',
            r'\bACCOUN1\b': 'ACCOUNT',
            r'\bNUMBE1\b': 'NUMBER',
            r'\bCAR1\b': 'CARD',
            r'\bSIGNATUR3\b': 'SIGNATURE',
            r'\bAADHAR\b': 'AADHAAR',
            r'\bADHAAR\b': 'AADHAAR',
            r'\bSUBTOTA1\b': 'SUBTOTAL',
            r'\bSUB TOTA1\b': 'SUB TOTAL',
            r'\bINVOIC3\b': 'INVOICE',
            r'\bDESCRIPTI0N\b': 'DESCRIPTION',
            r'\bBALANC3\b': 'BALANCE',
            r'\bRECEIP1\b': 'RECEIPT'
        }

        parsed_results: List[OCRResultItem] = []
        all_text_list: List[str] = []
        conf_sum = 0.0

        for idx, (bbox_pts, raw_txt, conf) in enumerate(raw_results):
            corrected_txt = raw_txt
            for pattern, replacement in TYPO_DICTIONARY.items():
                corrected_txt = re.sub(pattern, replacement, corrected_txt, flags=re.IGNORECASE)

            # Highlight / flag if confidence < 95% (0.95)
            is_low_conf = bool(conf < 0.95)

            item = OCRResultItem(
                id=idx + 1,
                text=corrected_txt,
                raw_text=raw_txt,
                corrected_text=corrected_txt,
                confidence=round(conf, 4),
                is_low_confidence=is_low_conf,
                coordinates=bbox_pts,
                bbox=bbox_pts
            )
            parsed_results.append(item)
            all_text_list.append(corrected_txt)
            conf_sum += conf

        processing_time = round(time.time() - start_time, 3)
        avg_conf = (conf_sum / len(parsed_results)) if parsed_results else 0.0
        memory_mb = logger.get_memory_usage_mb()

        # Step 6: Extract & Validate Fields via Regex
        extracted_fields = self._extract_id_card_fields(all_text_list)
        regex_validated = self._validate_ocr_fields_with_regex(all_text_list)
        extracted_fields.update(regex_validated)

        # Merge PAN Details if identified
        if best_pan and best_pan.is_pan_card:
            if best_pan.name and best_pan.name != "N/A":
                extracted_fields["Cardholder Name"] = best_pan.name
            if best_pan.father_name and best_pan.father_name != "N/A":
                extracted_fields["Father's Name"] = best_pan.father_name
            if best_pan.dob and best_pan.dob != "N/A":
                extracted_fields["Date of Birth"] = best_pan.dob
            if best_pan.pan_number and best_pan.pan_number != "N/A":
                extracted_fields["PAN Number"] = best_pan.pan_number

        full_text_str = "\n".join(all_text_list)

        logger.log_step("Regex Field Validation", f"Extracted Fields: {list(extracted_fields.keys())}")

        # Terminal log output
        logger.log_ocr_request(
            image_name=image_name,
            image_size=(w, h),
            text_blocks=len(parsed_results),
            ocr_time=processing_time,
            avg_confidence=avg_conf,
            memory_mb=memory_mb,
            results=[res.model_dump() for res in parsed_results]
        )

        # Generate annotated preview image on corrected cropped document image
        annotated_img = draw_bounding_boxes(best_img, [res.model_dump() for res in parsed_results])
        annotated_base64 = encode_image_to_base64(annotated_img)

        metrics_service.record_ocr_request(
            image_name=image_name,
            processing_time=processing_time,
            text_blocks=len(parsed_results),
            confidence=avg_conf
        )

        from datetime import datetime
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        response = OCRResponse(
            success=True,
            processing_time=processing_time,
            image_size=[w, h],
            results=parsed_results,
            pan_details=best_pan,
            extracted_fields=extracted_fields,
            full_text=full_text_str,
            image_name=image_name,
            detected_blocks_count=len(parsed_results),
            memory_usage_mb=round(memory_mb, 2),
            annotated_image_base64=annotated_base64,
            overall_confidence=round(avg_conf * 100, 1),
            model_version=self.engine_type,
            timestamp=current_time_str
        )

        # Limit in-memory cache to 50 items to prevent RAM bloat
        if len(self._cache) > 50:
            first_key = next(iter(self._cache))
            del self._cache[first_key]

        self._cache[img_hash] = response

        # Explicit Garbage Collection to free image buffer RAM immediately
        import gc
        del img, best_img, preprocessed_img
        gc.collect()

        return response

ocr_service = PaddleOCRService()

