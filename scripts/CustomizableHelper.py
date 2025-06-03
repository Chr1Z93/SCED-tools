import cv2
import statistics

# Load and preprocess the image
image = cv2.imread(r"C:\git\SCED-tools\scripts\HuntersArmor.png")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
adaptive_thresh = cv2.adaptiveThreshold(
    blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 3
)

# Find contours
contours, _ = cv2.findContours(
    adaptive_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
)

# Get image dimensions for normalization
height, width = image.shape[:2]

checkboxes = []
for cnt in contours:
    # Search for checkboxes
    x, z, w, h = cv2.boundingRect(cnt)
    aspect_ratio = w / h
    if 0.8 < aspect_ratio < 1.25 and 8 < w < 30 and 8 < h < 30:
        # Compute normalized coordinates using width for both axes
        center_x = x + w / 2
        center_z = z + h / 2

        # horizontal (left to right)
        norm_x = 2 * (center_x / width) - 1

        # vertical (top to bottom), scaled to width
        norm_z = 2 * ((center_z - height / 2) / width)

        if norm_x < -0.85:
            checkboxes.append((norm_x, norm_z))

# Sort checkboxes from top to bottom (by z)
checkboxes.sort(key=lambda pt: pt[1])

# Print results
if checkboxes:
    x_coords = [nx for nx, nz in checkboxes]
    z_coords = [nz for nx, nz in checkboxes]

    print("Z-coordinates:")
    for i, nz in enumerate(z_coords):
        print(f"{i+1}: z={nz:.3f}")

    print(f"\nX-mean: {statistics.mean(x_coords):.3f}")
    print(f"X-median: {statistics.median(x_coords):.3f}")
else:
    print("No checkboxes found.")
