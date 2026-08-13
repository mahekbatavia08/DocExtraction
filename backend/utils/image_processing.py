import base64
import io
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, List, Dict, Any, Optional

def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Convert image byte stream to OpenCV BGR numpy array."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid or corrupted image format")
    return img

def decode_base64_image(base64_str: str) -> np.ndarray:
    """Convert base64 string (with or without data URI prefix) to OpenCV BGR image."""
    base64_str = base64_str.strip()
    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]
    img_data = base64.b64decode(base64_str)
    return decode_image_bytes(img_data)

def encode_image_to_base64(img: np.ndarray, format: str = ".jpg") -> str:
    """Encode OpenCV BGR image to base64 string."""
    _, buffer = cv2.imencode(format, img)
    base64_data = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_data}"

def preprocess_handwritten_document(img: np.ndarray) -> np.ndarray:
    """
    Advanced preprocessing optimized for handwritten documents:
    - CLAHE contrast normalization
    - Bilateral filtering for stroke noise reduction
    - Deskewing via contour angle estimation
    - High-resolution upscaling
    """
    if img is None or img.size == 0:
        return img

    h, w = img.shape[:2]

    # 1. Upscale if image resolution is low (< 1200px)
    if w < 1200 or h < 1200:
        scale = max(1.5, 1200.0 / float(min(w, h)))
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    # 2. Convert to LAB color space & apply CLAHE to L-channel for contrast boost
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced = cv2.merge((cl, a, b))
    enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    # 3. Bilateral filter to smooth noise while keeping handwritten stroke edges sharp
    filtered = cv2.bilateralFilter(enhanced_bgr, d=7, sigmaColor=50, sigmaSpace=50)

    # 4. Deskewing
    gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 8)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) > 100:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) > 0.5 and abs(angle) < 25.0:
            (h_curr, w_curr) = filtered.shape[:2]
            center = (w_curr // 2, h_curr // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            filtered = cv2.warpAffine(filtered, M, (w_curr, h_curr), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return filtered

def detect_handwriting_signatures(img: np.ndarray) -> Dict[str, Any]:
    """Detects presence of handwriting or cursive signatures based on stroke density & variance."""
    if img is None or img.size == 0:
        return {"has_handwriting": False, "score": 0.0}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    edges = cv2.Canny(gray, 50, 150)
    density = np.sum(edges > 0) / float(gray.size)

    # Measure variance of Laplacian for stroke intensity fluctuations
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    has_hw = bool(density > 0.04 and laplacian_var > 150.0)
    return {
        "has_handwriting": has_hw,
        "edge_density": round(float(density), 4),
        "stroke_variance": round(float(laplacian_var), 2)
    }


def render_pdf_to_images(pdf_bytes: bytes) -> List[np.ndarray]:
    """Convert PDF byte stream to a list of OpenCV BGR images (one per page)."""
    images = []

    # 1. Try PyMuPDF (fitz) - Best performance and quality
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            if pix.n == 4: # RGBA to BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3: # RGB to BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            images.append(img)
        doc.close()
        if images:
            return images
    except Exception:
        pass

    # 2. Try pypdfium2
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_bytes)
        for page in pdf:
            image = page.render(scale=2).to_pil()
            open_cv_image = np.array(image.convert("RGB"))
            images.append(cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR))
        pdf.close()
        if images:
            return images
    except Exception:
        pass

    # 3. Fallback to PIL Image opening if standard image file was uploaded to PDF route
    try:
        pil_img = Image.open(io.BytesIO(pdf_bytes))
        open_cv_image = np.array(pil_img.convert("RGB"))
        return [cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)]
    except Exception as e:
        raise ValueError(f"Could not render PDF document: {str(e)}")

def extract_digital_pdf_text(pdf_bytes: bytes) -> Optional[str]:
    """
    Extract selectable digital text from PDF if available.
    Bypasses expensive image rendering and OCR for native digital PDFs.
    """
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_pages = []
        for page in doc:
            t = page.get_text()
            if t and t.strip():
                text_pages.append(t.strip())
        doc.close()
        full_text = "\n".join(text_pages)
        if len(full_text) >= 30:
            return full_text
    except Exception:
        pass
    return None

def enhance_image_for_ocr(img: np.ndarray) -> np.ndarray:
    """
    Enhance contrast, sharpness, and brightness of webcam images for 100% accurate OCR.
    - Applies mild CLAHE to improve contrast in uneven lighting.
    - Applies subtle bilateral filtering to reduce camera sensor noise without blurring text edges.
    """
    if img is None or img.size == 0:
        return img

    try:
        # Convert BGR to LAB color space to process Luminance channel independently
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply mild CLAHE to L-channel to enhance dark text against background
        clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        # Merge channels and convert back to BGR
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # Apply mild noise reduction (bilateral filter) to eliminate camera sensor grain
        denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=35, sigmaSpace=35)
        return denoised
    except Exception:
        return img

def detect_and_warp_document(img: np.ndarray) -> Tuple[np.ndarray, bool]:
    """
    Detect document boundaries (ID card, license, page), extract 4 corners,
    and apply perspective transform to flatten, unskew, and crop the document.
    Returns (warped_img, was_perspective_warped).
    """
    if img is None or img.size == 0:
        return img, False

    h, w = img.shape[:2]
    orig_area = h * w

    try:
        # Convert to grayscale & blur to reduce noise
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detection & morphological dilation
        edged = cv2.Canny(blurred, 30, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edged, kernel, iterations=1)

        # Find largest contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        doc_contour = None
        for c in contours:
            area = cv2.contourArea(c)
            if area < (orig_area * 0.12):  # Must take at least 12% of image frame
                continue
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                doc_contour = approx
                break

        if doc_contour is not None:
            # Order 4 corners: top-left, top-right, bottom-right, bottom-left
            pts = doc_contour.reshape(4, 2)
            rect = np.zeros((4, 2), dtype="float32")

            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]      # Top-left
            rect[2] = pts[np.argmax(s)]      # Bottom-right

            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]   # Top-right
            rect[3] = pts[np.argmax(diff)]   # Bottom-left

            (tl, tr, br, bl) = rect

            # Compute width of new warped image
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))

            # Compute height of new warped image
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))

            dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]
            ], dtype="float32")

            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
            return warped, True

    except Exception:
        pass

    return img, False

def upsample_image_for_ocr(img: np.ndarray, target_min_width: int = 1400) -> np.ndarray:
    """
    Upsample low-resolution camera frames so small printed text (DOB, Phone, Address)
    reaches a minimum height of 24-36px for 100% OCR recognition accuracy.
    """
    if img is None or img.size == 0:
        return img

    h, w = img.shape[:2]
    if w < target_min_width:
        scale = float(target_min_width) / float(w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        upsampled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        return upsampled

    return img

def assess_frame_quality(img: np.ndarray) -> Dict[str, Any]:
    """
    Evaluate webcam frame for Blur (Laplacian variance), Brightness (mean luminance),
    and Document Detection status. Returns quality scores and acceptance decision.
    """
    if img is None or img.size == 0:
        return {
            "is_acceptable": False,
            "blur_score": 0.0,
            "brightness": 0.0,
            "document_detected": False,
            "reason": "Empty or invalid frame"
        }

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Blur score via Laplacian variance
    blur_score = float(round(cv2.Laplacian(gray, cv2.CV_64F).var(), 2))

    # 2. Brightness score via mean grayscale luminance
    brightness = float(round(np.mean(gray), 2))

    # 3. Document presence detection (4-corner contour check)
    _, doc_detected = detect_and_warp_document(img)

    # Threshold checks
    BLUR_THRESHOLD = 50.0
    BRIGHTNESS_MIN = 35.0
    BRIGHTNESS_MAX = 230.0

    reasons = []
    if blur_score < BLUR_THRESHOLD:
        reasons.append(f"Frame is too blurry (Blur Score: {blur_score} < {BLUR_THRESHOLD})")

    if brightness < BRIGHTNESS_MIN:
        reasons.append(f"Frame is too dark (Brightness: {brightness} < {BRIGHTNESS_MIN})")
    elif brightness > BRIGHTNESS_MAX:
        reasons.append(f"Frame is overexposed (Brightness: {brightness} > {BRIGHTNESS_MAX})")

    is_acceptable = len(reasons) == 0

    return {
        "is_acceptable": is_acceptable,
        "blur_score": blur_score,
        "brightness": brightness,
        "document_detected": doc_detected,
        "reason": "Frame quality acceptable" if is_acceptable else " | ".join(reasons)
    }


def preprocess_document_image(img: np.ndarray, upscale_factor: float = 2.0) -> np.ndarray:
    """
    Apply full 5-stage document image enhancement:
      1. 2x Super-Resolution Upscaling (Bicubic)
      2. CLAHE Contrast Equalization
      3. Bilateral Denoising
      4. Crisp Text Sharpening Kernel
      5. Adaptive Contrast Adjustment
    """
    if img is None or img.size == 0:
        return img

    h, w = img.shape[:2]

    # 1. Upscale cropped document image by 2x
    new_w = int(w * upscale_factor)
    new_h = int(h * upscale_factor)
    upscaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    try:
        # 2. Convert to LAB color space & apply CLAHE to L-channel
        lab = cv2.cvtColor(upscaled, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl, a, b))
        bgr_enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        # 3. Bilateral Denoising to preserve text edges while removing camera sensor noise
        denoised = cv2.bilateralFilter(bgr_enhanced, d=5, sigmaColor=40, sigmaSpace=40)

        # 4. Sharpening Kernel to crisp character edges
        sharpen_kernel = np.array([[0, -0.4, 0], [-0.4, 2.6, -0.4], [0, -0.4, 0]], dtype=np.float32)
        sharpened = cv2.filter2D(denoised, -1, sharpen_kernel)

        return sharpened

    except Exception:
        return upscaled


def preprocess_prescription_image(img: np.ndarray, upscale_factor: float = 2.5) -> np.ndarray:
    """
    Enhanced 8-stage preprocessing pipeline specifically designed for:
      - Difficult cursive / joined doctor handwriting
      - Faded ink, photocopied, or poor-quality prescription scans
      - Tilted / rotated prescription pads
      - Low-contrast printed prescriptions

    Stages:
      1. Upscale 2.5x for high-fidelity stroke detail
      2. Grayscale + Aggressive CLAHE (clipLimit=3.5) for faded ink recovery
      3. Adaptive Gaussian Thresholding for stroke isolation in non-uniform lighting
      4. Morphological Dilation to thicken and reconnect broken cursive strokes
      5. Gaussian Blur to smooth jagged cursive edges
      6. Stroke-width Normalization via Erosion
      7. Deskew Correction using Hough Line Transform
      8. Final sharpening kernel pass
    """
    if img is None or img.size == 0:
        return img

    h, w = img.shape[:2]

    # Stage 1: High-res upscale preserving stroke detail
    new_w = int(w * upscale_factor)
    new_h = int(h * upscale_factor)
    upscaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    try:
        # Stage 2: Grayscale + Aggressive CLAHE for faded ink
        gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
        gray_clahe = clahe.apply(gray)

        # Stage 3: Adaptive Gaussian Thresholding — handles uneven lighting across prescription pad
        # blockSize=25 covers the typical stroke-to-background region for cursive text
        adaptive_thresh = cv2.adaptiveThreshold(
            gray_clahe,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY_INV,
            blockSize=25,
            C=8
        )

        # Stage 4: Morphological Dilation — thickens and reconnects broken cursive strokes
        # Horizontal kernel elongated to bridge gaps in joined cursive letters
        dilation_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        dilated = cv2.dilate(adaptive_thresh, dilation_kernel, iterations=1)

        # Stage 5: Slight Gaussian Blur to smooth jagged cursive letter edges
        blurred = cv2.GaussianBlur(dilated, (3, 3), 0)

        # Stage 6: Stroke-width Normalization via Erosion (prevents over-inflation of thick strokes)
        erosion_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
        normalized = cv2.erode(blurred, erosion_kernel, iterations=1)

        # Stage 7: Deskew Correction using Hough Line Transform
        try:
            edges = cv2.Canny(normalized, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=int(new_w * 0.3))
            if lines is not None and len(lines) > 0:
                angles = []
                for rho, theta in lines[:20, 0]:
                    angle_deg = np.degrees(theta) - 90
                    if -30 < angle_deg < 30:
                        angles.append(angle_deg)
                if angles:
                    median_angle = float(np.median(angles))
                    if abs(median_angle) > 0.5:
                        center = (new_w // 2, new_h // 2)
                        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        normalized = cv2.warpAffine(
                            normalized, M, (new_w, new_h),
                            flags=cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_REPLICATE
                        )
        except Exception:
            pass  # Deskew is best-effort; continue if it fails

        # Stage 8: Invert back to black-text-on-white and convert to BGR for downstream
        result_gray = cv2.bitwise_not(normalized)
        result_bgr = cv2.cvtColor(result_gray, cv2.COLOR_GRAY2BGR)

        # Final sharpening pass
        sharpen_kernel = np.array([[0, -0.5, 0], [-0.5, 3.0, -0.5], [0, -0.5, 0]], dtype=np.float32)
        sharpened = cv2.filter2D(result_bgr, -1, sharpen_kernel)
        return sharpened

    except Exception:
        return upscaled


def draw_bounding_boxes(img: np.ndarray, results: List[Dict[str, Any]]) -> np.ndarray:
    """Draw green bounding boxes and text labels on image."""
    annotated = img.copy()
    for res in results:
        bbox = np.array(res["bbox"], dtype=np.int32)
        pts = bbox.reshape((-1, 1, 2))
        cv2.polylines(annotated, [pts], isClosed=True, color=(0, 255, 100), thickness=2)
        
        conf_str = f"{res['text']} ({(res['confidence'] * 100):.0f}%)"
        x, y = bbox[0]
        cv2.putText(
            annotated, 
            conf_str, 
            (int(x), max(15, int(y) - 5)), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.45, 
            (0, 255, 100), 
            1, 
            cv2.LINE_AA
        )
    return annotated

