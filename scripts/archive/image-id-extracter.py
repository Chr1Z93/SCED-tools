import cv2
import os
import pytesseract
import re
import numpy as np
from PIL import Image

# CONFIGURE TESSERACT PATH (Windows Only)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

CARD_NUMBER_AREA = {"h": 0.95, "w": 0.83}
file_name = r"C:\Users\pulsc\Downloads\AHC100_SpoilerCards_Survivor_OldCompass.jpg"


def extract_card_number(image_path):
    try:
        pil_img = Image.open(image_path).convert("RGB")
        img = np.array(pil_img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    except Exception as e:
        return f"Error: {e}"

    h, w, _ = img.shape

    # Define the coordinates
    y_start = int(h * CARD_NUMBER_AREA["h"])
    x_start = int(w * CARD_NUMBER_AREA["w"])

    # Debug visualization
    debug_img = img.copy()
    cv2.rectangle(debug_img, (x_start, y_start), (w, h), (0, 255, 0), 2)

    img = img[y_start:h, x_start:w]

    # A. Grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # B. SUPER Upscale (4x) - Tiny numbers need big pixels
    img = cv2.resize(img, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)

    # C. Thresholding (Standard Binary often works better for high contrast text than Adaptive)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # D. Dilation
    # This makes the thin white text "fatter" so Tesseract can see it better.
    img = cv2.dilate(img, np.ones((3, 3), np.uint8), iterations=1)

    # E. Invert (Black text on white)
    img = cv2.bitwise_not(img)

    # OCR
    config = "--psm 7 -c tessedit_char_whitelist=0123456789abcdefgh"
    text = pytesseract.image_to_string(img, config=config)
    cleaned_text = re.sub(r'[^a-z0-9]', '', text.lower())
    match = re.search(r'(\d{2,4}[a-z]?)', cleaned_text)

    if match:
        extracted_number = match.group(0)
    else:
        extracted_number = cleaned_text # Fallback to the fully cleaned text

    if len(extracted_number) > 0:
        return extracted_number

    # Split name and extension
    base_name, _ = os.path.splitext(image_path)

    # Save ROI visualization
    roi_debug_filename = f"{base_name}_debug_roi.jpg"
    cv2.imwrite(roi_debug_filename, debug_img)
    print(f"Debug: No number detected. ROI image saved as '{roi_debug_filename}'")

    # Save processed image
    processed_debug_filename = f"{base_name}_debug_processed.jpg"
    cv2.imwrite(processed_debug_filename, img)
    print(f"Debug: Processed text image saved as '{processed_debug_filename}'")


result = extract_card_number(file_name)

print(f"Detected Number: {result}")
