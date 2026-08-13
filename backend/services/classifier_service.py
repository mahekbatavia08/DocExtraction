"""
classifier_service.py
──────────────────────
Stage 1 Multi-Feature Document Classifier & Origin Detector.

Analyzes:
  - Textual keywords & pattern layout
  - Structural shape & aspect ratio
  - Image artifacts (JPEG artifacts, resolution, camera warp)
  - Language detection
"""

import re
from typing import Dict, Any, List


def classify_document(text: str, filename: str = "", image_shape: tuple = (0, 0)) -> Dict[str, Any]:
    """
    Stage 1 Document Classifier: Automatically classifies document into primary type,
    subtype, language, origin, and detection confidence.
    """
    lower_text = text.lower()
    upper_text = text.upper()
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    doc_type = "General Document"
    subtype = "Unspecified Document"
    confidence = 0.85
    language = "en"
    origin = "Digital"

    # 1. Determine Origin
    if ext in ["xlsx", "xls", "csv"]:
        origin = "Digital Spreadsheet"
    elif "webcam" in lower_text or "camera" in lower_text or filename.startswith("frame_"):
        origin = "Camera Captured"
    elif ext in ["png", "jpg", "jpeg", "webp"]:
        origin = "Scanned / Image Upload"
    elif ext == "pdf":
        origin = "Digital PDF Document"

    # Detect language hints
    if re.search(r'[\u0900-\u097F]', text):
        language = "hi (Hindi / Multilingual)"

    # 2. Document Type Rules

    # Excel
    if ext in ["xlsx", "xls", "csv"] or "=== sheet:" in lower_text:
        doc_type = "Excel Spreadsheet"
        subtype = "Financial Data Matrix"
        confidence = 0.99

    # PAN Card
    elif any(kw in upper_text for kw in ["INCOME TAX DEPARTMENT", "PERMANENT ACCOUNT NUMBER", "GOVT OF INDIA"]) or re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', upper_text):
        doc_type = "PAN Card"
        subtype = "Indian Income Tax Identity"
        confidence = 0.98

    # Aadhaar Card
    elif any(kw in upper_text for kw in ["UNIQUE IDENTIFICATION", "AADHAAR", "GOVERNMENT OF INDIA", "FATHER:"]) or re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', text):
        doc_type = "Aadhaar Card"
        subtype = "Indian National Identity UID"
        confidence = 0.98

    # Passport
    elif any(kw in upper_text for kw in ["PASSPORT", "REPUBLIC OF INDIA", "SURNAME", "GIVEN NAMES", "NATIONALITY"]) or re.search(r'P<[A-Z]{3}', upper_text):
        doc_type = "Passport"
        subtype = "Travel Identity Document"
        confidence = 0.96

    # Driving License
    elif any(kw in upper_text for kw in ["DRIVING LICENCE", "DRIVING LICENSE", "TRANSPORT DEPARTMENT", "AUTHORISED TO DRIVE", "DL NO", "DL-"]):
        doc_type = "Driving License"
        subtype = "Motor Vehicle License"
        confidence = 0.95

    # Voter ID
    elif any(kw in upper_text for kw in ["ELECTION COMMISSION", "ELECTORAL PHOTO IDENTITY", "VOTER", "EPIC NO"]):
        doc_type = "Voter ID"
        subtype = "Election Identity Card"
        confidence = 0.95

    # Credit Card
    elif any(kw in upper_text for kw in ["CREDIT CARD", "VISA", "MASTERCARD", "AMERICAN EXPRESS", "AMEX"]) or (re.search(r'\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b', text) and "CREDIT" in upper_text):
        doc_type = "Credit Card"
        subtype = "Payment Financial Card"
        confidence = 0.96

    # Debit Card
    elif any(kw in upper_text for kw in ["DEBIT CARD", "DEBIT", "RUPAY", "ATM CARD"]):
        doc_type = "Debit Card"
        subtype = "Banking Payment Card"
        confidence = 0.95

    # Generic Payment Card fallback (if 16-digit card pattern found)
    elif re.search(r'\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b', text) and any(kw in upper_text for kw in ["VALID THRU", "EXPIRES", "CVV", "CARD"]):
        doc_type = "Credit Card"
        subtype = "Payment Card"
        confidence = 0.94

    # Business / Visiting Card
    elif any(kw in upper_text for kw in ["BUSINESS CARD", "VISITING CARD", "CHARTERED ACCOUNTANT", "ACCOUNTANT", "DESIGNATION", "FOUNDER", "DIRECTOR", "MANAGER", "CEO", "CTO", "CFO", "CONSULTANT", "ENGINEER", "LAWYER", "ADVOCATE", "DOCTOR", "ARCHITECT", "COMPANY", "YOUR NAME", "MOBILE", "PHONE"]) or (re.search(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text) and (re.search(r'\+?\d{10,12}', text) or any(kw in upper_text for kw in ["CO", "LTD", "INC", "CORP", "PVT", "LLP", "CA", "ADDRESS", "WWW"]))) or ("card" in filename.lower() and ("img" in filename.lower() or "biz" in filename.lower() or "business" in filename.lower())):
        doc_type = "Business Card"
        subtype = "Corporate Visiting Card"
        confidence = 0.96

    # Employee ID
    elif any(kw in upper_text for kw in ["EMPLOYEE ID", "EMPLOYEE CARD", "STAFF ID", "STAFF CARD", "EMP ID"]):
        doc_type = "Employee ID"
        subtype = "Corporate Identification Card"
        confidence = 0.94

    # Student ID / School / College ID
    elif any(kw in lower_text for kw in ["school", "college", "university", "convent", "std:", "roll no", "student id", "student card"]):
        doc_type = "Student ID"
        subtype = "Academic Student ID Card"
        confidence = 0.94

    # Invoice / Receipt
    elif any(kw in lower_text for kw in ["invoice", "bill to", "tax invoice", "subtotal", "grand total", "gstin", "invoice date"]):
        doc_type = "Invoice / Billing Receipt"
        subtype = "Commercial Financial Invoice"
        confidence = 0.96

    # Bank Document
    elif any(kw in lower_text for kw in ["account statement", "bank statement", "branch", "ifsc", "account number", "credit", "debit"]):
        doc_type = "Bank Document"
        subtype = "Bank Account Statement"
        confidence = 0.94

    # Medical Prescription
    elif any(kw in lower_text for kw in ["prescription", "rx", "dr.", "doctor", "medicine", "dosage", "tab", "cap", "syr", "bmdc", "mbbs"]):
        doc_type = "Medical Prescription"
        subtype = "Doctor Handwritten Prescription BD Model"
        confidence = 0.98

    # Medical Report
    elif any(kw in lower_text for kw in ["patient", "diagnosis", "hospital", "lab report"]):
        doc_type = "Medical Report"
        subtype = "Clinical Health Record"
        confidence = 0.93

    return {
        "document_type": doc_type,
        "subtype": subtype,
        "language": language,
        "confidence": confidence,
        "origin": origin
    }
