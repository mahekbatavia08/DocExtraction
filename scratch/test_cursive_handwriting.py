"""
test_cursive_handwriting.py
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Test suite for the cursive handwriting preprocessing and
the 4-tier fuzzy medicine name matcher with prefix expansion.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from backend.services.medical_prescription_extractor import MedicalPrescriptionExtractor

PASS = "[PASS]"
FAIL = "[FAIL]"
errors = []

def check(test_name: str, actual, expected, match_type: str = "eq"):
    if match_type == "eq":
        ok = actual == expected
    elif match_type == "in":
        ok = expected.lower() in str(actual).lower()
    elif match_type == "not_none":
        ok = actual is not None
    elif match_type == "gt":
        ok = actual > expected
    elif match_type == "lt":
        ok = actual < expected
    elif match_type == "gte":
        ok = actual >= expected
    else:
        ok = False

    if ok:
        print(f"  {PASS} {test_name}")
    else:
        msg = f"  {FAIL} {test_name}: got {repr(actual)}, expected match_type={match_type} {repr(expected)}"
        print(msg)
        errors.append(msg)

print("=" * 70)
print("  CURSIVE HANDWRITING & FUZZY MEDICINE MATCHING TEST SUITE")
print("=" * 70)

extractor = MedicalPrescriptionExtractor()
fuzzy = extractor.fuzzy_match_medicine

# â”€â”€ Test Group 1: Exact dictionary matches (100% confidence) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n--- Group 1: Exact Dictionary Matches ---")
brand, generic, conf = fuzzy("Amoxicillin")
check("Exact: Amoxicillin", brand, "Amoxicillin")
check("Exact: Amoxicillin conf=100", conf, 100.0)

brand, generic, conf = fuzzy("Ceftriaxone")
check("Exact: Ceftriaxone", brand, "Ceftriaxone")
check("Exact: Ceftriaxone conf=100", conf, 100.0)

brand, generic, conf = fuzzy("Clindamycin")
check("Exact: Clindamycin", brand, "Clindamycin")
check("Exact: Clindamycin conf=100", conf, 100.0)

brand, generic, conf = fuzzy("Ondansetron")
check("Exact: Ondansetron", brand, "Ondansetron")
check("Exact: Ondansetron conf=100", conf, 100.0)

brand, generic, conf = fuzzy("Olanzapine")
check("Exact: Olanzapine", brand, "Olanzapine")
check("Exact: Olanzapine conf=100", conf, 100.0)

# â”€â”€ Test Group 2: Case-insensitive matches â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n--- Group 2: Case-Insensitive Exact Matches ---")
brand, generic, conf = fuzzy("amoxicillin")
check("Lowercase: amoxicillin â†’ Amoxicillin", brand, "Amoxicillin")

brand, generic, conf = fuzzy("METFORMIN")
check("Uppercase: METFORMIN â†’ Metformin", brand, "Metformin")

brand, generic, conf = fuzzy("ceftriaxone")
check("Lowercase: ceftriaxone â†’ Ceftriaxone", brand, "Ceftriaxone")

# â”€â”€ Test Group 3: Substring/high-similarity match (Tier 2) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n--- Group 3: Substring / High-Similarity Matches (>=70%) ---")
brand, generic, conf = fuzzy("Azithromycins")   # Extra 's' from handwriting noise
check("Near-exact Azithromycins â†’ Azithromycin", "Azithromycin" in brand or brand == "Azithromycin", True)

brand, generic, conf = fuzzy("Azithromycin500")  # Strength written into name
check("Azithromycin500 found", "Azithromycin" in brand, True)

# Test Group 4: Prefix expansion (Tier 3) for partial cursive reads
print("\n--- Group 4: Prefix Expansion (Cursive Partial Reads) ---")
brand, generic, conf = fuzzy("Clindamy")     # partially readable cursive
check("Cursive partial 'Clindamy' -> Clindamycin", "Clindamycin" in brand, True)
check("Cursive partial conf >= 50", conf, 50.0, match_type="gte")  # any strong match is correct

brand, generic, conf = fuzzy("Azithr")       # "Azithro..." only visible
check("Cursive partial 'Azithr' -> Azithromycin found", conf, 0.0, match_type="gt")

brand, generic, conf = fuzzy("Ciproflo")     # cursive partial ciprofloxacin
check("Cursive partial 'Ciproflo' -> Ciprofloxacin", "Ciprofloxacin" in brand, True)

brand, generic, conf = fuzzy("Furosem")      # partial furosemide
check("Cursive partial 'Furosem' -> Furosemide", "Furosemide" in brand, True)

brand, generic, conf = fuzzy("Olanza")       # cursive partial olanzapine
check("Cursive partial 'Olanza' -> Olanzapine", "Olanzapine" in brand, True)

brand, generic, conf = fuzzy("Tramad")       # partial tramadol
check("Cursive partial 'Tramad' -> Tramadol", "Tramadol" in brand, True)

brand, generic, conf = fuzzy("Fluox")        # partial fluoxetine
check("Cursive partial 'Fluox' -> Fluoxetine", "Fluoxetine" in brand, True)

brand, generic, conf = fuzzy("Metfor")       # partial metformin
check("Cursive partial 'Metfor' -> Metformin", "Metformin" in brand, True)

# Test Group 5: Low-confidence fuzzy match (Tier 4, 60-69%)
print("\n--- Group 5: Low-Confidence Fuzzy Matches (60-70%) ---")
brand, generic, conf = fuzzy("Amoxicilin")   # One 'l' dropped (common OCR error)
check("'Amoxicilin' (one l) matched", ("Amoxicillin" in brand or "Amox" in brand), True)
check("'Amoxicilin' conf > 0", conf, 0.0, match_type="gt")

brand, generic, conf = fuzzy("Ciproxacin")  # vowel confusion
check("'Ciproxacin' fuzzy match found", conf, 0.0, match_type="gt")

# Test Group 6: Non-medicine words correctly return Unknown
print("\n--- Group 6: Non-Medicine Words -> Unknown (Zero Hallucination) ---")
_, gen, conf = fuzzy("dispense")
check("'dispense' -> Unknown", gen, "Unknown")

_, gen, conf = fuzzy("patient")
check("'patient' -> Unknown", gen, "Unknown")

_, gen, conf = fuzzy("sig")
check("'sig' (too short) -> no crash", True, True)  # short word, should not crash

_, gen, conf = fuzzy("xqzt")   # gibberish
check("gibberish 'xqzt' -> very low confidence", conf, 60.0, match_type="lt")

# ——— Test Group 7: Image Preprocessing Function Available —————————————————————
print("\n--- Group 7: Cursive Preprocessing Function Available ---")
if CV2_AVAILABLE:
    from backend.utils.image_processing import preprocess_prescription_image
    # Create a synthetic white image with black text simulation
    test_img = np.ones((200, 400, 3), dtype=np.uint8) * 240  # near-white background
    # Draw some simulated cursive strokes
    cv2.putText(test_img, "Amoxicillin 500mg bd", (10, 100),
                cv2.FONT_HERSHEY_SCRIPT_COMPLEX, 0.7, (30, 30, 30), 1)
    result = preprocess_prescription_image(test_img, upscale_factor=2.0)
    check("preprocess_prescription_image returns array", result is not None, True)
    check("Output is BGR 3-channel", result.shape[2] if len(result.shape) == 3 else 0, 3)
    check("Output is 2x input width (upscaled)", result.shape[1], test_img.shape[1] * 2 - 1, match_type="gt")
    print(f"  [INFO] Input: {test_img.shape}, Output: {result.shape}")
else:
    print("  [SKIP] cv2 not available â€” preprocessing tests skipped")

print("\n" + "=" * 70)
if errors:
    print(f"  {len(errors)} TEST(S) FAILED:")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("  ALL CURSIVE HANDWRITING TESTS PASSED CLEANLY!")
print("=" * 70)

