# Converts images to specified resolution, file format and file size (if JPG)
# Handles CMYK and removes top row if white
# Attempts to extract card number for file name

import cv2
import os
import numpy as np
from PIL import Image
import pytesseract
import re
import sys

# Configuration
ROTATE_HORIZONTAL_IMAGES = True
OUTPUT = (750, 1050)  # width x height, use 0 to calculate automatically
MAX_FILE_SIZE_KB = 450  # only used for JPEGs
OUTPUT_FORMAT = "JPEG"  # e.g. PNG or JPEG
REMOVE_WHITE_BORDERS = True
ROW_CROP_THRESHOLD = 215
OVERRIDE = False
CARD_NUMBER_PREFIX = 12  # set to 0 to skip number extracting

# TESSERACT PATH (Windows Only)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Data
OUTPUT_LANDSCAPE = (OUTPUT[1], OUTPUT[0])
OUTPUT_PORTRAIT = OUTPUT
FILE_ENDING = {"PNG": "png", "JPEG": "jpg"}
CARD_NUMBER_AREA = {"h_start": 0.96, "h_end": 0.99, "w_start": 0.84, "w_end": 0.96}


def is_row_white(img, row_y):
    """Returns True if the entire row at coordinate Y is white."""
    width = img.width

    # Crop out just that specific 1-pixel high row
    row_img = img.crop((0, row_y, width, row_y + 1))

    # Convert to grayscale to make the check simple (0=black, 255=white)
    grayscale = row_img.convert("L")

    # getextrema returns (min_pixel_value, max_pixel_value)
    min_val, _ = grayscale.getextrema()
    return min_val > ROW_CROP_THRESHOLD


def get_unique_filename(base_path, base_name, extension):
    """Generate a unique filename by adding a numeric suffix if the file already exists."""
    counter = 1
    output_path = f"{base_path}\\{base_name}{extension}"
    while os.path.exists(output_path):
        output_path = f"{base_path}\\{base_name}_{counter}{extension}"
        counter += 1
    return output_path


def calculate_new_size(original_size, target_size):
    """Calculates new dimensions to maintain aspect ratio if one dimension is 0."""
    original_width, original_height = original_size
    target_width, target_height = target_size

    if target_width == 0 and target_height == 0:
        # No change needed
        return original_size

    if target_width == 0:
        # Calculate width based on target height
        new_width = int(original_width * target_height / original_height)
        return (new_width, target_height)

    if target_height == 0:
        # Calculate height based on target width
        new_height = int(original_height * target_width / original_width)
        return (target_width, new_height)

    # If both are specified, just return the target size as-is
    return target_size


def extract_card_number(image_path, base_name):
    pil_img = Image.open(image_path).convert("RGB")
    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    h, w, _ = img.shape

    # Define the coordinates
    y_start = int(h * CARD_NUMBER_AREA["h_start"])
    y_end = int(h * CARD_NUMBER_AREA["h_end"])
    x_start = int(w * CARD_NUMBER_AREA["w_start"])
    x_end = int(w * CARD_NUMBER_AREA["w_end"])

    # Debug visualization
    debug_img = img.copy()
    cv2.rectangle(debug_img, (x_start, y_start), (x_end, y_end), (0, 255, 0), 2)

    # Crop to ROI (Region of Interest)
    img = img[y_start:y_end, x_start:x_end]

    # Grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # SUPER Upscale (4x) - Tiny numbers need big pixels
    img = cv2.resize(img, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)

    # Thresholding (Standard Binary often works better for high contrast text than Adaptive)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Dilation (makes the thin white text "fatter" for OCR)
    img = cv2.dilate(img, np.ones((3, 3), np.uint8), iterations=1)

    # Invert (Black text on white)
    img = cv2.bitwise_not(img)

    # OCR
    config = "--psm 7 -c tessedit_char_whitelist=0123456789abcdefgh"
    text = pytesseract.image_to_string(img, config=config)
    cleaned_text = re.sub(r"[^a-z0-9]", "", text.lower())
    match = re.search(r"(\d{1,3})([a-h]?)", cleaned_text)

    if match:
        # Separate the captured groups
        number_part = match.group(1)
        suffix_part = match.group(2)

        # Pad the number part to 3 digits and combine
        extracted_number = f"{CARD_NUMBER_PREFIX}{int(number_part):03d}{suffix_part}"
    else:
        extracted_number = cleaned_text  # Fallback to the fully cleaned text

    if len(extracted_number) > 0:
        return extracted_number

    # Save ROI visualization
    roi_debug_filename = f"{base_name}_debug_roi.jpg"
    cv2.imwrite(roi_debug_filename, debug_img)
    print(f"Debug: No number detected. ROI image saved as '{roi_debug_filename}'")

    # Save processed image
    processed_debug_filename = f"{base_name}_debug_processed.jpg"
    cv2.imwrite(processed_debug_filename, img)
    print(f"Debug: Processed text image saved as '{processed_debug_filename}'")


def resize_and_compress(image_path):
    try:
        with Image.open(image_path) as img:
            # Check top row & bottom row and crop if white
            if REMOVE_WHITE_BORDERS:
                top_offset = 0
                bottom_offset = 0

                # Check Top Row (Row 0)
                if is_row_white(img, 0):
                    top_offset = 1
                    print("[INFO] Removing top white row")

                # Check Bottom Row (Row height-1)
                if is_row_white(img, img.height - 1):
                    bottom_offset = 1
                    print("[INFO] Removing bottom white row")

                if top_offset > 0 or bottom_offset > 0:
                    # Crop: (left, top, right, bottom)
                    img = img.crop(
                        (0, top_offset, img.width, img.height - bottom_offset)
                    )

            # Check the output format and convert to RGB if saving as JPEG
            if OUTPUT_FORMAT == "JPEG" and (img.mode == "RGBA" or img.mode == "CMYK"):
                img = img.convert("RGB")

            original_size = img.size

            if ROTATE_HORIZONTAL_IMAGES:
                # Calculate the final output size based on aspect ratio
                output_size = calculate_new_size(original_size, OUTPUT)

                # Rotate horizontal images 90° clockwise
                if original_size[0] > original_size[1]:
                    img = img.rotate(-90, expand=True)
            else:
                # Determine orientation and set target size accordingly
                if original_size[0] > original_size[1]:
                    output_size = calculate_new_size(original_size, OUTPUT_LANDSCAPE)
                else:
                    output_size = calculate_new_size(original_size, OUTPUT_PORTRAIT)

            # Resize image to exact dimensions (without keeping aspect ratio)
            img = img.resize(output_size, Image.Resampling.LANCZOS)

            # Define output path
            base_path = os.path.dirname(image_path)
            base_name = os.path.splitext(os.path.basename(image_path))[0]

            # Attempt to extract card number
            if OVERRIDE == False and CARD_NUMBER_PREFIX != 0:
                card_number = extract_card_number(image_path, base_name)
                if card_number:
                    base_name = card_number

            # Construct final output path
            ending = "." + FILE_ENDING[OUTPUT_FORMAT]
            if OVERRIDE:
                output_path = base_path + "\\" + base_name + ending
            else:
                output_path = get_unique_filename(base_path, base_name, ending)

            if OUTPUT_FORMAT.upper() == "PNG":
                img.save(output_path, format=OUTPUT_FORMAT)
            else:
                # Save with compression to ensure file size is under MAX_FILE_SIZE_KB
                quality = 100
                while quality > 50:
                    img.save(output_path, format=OUTPUT_FORMAT, quality=quality)
                    file_size_kb = os.path.getsize(output_path) / 1024
                    if file_size_kb <= MAX_FILE_SIZE_KB:
                        break
                    quality -= 1

            # Only perform size check for JPEG, as PNG compression is different
            if OUTPUT_FORMAT == "JPEG" and file_size_kb > MAX_FILE_SIZE_KB:
                print(f"[WARNING] Unable to compress {image_path}")
            elif OUTPUT_FORMAT == "PNG":
                file_size_kb = os.path.getsize(output_path) / 1024

            print(f"[SUCCESS] Saved {output_path} ({file_size_kb:.2f} KB)")

    except Exception as e:
        print(f"[ERROR] Failed to process {image_path}: {e}")


def process_folder(folder_path):
    """Process all image files in a folder (and its subfolders)."""
    print(f"[INFO] Processing folder: {folder_path}")

    supported_extensions = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff")

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.lower().endswith(supported_extensions):
                file_path = os.path.join(root, file_name)
                resize_and_compress(file_path)


def process_input(path):
    """Process a file or folder based on the given path."""
    # Remove leading and trailing quotes if present
    path = path.strip('"').strip("'")

    if os.path.isdir(path):
        process_folder(path)
    elif os.path.isfile(path):
        resize_and_compress(path)
    else:
        print(f"[ERROR] Invalid path: {path}")


def main():
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            process_input(path)
    else:
        user_input = input("Enter a file or folder path: ").strip()
        if user_input:
            process_input(user_input)
        else:
            print("[ERROR] No input provided. Exiting.")


if __name__ == "__main__":
    main()
    input("Press Enter to close...")
