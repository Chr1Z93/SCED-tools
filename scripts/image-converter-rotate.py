# Converts images to 750 x 1050 and JPG with max. 450 KB

import sys
import os
from PIL import Image


def get_unique_filename(base_path, base_name, extension):
    """Generate a unique filename by adding a numeric suffix if the file already exists."""
    counter = 1
    output_path = f"{base_path}\\{base_name}{extension}"
    while os.path.exists(output_path):
        output_path = f"{base_path}\\{base_name}_{counter}{extension}"
        counter += 1
    return output_path


def resize_and_compress(image_path, output_size=(750, 1050), max_file_size_kb=450):
    try:
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode == "RGBA":
                img = img.convert("RGB")

            # Rotate horizontal images 90° clockwise
            if img.width > img.height:
                img = img.rotate(-90, expand=True)

            # Resize image to exact dimensions (without keeping aspect ratio)
            img = img.resize(output_size, Image.LANCZOS)

            # Define output path
            base_path = os.path.dirname(image_path)
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = get_unique_filename(base_path, base_name, ".jpg")

            # Save with compression to ensure file size is under max_file_size_kb
            quality = 100
            while quality > 50:
                img.save(output_path, format="JPEG", quality=quality)
                file_size_kb = os.path.getsize(output_path) / 1024
                if file_size_kb <= max_file_size_kb:
                    break
                quality -= 1

            if file_size_kb > max_file_size_kb:
                print(f"[WARNING] Unable to compress {image_path}")

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
