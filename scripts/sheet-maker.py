from pathlib import Path
from PIL import Image

# --- CONFIGURATION ---
PATH = Path(r"C:\Users\pulsc\Downloads\EotE Sheet")
COLUMNS = 10
ROWS = 5


def stitch_images(folder_path, cols, rows):
    # Convert string to Path object if it isn't one already
    base_path = Path(folder_path).resolve()

    if not base_path.exists():
        print(f"Error: Path {base_path} does not exist.")
        return
    
    # Define output info using Path properties
    output_filename = f"{base_path.name}_grid.webp"
    output_path = base_path.parent / output_filename

    # Gather all image files
    valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")
    images = sorted([
        f for f in base_path.iterdir() 
        if f.suffix.lower() in valid_extensions
    ])

    if not images:
        print("No images found in the directory.")
        return

    # Open the first image to get dimensions
    with Image.open(images[0]) as img:
        img_w, img_h = img.size

    # Create a blank canvas
    canvas = Image.new("RGB", (img_w * cols, img_h * rows))

    # Paste images into the grid
    for index, image_path in enumerate(images):
        if index >= cols * rows:
            break  # Stop if we run out of grid space

        with Image.open(image_path) as img:
            # Resize if the image doesn't match the first one's dimensions
            if img.size != (img_w, img_h):
                img = img.resize((img_w, img_h))

            # Calculate coordinates
            x = (index % cols) * img_w
            y = (index // cols) * img_h
            canvas.paste(img, (x, y))

    # Save the result
    canvas.save(output_path, method=6)
    print(f"Success! Sheet saved at: {output_path}")


stitch_images(PATH, COLUMNS, ROWS)
