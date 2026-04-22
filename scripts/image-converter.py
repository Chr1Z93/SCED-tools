# Converts images to specified resolution, file format and file size (if JPG/WEBP)
# Handles CMYK and removes borders if white
# Attempts to extract card number for file name

import cv2
import os
import numpy as np
from PIL import Image
import platform
import pytesseract
import re
import sys
from PIL import Image, ImageCms, ImageEnhance, ImageOps

# --------------------------------
# Configuration
# --------------------------------

# General
ROTATE_HORIZONTAL_IMAGES = True
OUTPUT = (750, 1050)  # width x height, use 0 to calculate automatically
MAX_FILE_SIZE_KB = 450  # used for JPEG and WEBP
OUTPUT_FORMAT = "WEBP"  # e.g. PNG or JPEG or WEBP
OVERRIDE_EXISTING_FILES = False
OUTPUT_FOLDER = r""  # Use "" (empty string) to save in the same folder as the source

# Image cropping
REMOVE_WHITE_BORDERS = False
WHITE_THRESHOLD = 215  # How "white" a row/column must be to be cropped (0-255)
MAX_CROP_LIMIT = 25 #  How many pixels can be removed automatically at maximum
FIXED_CROP_OFFSETS = None  # (left, top, right, bottom) pixels to remove from each side (after rotation)
CROP_TO_OUTPUT_SIZE = False # Images will be cropped instead of scaled to fit output

# Image enhancing
COLOR_BOOST = 1.0  # Default 1.0
CONTRAST_BOOST = 1.0  # Default 1.0
BRIGHTNESS_BOOST = 1.0  # Default 1.0
AUTO_CONTRAST = False

# Card Number Extracting (via Tesseract - Windows Only)
EXTRACT_CARD_NUMBER = False
CARD_NUMBER_START = 12001
CARD_NUMBER_AREA = {"h_start": 0.967, "h_end": 0.995, "w_start": 0.85, "w_end": 0.95}
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --------------------------------
# Data
# --------------------------------

OUTPUT_LANDSCAPE = (OUTPUT[1], OUTPUT[0])
OUTPUT_PORTRAIT = OUTPUT
FILE_ENDING = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}
PLATFORM = platform.system()


def safe_convert_to_rgb(img):
    if img.mode == "CMYK":
        try:
            cmyk_profile = "CGATS21_CRPC7.icc"
            srgb_profile = "sRGB_ICC_v4_Appearance.icc"

            # Attempt the high-quality conversion
            converted = ImageCms.profileToProfile(
                img,
                cmyk_profile,
                srgb_profile,
                outputMode="RGB",
            )

            # If the tool returned something valid, use it
            if converted:
                return converted

        except Exception as e:
            print(f"[INFO] ICC Profile conversion failed, using basic conversion: {e}")
            # If it fails (e.g. profile files not found), it falls through to the line below

    # Handles non-CMYK images and CMYK images where the profile conversion failed.
    return img.convert("RGB")


def get_content_box(img):
    """
    Scans from all sides to find the first non-white content.
    Returns (left, top, right, bottom) and the offsets.
    """
    # Convert to grayscale to find 'white' more accurately
    gray = img.convert("L")
    np_img = np.array(gray)

    # Mask of pixels that are NOT white
    mask = np_img < WHITE_THRESHOLD
    coords = np.argwhere(mask)

    if coords.size == 0:
        return None, None

    # Find the bounding box of the content
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0) + 1

    # Calculate how many pixels we are removing from each side
    offsets = {
        "left": x0,
        "top": y0,
        "right": img.width - x1,
        "bottom": img.height - y1,
    }

    return (x0, y0, x1, y1), offsets


def get_unique_filename(base_path, base_name, extension):
    """Generate a unique filename by adding a numeric suffix if the file already exists."""
    counter = 1
    output_path = os.path.join(base_path, f"{base_name}{extension}")
    while os.path.exists(output_path):
        output_path = os.path.join(base_path, f"{base_name}_{counter}{extension}")
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


def extract_card_number(img, image_path, debug_save_path):
    img = np.array(img.copy().convert("RGB"))
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
        combined_number = CARD_NUMBER_START - 1 + int(number_part)
        extracted_number = f"{combined_number:05d}{suffix_part}"
    else:
        extracted_number = cleaned_text  # Fallback to the fully cleaned text

    if len(extracted_number) > 0:
        return extracted_number

    # If OCR fails, save debug images to the designated output folder
    name_start = os.path.basename(image_path)

    # Save ROI visualization
    roi_debug_filename = f"{name_start}_debug_roi.jpg"
    cv2.imwrite(os.path.join(debug_save_path, roi_debug_filename), debug_img)

    # Save processed image
    processed_debug_filename = f"{name_start}_debug_processed.jpg"
    cv2.imwrite(os.path.join(debug_save_path, processed_debug_filename), img)
    print(f"[INFO] No number detected for {name_start} (see debug images)")


def crop_to_content(img, base_name):
    box, offsets = get_content_box(img)
    # Check if any side exceeds the skip limit
    if box and offsets:
        if any(val > MAX_CROP_LIMIT for val in offsets.values()):
            print(
                f"[SKIP] {base_name}: Border too large"
                f"(L:{offsets['left']} T:{offsets['top']} R:{offsets['right']} B:{offsets['bottom']})"
            )
            return None  # Exit the function for this file

        if any(val > 0 for val in offsets.values()):
            # Apply crop
            img = img.crop(box)

            # Output Message
            # crop_info = f"L:{offsets['left']}px, T:{offsets['top']}px, R:{offsets['right']}px, B:{offsets['bottom']}px"
            # print(f"[INFO] Cropped {base_name}: {crop_info}")
    return img


def resize_and_compress(image_path):
    base_name = os.path.basename(image_path)
    try:
        with Image.open(image_path) as img:
            img = safe_convert_to_rgb(img)

            # Check top row & bottom row and crop if white
            if REMOVE_WHITE_BORDERS:
                img = crop_to_content(img, base_name)
                if img is None:
                    return  # skip this file if the content wasn't properly detected

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

            # Maybe crop image with preference
            if FIXED_CROP_OFFSETS:
                left, top, right, bottom = FIXED_CROP_OFFSETS  # type: ignore
                # Calculate the crop box: (left, top, width-right, height-bottom)
                width, height = img.size
                img = img.crop((left, top, width - right, height - bottom))
            
            if CROP_TO_OUTPUT_SIZE:
                # Crop image to output size
                width, height = img.size
                target_w, target_h = output_size
                
                # Calculate the cropping box to center the cut
                left = (width - target_w) / 2
                top = (height - target_h) / 2
                right = (width + target_w) / 2
                bottom = (height + target_h) / 2
                
                # Remove the outer area and keep the center
                img = img.crop((left, top, right, bottom))
            else:
                # Resize image to exact dimensions (without keeping aspect ratio)
                img = img.resize(output_size, Image.Resampling.LANCZOS)

            # Maybe boost colors
            if COLOR_BOOST != 1.0:
                converter = ImageEnhance.Color(img)
                img = converter.enhance(COLOR_BOOST)

            # Maybe boost contrast
            if CONTRAST_BOOST != 1.0:
                contrast_converter = ImageEnhance.Contrast(img)
                img = contrast_converter.enhance(CONTRAST_BOOST)

            # Maybe boost brightness
            if BRIGHTNESS_BOOST != 1.0:
                brightener = ImageEnhance.Brightness(img)
                img = brightener.enhance(BRIGHTNESS_BOOST)

            # Cuts off 1% of extreme pixels to normalize
            if AUTO_CONTRAST:
                img = ImageOps.autocontrast(img, cutoff=1)

            # Determine which folder to use
            if OUTPUT_FOLDER:
                # If it's a relative path, put it inside the source image's directory
                if not os.path.isabs(OUTPUT_FOLDER):
                    target_dir = os.path.join(
                        os.path.dirname(image_path), OUTPUT_FOLDER
                    )
                else:
                    target_dir = OUTPUT_FOLDER

                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
            else:
                target_dir = os.path.dirname(image_path)

            base_name_no_ext = os.path.splitext(base_name)[0]

            # Attempt to extract card number (Windows only)
            if (
                PLATFORM == "Windows"
                and not OVERRIDE_EXISTING_FILES
                and EXTRACT_CARD_NUMBER
            ):
                card_number = extract_card_number(img, image_path, target_dir)
                if card_number:
                    base_name_no_ext = card_number

            # Construct final output path
            ending = "." + FILE_ENDING[OUTPUT_FORMAT]
            if OVERRIDE_EXISTING_FILES:
                output_path = os.path.join(target_dir, f"{base_name_no_ext}{ending}")
            else:
                output_path = get_unique_filename(target_dir, base_name_no_ext, ending)

            if OUTPUT_FORMAT.upper() == "PNG":
                img.save(output_path, format=OUTPUT_FORMAT)
            else:
                # Save with compression to ensure file size is under MAX_FILE_SIZE_KB
                # WebP and JPEG both use the 'quality' parameter
                quality = 100
                while quality > 50:
                    img.save(
                        output_path,
                        format=OUTPUT_FORMAT,
                        quality=quality,
                        method=6,
                    )
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
        # Prevent processing the output folder if it's inside the source folder
        if OUTPUT_FOLDER and OUTPUT_FOLDER in root:
            continue

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
