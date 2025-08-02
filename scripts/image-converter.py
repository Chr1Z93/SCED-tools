# Converts images to specified resolution, file format and file size (if JPG)

import sys
import os
from PIL import Image

# Configuration
ROTATE_HORIZONTAL_IMAGES = False
OUTPUT = (750, 1050)  # width x height, use 0 to calculate automatically
MAX_FILE_SIZE_KB = 450  # only used for JPEGs
OUTPUT_FORMAT = "JPG"  # e.g. PNG or JPEG

# Data
OUTPUT_LANDSCAPE = (OUTPUT[1], OUTPUT[0])
OUTPUT_PORTRAIT = OUTPUT
FILE_ENDING = {"PNG": "png", "JPEG": "jpg"}


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


def resize_and_compress(image_path):
    try:
        with Image.open(image_path) as img:
            # Check the output format and convert if necessary
            if OUTPUT_FORMAT == "JPEG" and img.mode == "RGBA":
                img = img.convert("RGB")

            original_size = img.size

            if ROTATE_HORIZONTAL_IMAGES:
                # Calculate the final output size based on aspect ratio
                output_size = calculate_new_size(original_size, OUTPUT)

                # Rotate horizontal images 90° clockwise
                if original_size[0] > original_size[1]:
                    img = img.rotate(-90, expand=True)
                    output_size = (output_size[1], output_size[0])
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
            ending = "." + FILE_ENDING[OUTPUT_FORMAT]
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
