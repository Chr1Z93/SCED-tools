import os
from PIL import Image

# List of file names (without extensions)
FILTER_NAMES = []  # Example: [ "90091", "90092"]
INPUT_FOLDER = r""
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff")


def rotate_image(filepath, filename):
    """Helper function to handle the rotation logic."""
    try:
        with Image.open(filepath) as img:
            rotated_img = img.rotate(180)
            rotated_img.save(
                filepath,
                quality=100,
                method=6,
            )
            print(f"Rotated and saved: {filename}")
    except Exception as e:
        print(f"Could not process {filename}: {e}")


def rotate_images_auto_ext():
    # Get a list of all files in the folder once to save time
    folder_files = os.listdir(INPUT_FOLDER)

    if len(FILTER_NAMES) > 0:
        print("Filtering enabled. Processing specific names...")
        for name in FILTER_NAMES:
            # Find the file that matches the name (ignoring extension)
            match = next(
                (f for f in folder_files if os.path.splitext(f)[0] == name),
                None,
            )

            if match:
                filepath = os.path.join(INPUT_FOLDER, match)
                rotate_image(filepath, match)
            else:
                print(f"No file found matching: {name}")
    else:
        print("Processing ALL images in folder...")
        for filename in folder_files:
            filepath = os.path.join(INPUT_FOLDER, filename)

            # Ensure it's a file and has a valid image extension
            if os.path.isfile(filepath) and filename.lower().endswith(VALID_EXTENSIONS):
                rotate_image(filepath, filename)


if __name__ == "__main__":
    rotate_images_auto_ext()
