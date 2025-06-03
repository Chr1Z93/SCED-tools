import cv2
import os
import statistics

# Configuration parameters
IMAGE_PATH = r"C:\git\SCED-tools\scripts\HuntersArmor2.png"
PRINT_DISCARDED = False

# Box identification parameters
MIN_ASPECT_RATIO = 0.9
MAX_ASPECT_RATIO = 1.1
MIN_BOX_SIZE = 20 / 750
MAX_BOX_SIZE = 30 / 750

# Ignore boxes left of this
LEFT_SIDE_THRESHOLD = -0.5

# Used for grouping boxes into rows
Z_ROW_THRESHOLD = 0.03 / 1050

# Used to ignore outliers in row's initial x-position
X_INITIAL_DEVIATION_THRESHOLD = 0.1 / 750

# Used to ignore outliers in x-offset within a row
X_OFFSET_DEVIATION_THRESHOLD_FACTOR = 1.2


def is_valid_checkbox(w, h):
    """Check if dimensions match checkbox criteria"""
    return (
        MIN_ASPECT_RATIO < w / h < MAX_ASPECT_RATIO
        and MIN_BOX_SIZE < w / width < MAX_BOX_SIZE
        and MIN_BOX_SIZE < h / width < MAX_BOX_SIZE
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


def draw_debug_image(image, final_checkbox_statuses):
    """
    Draws bounding boxes on the image for debugging based on final inclusion status.
    Green for included, Red for disregarded.
    final_checkbox_statuses is a list of (bbox_pixel_coords, is_included)
    """
    debug_image = image.copy()
    for (x, z, w, h), is_included in final_checkbox_statuses:
        color = (0, 255, 0) if is_included else (0, 0, 255)  # Green or Red
        cv2.rectangle(debug_image, (x, z), (x + w, z + h), color, 2)

    # Get the directory of the current script
    # os.path.abspath(__file__) gets the absolute path of the script file.
    # os.path.dirname() extracts the directory part from that path.
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Extract original filename and extension
    original_filename_with_ext = os.path.basename(IMAGE_PATH)
    filename_base, file_extension = os.path.splitext(original_filename_with_ext)

    # Construct the new debug filename
    output_filename = f"{filename_base}_debug{file_extension}"

    # Combine the script directory and the filename to create the full output path
    output_path = os.path.join(script_directory, output_filename)

    cv2.imwrite(output_path, debug_image)

    return output_filename


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
        if abs(curr_z - prev_z) <= Z_ROW_THRESHOLD * height:
            current_row.append(cb)
        else:
            rows.append(current_row)
            current_row = [cb]
    rows.append(current_row)
    return rows


def filter_rows_by_x_offset_deviation(rows_grouped_by_z):
    """
    Filters checkboxes within each row based on x-offset deviation from the previous box.
    If an x-offset is too large, that box and all subsequent boxes in the row are discarded.
    Input rows_grouped_by_z: list of lists of (norm_x, norm_z) tuples.
    Returns:
        valid_rows_after_offset_filter: List of (original_row_idx, list_of_checkboxes_content)
        discarded_rows_by_offset_filter: List of (original_row_idx, list_of_checkboxes_content)
    """
    valid_rows_after_offset_filter = []
    discarded_rows_by_offset_filter = []

    for original_row_idx, row_content in enumerate(rows_grouped_by_z):
        # Sort boxes within the row by x-coordinate for offset calculation
        row_sorted_by_x = sorted(row_content, key=lambda pt: pt[0])

        valid_segment_in_row = []
        discarded_segment_in_row = []  # To hold checkboxes discarded *within* this row

        if len(row_sorted_by_x) < 2:
            # Rows with 0 or 1 box are always valid for this filter (no offsets to check)
            if row_sorted_by_x:  # Add if not empty
                valid_rows_after_offset_filter.append(
                    (original_row_idx, row_sorted_by_x)
                )
            continue

        # Always include the first box
        valid_segment_in_row.append(row_sorted_by_x[0])

        # Calculate the first offset (between box 0 and box 1)
        prev_offset = row_sorted_by_x[1][0] - row_sorted_by_x[0][0]

        # Always include the second box (it defines the first offset for subsequent comparisons)
        valid_segment_in_row.append(row_sorted_by_x[1])

        # Iterate from the third box onwards (index 2)
        for j in range(1, len(row_sorted_by_x) - 1):
            current_cb = row_sorted_by_x[j + 1]
            prev_cb_in_sequence = row_sorted_by_x[
                j
            ]  # This is the checkbox whose offset we're comparing FROM

            current_offset = current_cb[0] - prev_cb_in_sequence[0]

            if current_offset > X_OFFSET_DEVIATION_THRESHOLD_FACTOR * prev_offset:
                # Discard current box and all subsequent boxes in this row
                discarded_segment_in_row.extend(row_sorted_by_x[j + 1 :])
                break  # Exit inner loop for this row, no more boxes from this row are valid
            else:
                valid_segment_in_row.append(current_cb)
                prev_offset = (
                    current_offset  # Update previous_offset for the next iteration
                )

        # Add segments to appropriate lists
        if valid_segment_in_row:
            valid_rows_after_offset_filter.append(
                (original_row_idx, valid_segment_in_row)
            )
        if (
            discarded_segment_in_row
        ):  # Only add if something was actually discarded from this row
            discarded_rows_by_offset_filter.append(
                (original_row_idx, discarded_segment_in_row)
            )

    return valid_rows_after_offset_filter, discarded_rows_by_offset_filter


def filter_rows_by_x_initial(rows):
    """
    Filters rows based on the deviation of their initial x-coordinate
    from the mean initial x-coordinate of all rows.
    Input rows are expected to be [(original_index_from_prev_filter, [(norm_x, norm_z), ...]), ...]
    Returns:
        valid_rows_content: List of lists of (norm_x, norm_z) content that passed this filter.
        discarded_rows_by_initial_x: List of (original_index, list_of_checkboxes_content)
        mean_x_initial: The mean x-initial of the valid rows.
    """
    valid_rows_content = []  # Initialize here
    discarded_rows_by_initial_x = []  # Initialize here

    row_x_initials_map = {}  # Map (original_index, row_content) for easier processing
    for original_idx_from_prev_filter, row_content in rows:
        if row_content:  # Ensure row is not empty
            row_x_initials_map[original_idx_from_prev_filter] = (
                min(row_content, key=lambda pt: pt[0])[0],
                row_content,
            )
        else:
            # If an empty row makes it here, it effectively gets discarded by this filter's logic
            discarded_rows_by_initial_x.append((original_idx_from_prev_filter, []))
            continue

    x_initial_values = [x for x, _ in row_x_initials_map.values()]

    if not x_initial_values:
        # If no non-empty rows passed to this filter, return empty results,
        # but include any empty rows that were already accumulated as discarded.
        return [], discarded_rows_by_initial_x, 0

    mean_x_initial = statistics.mean(x_initial_values)

    for original_idx, (x_init, row_content) in row_x_initials_map.items():
        if abs(x_init - mean_x_initial) <= X_INITIAL_DEVIATION_THRESHOLD * width:
            valid_rows_content.append(row_content)  # Just the content
        else:
            # Keep original index for context
            discarded_rows_by_initial_x.append((original_idx, row_content))

    return valid_rows_content, discarded_rows_by_initial_x, mean_x_initial


def print_rows_info(label, indexed_rows):
    """Prints detailed information for each row of checkboxes.
    indexed_rows format: [(display_index, [(norm_x, norm_z), ...]), ...]
    """
    print(f"\n--- {label} ---")
    if not indexed_rows:
        print("No rows to display.")
        return

    for display_index, row_content in indexed_rows:  # Using display_index provided
        # Sort by norm_x for offsets
        row_sorted = sorted(row_content, key=lambda pt: pt[0])
        xs = [x for x, _ in row_sorted]
        zs = [z for _, z in row_sorted]

        # Handle empty rows if they somehow got here (shouldn't for valid rows)
        if not xs:
            print(f"Row {display_index + 1}: (Empty row)")
            continue

        median_z = statistics.median(zs)
        # Calculate pairwise offsets only if there's more than one checkbox in the row
        pairwise_offsets = (
            [f"{(xs[j+1] - xs[j]):+.3f}" for j in range(len(xs) - 1)]
            if len(xs) > 1
            else []
        )

        print(
            f"Row {display_index + 1}: z-pos = {median_z:+.3f}, count = {len(xs)}, "
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

    # Initialize sets for tracking final inclusion/discard status (normalized coordinates)
    overall_included_norm_coords = set()
    overall_discarded_norm_coords = set()

    # --- Step 1: Find all potential checkboxes with their normalized and pixel coords ---
    # Each item: (norm_x, norm_z, (x_pixel, z_pixel, w_pixel, h_pixel))
    all_potential_checkboxes_with_coords = find_all_potential_checkboxes(
        contours, width, height
    )

    # --- Step 2: Apply LEFT_SIDE_THRESHOLD filter and populate initial discarded set ---
    # These will be used for row grouping
    checkboxes_passing_left_filter_norm_coords = []
    for norm_x, norm_z, bbox_pixel_coords in all_potential_checkboxes_with_coords:
        if norm_x < LEFT_SIDE_THRESHOLD:
            checkboxes_passing_left_filter_norm_coords.append((norm_x, norm_z))
        else:
            # Discarded by left threshold
            overall_discarded_norm_coords.add((norm_x, norm_z))

    # Sort these checkboxes from top to bottom (by z) for consistent row grouping
    # Sort by norm_z
    checkboxes_passing_left_filter_norm_coords.sort(key=lambda pt: pt[1])

    # --- Step 3: Group initially filtered checkboxes into rows by Z ---
    rows_grouped_by_z = group_checkboxes_by_z(
        checkboxes_passing_left_filter_norm_coords
    )

    # --- Step 4: Filter rows by X-Offset Deviation ---
    # `rows_after_offset_filter`: List of (original_row_idx, list_of_checkboxes_content)
    # `discarded_rows_by_offset`: List of (original_row_idx, list_of_checkboxes_content)
    rows_after_offset_filter, discarded_rows_by_offset = (
        filter_rows_by_x_offset_deviation(rows_grouped_by_z)
    )

    # Add checkboxes from rows/segments discarded by X-offset filter to overall discards
    for _, row_content in discarded_rows_by_offset:
        for cb_norm_x, cb_norm_z in row_content:
            overall_discarded_norm_coords.add((cb_norm_x, cb_norm_z))

    # --- Step 5: Filter rows by X-Initial Deviation ---
    # `valid_rows_content_final`: List of lists of (norm_x, norm_z) content.
    # `discarded_rows_by_initial_x`: List of (original_idx, list_of_checkboxes_content)
    valid_rows_content_final, discarded_rows_by_initial_x, mean_x_initial = (
        filter_rows_by_x_initial(rows_after_offset_filter)
    )

    # Add checkboxes from rows discarded by X-initial filter to overall discards
    for _, row_content in discarded_rows_by_initial_x:
        for cb_norm_x, cb_norm_z in row_content:
            overall_discarded_norm_coords.add((cb_norm_x, cb_norm_z))

    # Populate final included set (these passed ALL filters)
    for row_content in valid_rows_content_final:
        for cb_norm_x, cb_norm_z in row_content:
            overall_included_norm_coords.add((cb_norm_x, cb_norm_z))

    # --- Step 6: Print detailed information about rows ---

    # Prepare valid rows for printing with new sequential indices
    valid_rows_for_printing_indexed = [
        (i, row) for i, row in enumerate(valid_rows_content_final)
    ]
    print_rows_info(
        "Grouped rows by similar Z-coordinates (valid and passed all filters)",
        valid_rows_for_printing_indexed,
    )

    # Print summary stats for valid rows
    all_valid_x_offsets = []
    if valid_rows_for_printing_indexed:
        all_x_initials = [
            min(row, key=lambda pt: pt[0])[0]
            for _, row in valid_rows_for_printing_indexed
        ]
        print(f"\nx-initial mean:   {statistics.mean(all_x_initials):.3f}")
        print(f"x-initial median: {statistics.median(all_x_initials):.3f}")

        # Calculate all x-offsets from all valid rows
        for _, row_content in valid_rows_for_printing_indexed:
            row_sorted = sorted(row_content, key=lambda pt: pt[0])
            xs = [x for x, _ in row_sorted]
            for j in range(len(xs) - 1):
                all_valid_x_offsets.append(xs[j + 1] - xs[j])

        if all_valid_x_offsets:
            print(f"x-offset mean:    {statistics.mean(all_valid_x_offsets):+.3f}")
            print(f"x-offset median:  {statistics.median(all_valid_x_offsets):+.3f}")
        else:
            print("No offsets found for valid rows.")

    if PRINT_DISCARDED:
        # Prepare ALL discarded rows for printing (combining from various stages)
        all_discarded_rows_for_printing = []

        # Add rows discarded by initial X filter
        all_discarded_rows_for_printing.extend(discarded_rows_by_initial_x)

        # Add rows/segments discarded by X-offset filter
        all_discarded_rows_for_printing.extend(discarded_rows_by_offset)

        # Sort all discarded rows by their original index for better readability in output
        all_discarded_rows_for_printing.sort(key=lambda x: x[0])

        if all_discarded_rows_for_printing:
            # Re-index for printing for discarded rows for neatness
            indexed_discarded_rows_for_printing = [
                (i, row_content)
                for i, (_, row_content) in enumerate(all_discarded_rows_for_printing)
            ]
            print_rows_info(
                "Discarded checkboxes (due to any filter):",
                indexed_discarded_rows_for_printing,
            )
        else:
            print("\nNo checkboxes were discarded by the offset or initial X filters.")

    # --- Step 7: Prepare debug data based on final filtering results ---
    final_debug_checkbox_statuses = []
    for norm_x, norm_z, bbox_pixel_coords in all_potential_checkboxes_with_coords:
        if (norm_x, norm_z) in overall_included_norm_coords:
            final_debug_checkbox_statuses.append((bbox_pixel_coords, True))  # Green
        else:
            final_debug_checkbox_statuses.append((bbox_pixel_coords, False))  # Red

    # --- Step 8: Draw and save the debug image ---
    file_name = draw_debug_image(image, final_debug_checkbox_statuses)
    print(f"\nDebug image saved as '{file_name}'")
    print("Green boxes = included checkboxes (passed all filters)")
    print("Red boxes   = disregarded checkboxes (failed any filter)")
