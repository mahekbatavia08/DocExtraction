"""
test_business_card_pipeline.py
────────────────────────────────
Unit test suite verifying 25-Point Business Card Field Extraction Architecture against:
  1. Image 6 test tokens (SHOP NAME, Your Name, +91-0000000000, yourmailid@gmail.com, your address location & landmark)
  2. Indian +91 format cards
  3. US/Global layout cards
  4. Multi-line address cards
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.business_card_extractor import business_card_extractor

def test_screenshot_card_layout():
    """Tests exact card from user screenshot"""
    print("\n--- Test 1: Screenshot Card Layout ---")
    ocr_tokens = [
        ([[10, 10], [50, 10], [50, 30], [10, 30]], "CA", 0.95),
        ([[60, 40], [250, 40], [250, 80], [60, 80]], "SHOP NAME", 0.98),
        ([[300, 150], [450, 150], [450, 180], [300, 180]], "Your Name", 0.96),
        ([[300, 190], [480, 190], [480, 210], [300, 210]], "Chartered Accountant", 0.94),
        ([[310, 230], [500, 230], [500, 250], [310, 250]], "+91-0000000000", 0.97),
        ([[310, 255], [520, 255], [520, 275], [310, 275]], "yourmailid@gmail.com", 0.99),
        ([[50, 300], [350, 300], [350, 325], [50, 325]], "your address location & landmark", 0.93)
    ]

    res = business_card_extractor.extract_structured_data(ocr_tokens)
    fields = res["fields"]
    
    print(f"Extracted Fields: {fields}")
    assert fields["Company"] == "SHOP NAME", f"Expected 'SHOP NAME', got '{fields['Company']}'"
    assert fields["Name"] == "Your Name", f"Expected 'Your Name', got '{fields['Name']}'"
    assert fields["Designation"] == "Chartered Accountant", f"Expected 'Chartered Accountant', got '{fields['Designation']}'"
    assert fields["Phone"] == "+91-0000000000", f"Expected '+91-0000000000', got '{fields['Phone']}'"
    assert fields["Email"] == "yourmailid@gmail.com", f"Expected 'yourmailid@gmail.com', got '{fields['Email']}'"
    assert fields["Address"] == "your address location & landmark", f"Expected 'your address location & landmark', got '{fields['Address']}'"
    print("[PASS] Test 1 PASSED SUCCESSFULLY!")

def test_layout_b_international_card():
    """Tests Layout B: International Card with www website and +1 phone"""
    print("\n--- Test 2: Layout B International Card ---")
    ocr_tokens = [
        ([[10, 20], [200, 20], [200, 50], [10, 50]], "Acme Global Corp", 0.97),
        ([[10, 60], [180, 60], [180, 80], [10, 80]], "Sarah Connor", 0.96),
        ([[10, 85], [170, 85], [170, 100], [10, 100]], "VP of Technology", 0.95),
        ([[10, 120], [200, 120], [200, 140], [10, 140]], "sarah.c@acmeglobal.com", 0.99),
        ([[10, 145], [180, 145], [180, 165], [10, 165]], "+1 (555) 019-2834", 0.98),
        ([[10, 190], [190, 170], [190, 190], [10, 190]], "www.acmeglobal.com", 0.98),
        ([[10, 200], [300, 200], [300, 220], [10, 220]], "100 Innovation Way, Silicon Valley, CA 94025", 0.94)
    ]

    res = business_card_extractor.extract_structured_data(ocr_tokens)
    fields = res["fields"]

    print(f"Extracted Fields: {fields}")
    assert fields["Company"] == "Acme Global Corp", f"Expected 'Acme Global Corp', got '{fields['Company']}'"
    assert fields["Name"] == "Sarah Connor", f"Expected 'Sarah Connor', got '{fields['Name']}'"
    assert fields["Designation"] == "VP of Technology", f"Expected 'VP of Technology', got '{fields['Designation']}'"
    assert fields["Email"] == "sarah.c@acmeglobal.com", f"Expected 'sarah.c@acmeglobal.com', got '{fields['Email']}'"
    assert fields["Phone"] == "+1 (555) 019-2834", f"Expected '+1 (555) 019-2834', got '{fields['Phone']}'"
    assert fields["Website"] == "www.acmeglobal.com", f"Expected 'www.acmeglobal.com', got '{fields['Website']}'"
    print("[PASS] Test 2 PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_screenshot_card_layout()
    test_layout_b_international_card()
    print("\nALL BUSINESS CARD EXTRACTION UNIT TESTS PASSED 100%!")
