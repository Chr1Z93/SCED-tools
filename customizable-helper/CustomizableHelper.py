import cv2
import os
import statistics
import sys
import tempfile
import urllib.request
from urllib.parse import urlparse, unquote

# Configuration parameters
IMAGE_PATH = r""
PRINT_DETAILS = True
PRINT_DISCARDED = True

# Box identification parameters
MIN_BOX_RATIO = 0.9
MAX_BOX_RATIO = 1.1
MIN_BOX_SIZE = 20 / 1050
MAX_BOX_SIZE = 45 / 1050
MIN_BOX_SOLIDITY = 0.7
MIN_BOX_CORNERS = 3
MAX_BOX_CORNERS = 10

# Ignore boxes outside of this
LEFT_SIDE_THRESHOLD_MIN = -0.5
LEFT_SIDE_THRESHOLD_MAX = -0.9

# Used for grouping boxes into rows
Z_ROW_THRESHOLD = 0.03 / 1050

# Used to ignore outliers in row's initial x-position
X_INITIAL_DEVIATION_THRESHOLD = 0.07 / 1050

# Used to ignore outliers in x-offset
X_OFFSET_DEVIATION_THRESHOLD_FACTOR = 1.1

# Weird standard size for custom cards in TTS, but it is what it is
TTS_CARD_HEIGHT = 3.062473

# Don't ask me why this is necessary, it just works (emprically derived, should have been 1)
TTS_FIRST_X_OFFSET_FACTOR = 0.775


def is_url(path):
    return path.startswith("http://") or path.startswith("https://")


def download_temp_image(url):
    try:
        print(f"Downloading image from URL: {url}")

        # Try to extract the filename from the URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        filename = unquote(filename)

        # Fallback if URL has no filename
        if not filename or "." not in filename:
            filename = "CustomizableCard.png"

        # Create a full temp path with that filename
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{filename}")

        urllib.request.urlretrieve(url, temp_path)
        return temp_path

    except Exception as e:
        print(f"Error downloading image:\n  {e}")
        return None


def get_image_path():
    global IMAGE_PATH

    # Priority 1: Use IMAGE_PATH if defined
    if IMAGE_PATH:
        if is_url(IMAGE_PATH):
            IMAGE_PATH = download_temp_image(IMAGE_PATH)
            return

        if os.path.isfile(IMAGE_PATH):
            return

        temp_path = get_global_path(IMAGE_PATH)
        if os.path.isfile(temp_path):
            IMAGE_PATH = temp_path
            return

    # Priority 2: Use CLI argument (drag-and-drop)
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if is_url(arg_path):
            IMAGE_PATH = download_temp_image(arg_path)
            return

        if os.path.isfile(arg_path):
            IMAGE_PATH = arg_path
            return

        temp_path = get_global_path(IMAGE_PATH)
        if os.path.isfile(temp_path):
            IMAGE_PATH = temp_path
            return

        print(f"Error: Invalid path or file does not exist:\n  {arg_path}")

    # Priority 3: Prompt the user (and strip spaces and quotes)
    IMAGE_PATH = input(
        "Please enter the path to the image file (local or global): "
    ).strip(" \"'")
    if is_url(IMAGE_PATH):
        IMAGE_PATH = download_temp_image(IMAGE_PATH)
        return

    if os.path.isfile(IMAGE_PATH):
        return

    temp_path = get_global_path(IMAGE_PATH)
    if os.path.isfile(temp_path):
        IMAGE_PATH = temp_path
        return

    print(f"Error: File not found:\n  {IMAGE_PATH}")


def generate_lua_script(valid_rows_data, global_mean_x_initial, global_mean_x_offset):
    """Generates a string formatted for a .ttslua file based on the detected checkboxes."""
    lua_script_lines = []

    # Add the card name
    card_name, _ = extract_image_name_and_extension()
    lua_script_lines.append(f"-- Customizable Cards: {card_name}\n")
    lua_script_lines.append(f"boxSize  = 40")

    # The TTS script assumes that the first box is at x_initial + 1x x_offset
    # so we substract the offset for this output
    lua_script_lines.append(
        f"xInitial = {global_mean_x_initial - TTS_FIRST_X_OFFSET_FACTOR * global_mean_x_offset:.3f}"
    )
    lua_script_lines.append(f"xOffset  = {global_mean_x_offset:.3f}\n")

    # Start the customizations table
    lua_script_lines.append("customizations = {")

    for idx, row_content in valid_rows_data:
        # Use the median Z for posZ
        pos_z = statistics.median([cb_z for _, cb_z in row_content])

        lua_script_lines.append(f"  [{idx + 1}] = {{")  # Lua tables are 1-indexed
        lua_script_lines.append("    checkboxes = {")

        # This is a purely empirical factor to fix the values for TTS
        lua_script_lines.append(f"      posZ = {pos_z:.3f},")
        lua_script_lines.append(f"      count = {len(row_content)}")
        lua_script_lines.append("    }")
        lua_script_lines.append("  },")

    lua_script_lines.append("}")
    lua_script_lines.append('require("playercards/customizable/UpgradeSheetLibrary")')
    lua_script_block = "\n".join(lua_script_lines)

    # Get base script name
    base_script_path = get_global_path("CustomizableScript.ttslua")

    # Read and replace the insert marker in the base script
    with open(base_script_path, "r", encoding="utf-8") as f:
        base_script = f.read()

    replaced_name = base_script.replace("<<TTS_FILE_NAME>>", card_name)
    replaced_lua = replaced_name.replace("--<<TTS_LUA_SCRIPT>>", lua_script_block)

    return replaced_lua


def get_global_path(localPath):
    # os.path.abspath(__file__) gets the absolute path of the script file.
    # os.path.dirname() extracts the directory part from that path.
    script_directory = os.path.dirname(os.path.abspath(__file__))
    global_path = os.path.join(script_directory, localPath)
    return global_path


def is_valid_checkbox(w, h):
    """Checks if dimensions match checkbox criteria."""
    return (
        MIN_BOX_RATIO < w / h < MAX_BOX_RATIO
        and MIN_BOX_SIZE < w / height < MAX_BOX_SIZE
        and MIN_BOX_SIZE < h / height < MAX_BOX_SIZE
    )


def get_normalized_coords(x, z, w, h):
    """Converts pixel coordinates to normalized card coordinates (x, z)."""
    center_x = x + w / 2
    center_z = z + h / 2

    # Scale factor: pixels to TTS units for z-axis
    pixels_to_units = TTS_CARD_HEIGHT / height

    # Vertical (z): top to bottom becomes - to +
    norm_z = (center_z - height / 2) * pixels_to_units

    # Horizontal (x): apply same scale factor to preserve aspect ratio
    norm_x = (center_x - width / 2) * pixels_to_units

    return norm_x, norm_z


def find_all_potential_checkboxes(contours):
    """Finds all potential checkboxes based on geometry and shape."""

    potential_checkboxes = []

    for cnt in contours:
        x_pixel, z_pixel, w_pixel, h_pixel = cv2.boundingRect(cnt)

        # Shape analysis
        area = cv2.contourArea(cnt)
        bbox_area = w_pixel * h_pixel
        solidity = area / bbox_area if bbox_area > 0 else 0

        # Approximate contour to count corners
        epsilon = 0.02 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        corner_count = len(approx)

        # Apply filters
        if (
            is_valid_checkbox(w_pixel, h_pixel)
            and solidity > MIN_BOX_SOLIDITY
            and MIN_BOX_CORNERS <= corner_count <= MAX_BOX_CORNERS
        ):
            norm_x, norm_z = get_normalized_coords(x_pixel, z_pixel, w_pixel, h_pixel)
            potential_checkboxes.append(
                (norm_x, norm_z, (x_pixel, z_pixel, w_pixel, h_pixel))
            )

    return potential_checkboxes


def draw_debug_image(image, final_checkbox_statuses):
    """Draws bounding boxes on the image for debugging based on final inclusion status."""
    debug_image = image.copy()
    for (x, z, w, h), color in final_checkbox_statuses:
        cv2.rectangle(debug_image, (x, z), (x + w, z + h), color, 2)

    filename_base, file_extension = extract_image_name_and_extension()

    # Construct the new debug filename
    output_filename = f"{filename_base}_debug{file_extension}"

    # Combine the script directory and the filename to create the full output path
    output_path = get_global_path(output_filename)

    cv2.imwrite(output_path, debug_image)

    return output_filename


def extract_image_name_and_extension():
    original_filename_with_ext = os.path.basename(IMAGE_PATH)  # type: ignore
    filename_base, file_extension = os.path.splitext(original_filename_with_ext)
    return filename_base, file_extension


def group_checkboxes_by_z(checkboxes):
    """Groups checkboxes into rows based on their z-coordinates."""
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


def calculate_global_median_x_offset(rows_grouped_by_z):
    all_offsets = []
    for row in rows_grouped_by_z:
        # Sort by x to calculate offsets
        row_sorted = sorted(row, key=lambda pt: pt[0])
        xs = [x for x, _ in row_sorted]
        for i in range(len(xs) - 1):
            offset = xs[i + 1] - xs[i]
            all_offsets.append(offset)
    if all_offsets:
        return statistics.median(all_offsets)
    else:
        return 0


def filter_rows_by_x_offset_deviation(rows_grouped_by_z, global_mean_offset):
    """
    Filters checkboxes within each row based on x-offset deviation from the previous box.
    If an x-offset is too large, that box and all subsequent boxes in the row are discarded.
    Input rows_grouped_by_z: list of lists of (norm_x, norm_z) tuples.
    Returns:
        valid_rows_after_offset_filter: List of (original_row_idx, list_of_checkboxes_content)
        discarded_rows_by_x_offset_filter: List of (original_row_idx, list_of_checkboxes_content)
    """
    valid_rows_after_offset_filter = []
    discarded_rows_by_x_offset_filter = []

    for original_row_idx, row_content in enumerate(rows_grouped_by_z):
        # Sort boxes within the row by x-coordinate for offset calculation
        row_sorted_by_x = sorted(row_content, key=lambda pt: pt[0])

        # Only include the first box initially
        valid_segment_in_row = [row_sorted_by_x[0]]
        discarded_segment_in_row = []

        # Iterate from the second box onwards (index 1) to check the offset relative to the *previous valid* box
        for j in range(len(row_sorted_by_x) - 1):  # j goes from 0 to len-2
            current_cb = row_sorted_by_x[j + 1]

            # This is the checkbox whose offset we're comparing FROM
            prev_cb = row_sorted_by_x[j]

            current_offset_deviation = (current_cb[0] - prev_cb[0]) / global_mean_offset

            if current_offset_deviation > X_OFFSET_DEVIATION_THRESHOLD_FACTOR:
                # Discard current box and all subsequent boxes in this row
                discarded_segment_in_row.extend(row_sorted_by_x[j + 1 :])
                break  # Exit inner loop for this row, no more boxes from this row are valid
            else:
                valid_segment_in_row.append(current_cb)

        # Add segments to appropriate lists
        if valid_segment_in_row:
            valid_rows_after_offset_filter.append(
                (original_row_idx, valid_segment_in_row)
            )

        # Only add if something was actually discarded from this row
        if discarded_segment_in_row:
            discarded_rows_by_x_offset_filter.append(
                (original_row_idx, discarded_segment_in_row)
            )

    return valid_rows_after_offset_filter, discarded_rows_by_x_offset_filter


def filter_rows_by_x_initial(rows):
    """
    Filters rows based on the deviation of their initial x-coordinate
    from the mean initial x-coordinate of all rows.
    Input rows are expected to be [(original_index_from_prev_filter, [(norm_x, norm_z), ...]), ...]
    Returns:
        valid_rows_content: List of lists of (norm_x, norm_z) content that passed this filter.
        discarded_rows_by_x_initial: List of (original_index, list_of_checkboxes_content)
    """
    valid_rows_content = []
    discarded_rows_by_x_initial = []

    row_x_initials_map = {}  # Map (original_index, row_content) for easier processing
    for original_idx_from_prev_filter, row_content in rows:
        if row_content:  # Ensure row is not empty
            row_x_initials_map[original_idx_from_prev_filter] = (
                min(row_content, key=lambda pt: pt[0])[0],
                row_content,
            )
        else:
            # If an empty row makes it here, it effectively gets discarded by this filter's logic
            discarded_rows_by_x_initial.append((original_idx_from_prev_filter, []))
            continue

    x_initial_values = [x for x, _ in row_x_initials_map.values()]

    if not x_initial_values:
        # If no non-empty rows passed to this filter, return empty results,
        # but include any empty rows that were already accumulated as discarded.
        return [], discarded_rows_by_x_initial

    mean_x_initial = statistics.mean(x_initial_values)

    for original_idx, (x_init, row_content) in row_x_initials_map.items():
        if abs(x_init - mean_x_initial) <= X_INITIAL_DEVIATION_THRESHOLD * height:
            valid_rows_content.append(row_content)  # Just the content
        else:
            # Keep original index for context
            discarded_rows_by_x_initial.append((original_idx, row_content))

    return valid_rows_content, discarded_rows_by_x_initial


def print_rows_info(indexed_rows):
    """Prints detailed information for each row of checkboxes."""
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
    get_image_path()

    # Load and preprocess the image
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        input(f"Error: Could not load image at {IMAGE_PATH}. Press Enter to exit...")
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

    # Find all potential checkboxes with their normalized and pixel coords
    # Each item: (norm_x, norm_z, (x_pixel, z_pixel, w_pixel, h_pixel))
    all_potential_checkboxes = find_all_potential_checkboxes(contours)

    # Apply LEFT_SIDE_THRESHOLD filter and populate initial discarded set
    checkboxes_after_left_filter = []
    for norm_x, norm_z, bbox_pixel_coords in all_potential_checkboxes:
        if LEFT_SIDE_THRESHOLD_MAX < norm_x < LEFT_SIDE_THRESHOLD_MIN:
            checkboxes_after_left_filter.append((norm_x, norm_z))
        else:
            overall_discarded_norm_coords.add((norm_x, norm_z))

    # Sort these checkboxes from top to bottom (by z) for consistent row grouping
    checkboxes_after_left_filter.sort(key=lambda pt: pt[1])

    # Group initially filtered checkboxes into rows by Z
    rows_grouped_by_z = group_checkboxes_by_z(checkboxes_after_left_filter)

    # Calculate global median x-offset from initially grouped rows
    global_mean_x_offset = calculate_global_median_x_offset(rows_grouped_by_z)

    # Filter rows by X-Offset Deviation
    # `rows_after_offset_filter`: List of (original_row_idx, list_of_checkboxes_content)
    # `discarded_rows_by_x_offset`: List of (original_row_idx, list_of_checkboxes_content)
    rows_after_offset_filter, discarded_rows_by_x_offset = (
        filter_rows_by_x_offset_deviation(rows_grouped_by_z, global_mean_x_offset)
    )

    # Add checkboxes from rows/segments discarded by X-offset filter to overall discards
    for _, row_content in discarded_rows_by_x_offset:
        for cb_norm_x, cb_norm_z in row_content:
            overall_discarded_norm_coords.add((cb_norm_x, cb_norm_z))

    # Filter rows by X-Initial Deviation
    # `rows_after_initial_filter`: List of lists of (norm_x, norm_z) content.
    # `discarded_rows_by_x_initial`: List of (original_idx, list_of_checkboxes_content)
    rows_after_initial_filter, discarded_rows_by_x_initial = filter_rows_by_x_initial(
        rows_after_offset_filter
    )

    # Add checkboxes from rows discarded by x-initial filter to overall discards
    for _, row_content in discarded_rows_by_x_initial:
        for cb_norm_x, cb_norm_z in row_content:
            overall_discarded_norm_coords.add((cb_norm_x, cb_norm_z))

    # Populate final included set (these passed ALL filters)
    for row_content in rows_after_initial_filter:
        for cb_norm_x, cb_norm_z in row_content:
            overall_included_norm_coords.add((cb_norm_x, cb_norm_z))

    # Prepare valid rows for printing with new sequential indices
    valid_rows_final = [(i, row) for i, row in enumerate(rows_after_initial_filter)]

    # Calculate all x-initials from all valid rows
    all_valid_x_initials = [
        min(row, key=lambda pt: pt[0])[0] for _, row in valid_rows_final
    ]

    # Calculate all x-offsets from all valid rows
    all_valid_x_offsets = []
    for _, row_content in valid_rows_final:
        row_sorted = sorted(row_content, key=lambda pt: pt[0])
        xs = [x for x, _ in row_sorted]
        for j in range(len(xs) - 1):
            all_valid_x_offsets.append(xs[j + 1] - xs[j])

    # Calculate summary stats
    if not all_valid_x_initials:
        input(f"Error: Didn't find any boxes. Press Enter to exit...")
        exit()

    global_x_initial_mean = statistics.mean(all_valid_x_initials)
    global_x_initial_median = statistics.median(all_valid_x_initials)

    if not all_valid_x_offsets:
        global_x_offset_mean = 0
        global_x_offset_median = 0
    else:
        global_x_offset_mean = statistics.mean(all_valid_x_offsets)
        global_x_offset_median = statistics.median(all_valid_x_offsets)

    if PRINT_DETAILS:
        # Print summary stats
        print(f"\n--- Grouped rows by Z-coordinates (valid and passed all filters) ---")
        print_rows_info(valid_rows_final)

        print(f"\nx-initial mean:   {global_x_initial_mean:.3f}")
        print(f"x-initial median: {global_x_initial_median:.3f}")
        print(f"x-offset mean:    {global_x_offset_mean:+.3f}")
        print(f"x-offset median:  {global_x_offset_median:+.3f}")
        print("")

    if PRINT_DISCARDED:
        # Prepare ALL discarded rows for printing (combining from various stages)
        all_discarded_rows_for_printing = []
        all_discarded_rows_for_printing.extend(discarded_rows_by_x_initial)
        all_discarded_rows_for_printing.extend(discarded_rows_by_x_offset)

        # Sort all discarded rows by their original index for better readability in output
        all_discarded_rows_for_printing.sort(key=lambda x: x[0])

        if all_discarded_rows_for_printing:
            # Re-index for printing for discarded rows for neatness
            indexed_discarded_rows_for_printing = [
                (i, row_content)
                for i, (_, row_content) in enumerate(all_discarded_rows_for_printing)
            ]
            print(f"--- Discarded checkboxes (due to filters) ---")
            print_rows_info(indexed_discarded_rows_for_printing)
        else:
            print("No checkboxes were discarded by the filters.")

        print("")

    # Prepare debug data based on final filtering results
    final_debug_checkbox_statuses = []
    for norm_x, norm_z, bbox_pixel_coords in all_potential_checkboxes:
        if (norm_x, norm_z) in overall_included_norm_coords:
            color = (0, 255, 0)  # Green
        else:
            color = (0, 0, 255)  # Red

        final_debug_checkbox_statuses.append((bbox_pixel_coords, color))

    # Draw and save the debug image
    file_name = draw_debug_image(image, final_debug_checkbox_statuses)
    print(f"Debug image saved as '{file_name}'")
    print("  - Green boxes =    included checkboxes (passed all filters)")
    print("  - Red boxes   = disregarded checkboxes (failed any filter)")
    print("")

    # Generate and save TTSLua File
    filename_base, _ = extract_image_name_and_extension()
    output_filename = f"{filename_base}_script.ttslua"
    output_path = get_global_path(output_filename)

    lua_output_string = generate_lua_script(
        valid_rows_final,
        global_x_initial_mean,
        global_x_offset_mean,
    )

    try:
        with open(output_path, "w") as f:
            f.write(lua_output_string)
        print(f"Lua script saved as '{output_filename}'")
    except IOError as e:
        print(f"Error saving Lua output to file: {e}")

    input("\nDone. Press Enter to exit...")
