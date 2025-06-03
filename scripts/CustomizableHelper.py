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


def find_all_potential_checkboxes(contours, width, height):
    """
    Finds all valid checkboxes based on size and aspect ratio,
    returns their normalized and pixel coordinates.
    """
    potential_checkboxes = (
        []
    )  # Stores (norm_x, norm_z, (x_pixel, z_pixel, w_pixel, h_pixel))

    for cnt in contours:
        x_pixel, z_pixel, w_pixel, h_pixel = cv2.boundingRect(cnt)
        if is_valid_checkbox(w_pixel, h_pixel):
            norm_x, norm_z = get_normalized_coords(
                x_pixel, z_pixel, w_pixel, h_pixel, width, height
            )
            potential_checkboxes.append(
                (norm_x, norm_z, (x_pixel, z_pixel, w_pixel, h_pixel))
            )

    return potential_checkboxes


def draw_debug_image(
    image, final_checkbox_statuses, output_path="debug_checkboxes.png"
):
    """
    Draws bounding boxes on the image for debugging based on final inclusion status.
    Green for included, Red for disregarded.
    final_checkbox_statuses is a list of (bbox_pixel_coords, is_included)
    """
    debug_image = image.copy()
    for (x, z, w, h), is_included in final_checkbox_statuses:
        color = (0, 255, 0) if is_included else (0, 0, 255)  # Green or Red
        cv2.rectangle(debug_image, (x, z), (x + w, z + h), color, 2)
    cv2.imwrite(output_path, debug_image)


def group_checkboxes_by_z(checkboxes):
    """Groups checkboxes into rows based on their z-coordinates.
    Input checkboxes are expected to be (norm_x, norm_z) tuples.
    """
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
    Input rows contain (norm_x, norm_z) tuples.
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
    original_row_index_map = {}  # Map new index to original row index for printing
    valid_rows_temp = []

    for row_idx, x_init in row_x_initials:
        row = rows[row_idx]
        if abs(x_init - mean_x_initial) <= X_INITIAL_DEVIATION_THRESHOLD:
            valid_rows_temp.append(row)
            original_row_index_map[len(valid_rows_temp) - 1] = (
                row_idx  # Store original index
            )
        else:
            discarded_rows.append((row_idx, row))  # Keep original index for discarded

    # Re-index valid rows to start from 0 for print_rows_info consistent output
    for new_idx, row_content in enumerate(valid_rows_temp):
        valid_rows.append(
            (new_idx, row_content)
        )  # Use new_idx for display, content for actual data

    return valid_rows, discarded_rows, mean_x_initial


def print_rows_info(label, indexed_rows):
    """Prints detailed information for each row of checkboxes.
    indexed_rows format: [(original_index, [(norm_x, norm_z), ...]), ...]
    """
    print(f"\n--- {label} ---")
    if not indexed_rows:
        print("No rows to display.")
        return

    for original_index, row in indexed_rows:
        row_sorted = sorted(row, key=lambda pt: pt[0])  # Sort by norm_x for offsets
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

    # --- Step 1: Find all potential checkboxes with their normalized and pixel coords ---
    # Each item: (norm_x, norm_z, (x_pixel, z_pixel, w_pixel, h_pixel))
    all_potential_checkboxes_with_coords = find_all_potential_checkboxes(
        contours, width, height
    )

    # --- Step 2: Apply LEFT_SIDE_THRESHOLD filter ---
    # Only keep those to the left of the threshold for further row processing
    checkboxes_passing_left_filter = [
        cb for cb in all_potential_checkboxes_with_coords if cb[0] < LEFT_SIDE_THRESHOLD
    ]

    # Sort these checkboxes from top to bottom (by z) for row grouping
    checkboxes_passing_left_filter.sort(key=lambda item: item[1])  # Sort by norm_z

    # Extract only (norm_x, norm_z) for row grouping functions
    normalized_checkboxes_for_grouping = [
        (cb[0], cb[1]) for cb in checkboxes_passing_left_filter
    ]

    final_included_checkboxes_norm_coords = set()
    final_discarded_checkboxes_norm_coords = set()

    if normalized_checkboxes_for_grouping:
        # --- Step 3: Group initially filtered checkboxes into rows ---
        rows = group_checkboxes_by_z(normalized_checkboxes_for_grouping)

        # --- Step 4: Filter rows by x-initial deviation ---
        valid_rows_for_printing, discarded_rows_for_printing, mean_x_initial = (
            filter_rows_by_x_initial(rows)
        )

        # Populate the set of final included checkboxes (normalized coords)
        for _, row_content in valid_rows_for_printing:
            for cb_norm_x, cb_norm_z in row_content:
                final_included_checkboxes_norm_coords.add((cb_norm_x, cb_norm_z))

        # Populate the set of final discarded checkboxes (normalized coords from rows)
        for _, row_content in discarded_rows_for_printing:
            for cb_norm_x, cb_norm_z in row_content:
                final_discarded_checkboxes_norm_coords.add((cb_norm_x, cb_norm_z))

        # Print valid rows info
        print_rows_info(
            "Grouped rows by similar Z-coordinates (valid)", valid_rows_for_printing
        )

        # Print summary stats for valid rows
        if valid_rows_for_printing:
            all_x_initials = [
                min(row, key=lambda pt: pt[0])[0] for _, row in valid_rows_for_printing
            ]
            print(f"\nx-initial mean: {statistics.mean(all_x_initials):.3f}")
            print(f"x-initial median: {statistics.median(all_x_initials):.3f}")
        else:
            print("\nNo valid rows remaining after outlier removal.")

        # Print discarded rows info
        if discarded_rows_for_printing:
            print_rows_info(
                "Discarded rows due to x-initial deviation:",
                discarded_rows_for_printing,
            )
    else:
        print("\nNo checkboxes found after initial filtering (left side threshold).")

    # --- Step 5: Prepare debug data based on final filtering results ---
    # Iterate through ALL potential checkboxes (from step 1) to determine their final color
    final_debug_checkbox_statuses = []
    for norm_x, norm_z, bbox_pixel_coords in all_potential_checkboxes_with_coords:
        if (norm_x, norm_z) in final_included_checkboxes_norm_coords:
            final_debug_checkbox_statuses.append((bbox_pixel_coords, True))  # Green
        else:
            # If not in final_included_checkboxes_norm_coords, it means it was discarded
            # either by LEFT_SIDE_THRESHOLD or X_INITIAL_DEVIATION_THRESHOLD
            final_debug_checkbox_statuses.append((bbox_pixel_coords, False))  # Red

    # --- Step 6: Draw and save the debug image ---
    draw_debug_image(image, final_debug_checkbox_statuses)
    print("\nDebug image saved as 'debug_checkboxes.png'")
    print("Green boxes = included checkboxes (passed all filters)")
    print("Red boxes   = disregarded checkboxes (failed any filter)")
