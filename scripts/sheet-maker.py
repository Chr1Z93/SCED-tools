import os
from PIL import Image

# --- CONFIGURATION ---
PATH = r"C:\Users\pulsc\Downloads\Brethren of Ash\TTS ready\double sided back"
COLUMNS = 10
ROWS = 4


def stitch_images(folder_path, cols, rows):
    # Clean up path and get folder name
    abs_path = os.path.abspath(folder_path)
    folder_name = os.path.basename(abs_path)
    parent_dir = os.path.dirname(abs_path)
    output_filename = f"{folder_name}_grid.webp"

    # Gather all image files
    valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")
    images = [
        f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)
    ]
    images.sort()  # Ensures consistent ordering

    if not images:
        print("No images found in the directory.")
        return

    # Open the first image to get dimensions
    with Image.open(os.path.join(folder_path, images[0])) as img:
        img_w, img_h = img.size

    # Create a blank canvas
    # Total size = (width * cols) x (height * rows)
    grid_w = img_w * cols
    grid_h = img_h * rows
    canvas = Image.new("RGB", (grid_w, grid_h))

    # Paste images into the grid
    for index, image_name in enumerate(images):
        if index >= cols * rows:
            break  # Stop if we run out of grid space

        with Image.open(os.path.join(folder_path, image_name)) as img:
            # Resize if the image doesn't match the first one's dimensions
            if img.size != (img_w, img_h):
                img = img.resize((img_w, img_h))

            # Calculate coordinates
            x = (index % cols) * img_w
            y = (index // cols) * img_h
            canvas.paste(img, (x, y))

    # Determine the parent directory
    parent_dir = os.path.dirname(os.path.abspath(folder_path))

    # Define the full output path
    output_path = os.path.join(parent_dir, output_filename)

    # Save the result
    canvas.save(output_path)
    print(f"Success! Grid saved at: {output_path}")


stitch_images(PATH, COLUMNS, ROWS)
