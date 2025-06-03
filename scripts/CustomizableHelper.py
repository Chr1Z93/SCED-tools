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
Z_ROW_THRESHOLD = 0.03
X_INITIAL_DEVIATION_THRESHOLD = 0.1

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


def group_checkboxes_by_z(checkboxes, z_threshold):
    if not checkboxes:
        return []

    rows = []
    current_row = [checkboxes[0]]

    for cb in checkboxes[1:]:
        _, prev_z = current_row[-1]
        _, curr_z = cb
        if abs(curr_z - prev_z) <= z_threshold:
            current_row.append(cb)
        else:
            rows.append(current_row)
            current_row = [cb]
    rows.append(current_row)
    return rows


def filter_rows_by_x_initial(rows, deviation_threshold):
    row_x_initials = [
        (i, min(row, key=lambda pt: pt[0])[0]) for i, row in enumerate(rows)
    ]
    x_initial_values = [x for _, x in row_x_initials]
    mean_x_initial = statistics.mean(x_initial_values)

    valid_rows = []
    discarded_rows = []

    for row_idx, x_init in row_x_initials:
        row = rows[row_idx]
        if abs(x_init - mean_x_initial) <= deviation_threshold:
            valid_rows.append((row_idx, row))
        else:
            discarded_rows.append((row_idx, row))

    return valid_rows, discarded_rows, mean_x_initial


def print_rows_info(label, indexed_rows):
    print(f"\n{label}")
    for original_index, row in indexed_rows:
        row_sorted = sorted(row, key=lambda pt: pt[0])
        xs = [x for x, _ in row_sorted]
        zs = [z for _, z in row_sorted]

        median_z = statistics.median(zs)
        pairwise_offsets = [f"{(xs[j+1] - xs[j]):+.3f}" for j in range(len(xs) - 1)]

        print(
            f"Row {original_index + 1}: z-pos = {median_z:.3f}, count = {len(xs)}, "
            f"x-initial = {xs[0]:.3f}, x-offsets: {pairwise_offsets}"
        )


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

if checkboxes:
    # Group checkboxes by Z
    rows = group_checkboxes_by_z(checkboxes, Z_ROW_THRESHOLD)

    # Filter rows by x-initial deviation
    valid_rows, discarded_rows, mean_x_initial = filter_rows_by_x_initial(
        rows, X_INITIAL_DEVIATION_THRESHOLD
    )

    # Print valid rows info
    print_rows_info("Grouped rows by similar Z-coordinates (valid):", valid_rows)

    # Print summary stats for valid rows
    if valid_rows:
        all_x = [min(row, key=lambda pt: pt[0])[0] for _, row in valid_rows]
        print(f"\nx-initial mean: {statistics.mean(all_x):.3f}")
        print(f"x-initial median: {statistics.median(all_x):.3f}")
    else:
        print("\nNo valid rows remaining after outlier removal.")

    # Print discarded rows info
    if discarded_rows:
        print_rows_info("Discarded rows due to x-initial deviation:", discarded_rows)
else:
    print("No checkboxes found.")


# Save debug image
cv2.imwrite("debug_checkboxes.png", debug_image)
print("\nDebug image saved as 'debug_checkboxes.png'")
print("Green boxes = left-side checkboxes (included)")
print("Red boxes = other checkboxes (excluded)")
