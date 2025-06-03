import cv2
import statistics

# Configuration parameters
IMAGE_PATH = r"C:\git\SCED-tools\scripts\HuntersArmor.png"
MIN_ASPECT_RATIO = 0.9
MAX_ASPECT_RATIO = 1.1
MIN_WIDTH = 20
MAX_WIDTH = 30
MIN_HEIGHT = 20
MAX_HEIGHT = 30
LEFT_SIDE_THRESHOLD = -0.5

# Load and preprocess the image
image = cv2.imread(IMAGE_PATH)
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


def is_valid_checkbox(w, h):
    """Check if dimensions match checkbox criteria"""
    aspect_ratio = w / h
    return (
        MIN_ASPECT_RATIO < aspect_ratio < MAX_ASPECT_RATIO
        and MIN_WIDTH < w < MAX_WIDTH
        and MIN_HEIGHT < h < MAX_HEIGHT
    )


def get_normalized_coords(x, z, w, h, width, height):
    """Convert pixel coordinates to normalized coordinates"""
    center_x = x + w / 2
    center_z = z + h / 2

    # horizontal (left to right)
    norm_x = 2 * (center_x / width) - 1

    # vertical (top to bottom), scaled to width
    norm_z = 2 * ((center_z - height / 2) / width)

    return norm_x, norm_z


# Find checkboxes
checkboxes = []
for cnt in contours:
    x, z, w, h = cv2.boundingRect(cnt)
    if is_valid_checkbox(w, h):
        norm_x, norm_z = get_normalized_coords(x, z, w, h, width, height)
        if norm_x < LEFT_SIDE_THRESHOLD:
            checkboxes.append((norm_x, norm_z))

# Sort checkboxes from top to bottom (by z)
checkboxes.sort(key=lambda pt: pt[1])

# Create visual output for debugging
debug_image = image.copy()
for cnt in contours:
    x, z, w, h = cv2.boundingRect(cnt)
    if is_valid_checkbox(w, h):
        norm_x, _ = get_normalized_coords(x, z, w, h, width, height)
        # Draw rectangle - green for left-side checkboxes, red for others
        if norm_x < LEFT_SIDE_THRESHOLD:
            cv2.rectangle(debug_image, (x, z), (x + w, z + h), (0, 255, 0), 2)  # Green
        else:
            cv2.rectangle(debug_image, (x, z), (x + w, z + h), (0, 0, 255), 2)  # Red

# Print results
if checkboxes:
    x_coords = [nx for nx, nz in checkboxes]
    z_coords = [nz for nx, nz in checkboxes]

    print("\nZ-coordinates:")
    for i, nz in enumerate(z_coords):
        print(f"{i+1}: z={nz:.3f}")

    print(f"\nX-coordinate mean: {statistics.mean(x_coords):.3f}")
    print(f"X-coordinate median: {statistics.median(x_coords):.3f}")
else:
    print("No checkboxes found.")

# Save debug image
cv2.imwrite("debug_checkboxes.png", debug_image)
print("Debug image saved as 'debug_checkboxes.png'")
print("Green boxes = left-side checkboxes (included)")
print("Red boxes = other checkboxes (excluded)")
