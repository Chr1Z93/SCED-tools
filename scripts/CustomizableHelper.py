import cv2
import statistics

# Configuration parameters
IMAGE_PATH = r"C:\git\SCED-tools\scripts\HuntersArmor.png"

# Box identification parameters
MIN_ASPECT_RATIO = 0.9
MAX_ASPECT_RATIO = 1.1
MIN_BOX_SIZE = 20
MAX_BOX_SIZE = 30

# Ignore boxes left of this
LEFT_SIDE_THRESHOLD = -0.5

# Used for grouping boxes into rows
Z_ROW_THRESHOLD = 0.03

# Used to ignore outliers
X_INITIAL_DEVIATION_THRESHOLD = 0.1


def is_valid_checkbox(w, h):
    """Check if dimensions match checkbox criteria"""
    return (
        MIN_ASPECT_RATIO < w / h < MAX_ASPECT_RATIO
        and MIN_BOX_SIZE < w < MAX_BOX_SIZE
        and MIN_BOX_SIZE < h < MAX_BOX_SIZE
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


def find_checkboxes(contours, width, height):
    """
    Identifies and returns normalized coordinates of valid checkboxes.
    Also returns the bounding rectangles for drawing debug images.
    """
    checkboxes = []
    # Stores bounding rects along with a flag indicating if they are included
    debug_rects = []

    for cnt in contours:
        x, z, w, h = cv2.boundingRect(cnt)
        if is_valid_checkbox(w, h):
            norm_x, norm_z = get_normalized_coords(x, z, w, h, width, height)
            if norm_x < LEFT_SIDE_THRESHOLD:
                checkboxes.append((norm_x, norm_z))
                debug_rects.append(((x, z, w, h), True))  # Included
            else:
                debug_rects.append(((x, z, w, h), False))  # Disregarded

    # Sort checkboxes from top to bottom (by z)
    checkboxes.sort(key=lambda pt: pt[1])
    return checkboxes, debug_rects


def draw_debug_image(image, debug_rects, output_path="debug_checkboxes.png"):
    """
    Draws bounding boxes on the image for debugging.
    Green for included, Red for disregarded.
    """
    debug_image = image.copy()
    for (x, z, w, h), is_included in debug_rects:
        color = (0, 255, 0) if is_included else (0, 0, 255)  # Green or Red
        cv2.rectangle(debug_image, (x, z), (x + w, z + h), color, 2)
    cv2.imwrite(output_path, debug_image)


def group_checkboxes_by_z(checkboxes):
    """Groups checkboxes into rows based on their z-coordinates."""
    if not checkboxes:
        return []

    rows = []
    current_row = [checkboxes[0]]

    for cb in checkboxes[1:]:
        _, prev_z = current_row[-1]
        _, curr_z = cb
        if abs(curr_z - prev_z) <= Z_ROW_THRESHOLD:
            current_row.append(cb)
        else:
            rows.append(current_row)
            current_row = [cb]
    rows.append(current_row)
    return rows


def filter_rows_by_x_initial(rows):
    """
    Filters rows based on the deviation of their initial x-coordinate
    from the mean initial x-coordinate of all rows.
    """
    row_x_initials = [
        (i, min(row, key=lambda pt: pt[0])[0]) for i, row in enumerate(rows)
    ]
    x_initial_values = [x for _, x in row_x_initials]

    if not x_initial_values:
        return [], [], 0  # No rows to process

    mean_x_initial = statistics.mean(x_initial_values)

    valid_rows = []
    discarded_rows = []

    # This 'discarded_row_id' helps in maintaining the correct index for valid_rows
    # if rows are removed.
    discarded_row_id = 0

    for row_idx, x_init in row_x_initials:
        row = rows[row_idx]
        if abs(x_init - mean_x_initial) <= X_INITIAL_DEVIATION_THRESHOLD:
            valid_rows.append((row_idx - discarded_row_id, row))
        else:
            discarded_rows.append((discarded_row_id, row))
            discarded_row_id += 1

    return valid_rows, discarded_rows, mean_x_initial


def print_rows_info(label, indexed_rows):
    """Prints detailed information for each row of checkboxes."""
    print(f"\n--- {label} ---")
    if not indexed_rows:
        print("No rows to display.")
        return

    for original_index, row in indexed_rows:
        row_sorted = sorted(row, key=lambda pt: pt[0])
        xs = [x for x, _ in row_sorted]
        zs = [z for _, z in row_sorted]

        median_z = statistics.median(zs)
        # Calculate pairwise offsets only if there's more than one checkbox in the row
        pairwise_offsets = (
            [f"{(xs[j+1] - xs[j]):+.3f}" for j in range(len(xs) - 1)]
            if len(xs) > 1
            else []
        )

        print(
            f"Row {original_index + 1}: z-pos = {median_z:+.3f}, count = {len(xs)}, "
            f"x-initial = {xs[0]:.3f}, x-offsets: [{', '.join(pairwise_offsets)}]"
        )


# Main processing starts here
if __name__ == "__main__":
    # Load and preprocess the image
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        print(f"Error: Could not load image at {IMAGE_PATH}")
        exit()

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

    # Find checkboxes and prepare debug info
    checkboxes, debug_rects = find_checkboxes(contours, width, height)

    # Draw and save the debug image
    draw_debug_image(image, debug_rects)
    print("\nDebug image saved as 'debug_checkboxes.png'")
    print("Green boxes = included checkboxes")
    print("Red boxes   = disregarded checkboxes")

    if checkboxes:
        rows = group_checkboxes_by_z(checkboxes)

        # Filter rows by x-initial deviation
        valid_rows, discarded_rows, mean_x_initial = filter_rows_by_x_initial(rows)

        # Print valid rows info
        print_rows_info("Grouped rows by similar Z-coordinates (valid)", valid_rows)

        # Print summary stats for valid rows
        if valid_rows:
            all_x_initials = [
                min(row, key=lambda pt: pt[0])[0] for _, row in valid_rows
            ]
            print(f"\nx-initial mean: {statistics.mean(all_x_initials):.3f}")
        else:
            print("\nNo valid rows remaining after outlier removal.")

        # Print discarded rows info
        if discarded_rows:
            print_rows_info("Discarded rows due to x-initial deviation", discarded_rows)
    else:
        print("\nNo checkboxes found.")
