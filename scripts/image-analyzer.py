import os
from pathlib import Path
from PIL import Image

# --- CONFIGURATION ---
# The root folder you want to scan (e.g., 'C:/MyImages' or '/home/user/photos')
TARGET_FOLDER = r"C:\Users\pulsc\Downloads\CardsToParse"  # <-- CHANGE THIS TO YOUR FOLDER PATH!

# The maximum allowed deviation in pixels (e.g., 10px in width OR height)
PIXEL_MARGIN = 25


def analyze_image_dimensions(root_dir: str, deviation_margin: int):
    """
    Traverses a directory, calculates the average dimensions of image files,
    and identifies files that deviate from that average.
    """
    print(f"🔍 Starting analysis in: {root_dir}")
    print(f"⚠️ Deviation Margin: {deviation_margin} pixels\n")

    # 1. Collect dimensions for all images
    image_data = []

    # Define common image extensions
    image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp")

    # os.walk is used to iterate through all files and subfolders
    for folder, _, files in os.walk(root_dir):
        for filename in files:
            if filename.lower().endswith(image_extensions):
                full_path = Path(folder) / filename

                try:
                    # Use Pillow to open the image and get its size (width, height)
                    with Image.open(full_path) as img:
                        width, height = img.size

                        # Store the file path and its dimensions
                        image_data.append(
                            {"path": str(full_path), "width": width, "height": height}
                        )

                except Exception as e:
                    # Skip files that cannot be opened as images
                    print(f"Skipping file (read error): {full_path} -> {e}")

    total_images = len(image_data)
    if total_images == 0:
        print("❌ No images found for analysis.")
        return

    # 2. Calculate average dimensions
    total_width = sum(d["width"] for d in image_data)
    total_height = sum(d["height"] for d in image_data)

    avg_width = round(total_width / total_images)
    avg_height = round(total_height / total_images)

    print("---")
    print(f"📊 Analysis Results for {total_images} images:")
    print(f"Average Dimensions: **{avg_width}x{avg_height}** (Width x Height)")
    print("---")

    # 3. Find files that deviate from the average
    deviating_files = []

    for item in image_data:
        # Calculate the absolute difference from the average for each dimension
        width_diff = abs(item["width"] - avg_width)
        height_diff = abs(item["height"] - avg_height)

        # Check if the deviation exceeds the margin in EITHER dimension
        if width_diff > deviation_margin or height_diff > deviation_margin:
            deviating_files.append(
                {
                    "path": item["path"],
                    "dimensions": f"{item['width']}x{item['height']}",
                    "deviation_w": width_diff,
                    "deviation_h": height_diff,
                }
            )

    # 4. Display the deviating files
    if deviating_files:
        print(
            f"❗ **{len(deviating_files)} Files Deviating by >{deviation_margin}px:**"
        )
        print("\nPath | Dimensions | Dev W | Dev H")
        print("---|---|---|---")
        for file in deviating_files:
            print(
                f"{file['path']} | {file['dimensions']} | {file['deviation_w']} | {file['deviation_h']}"
            )
    else:
        print("✅ All files are within the specified deviation margin.")


if __name__ == "__main__":
    analyze_image_dimensions(TARGET_FOLDER, PIXEL_MARGIN)
