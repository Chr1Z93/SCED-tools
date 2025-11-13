import re
from pathlib import Path

# --- 1. Define File Paths ---
NEW_DATA_FOLDER = Path(r"C:\git\SCED-downloads\src\localization\es\playercards")
ORIGINAL_FOLDER = Path(
    r"C:\git\SCED-downloads\src\localization\es\playercards\customizable"
)


# --- Data Extraction Function (Unchanged) ---
def extract_new_data(new_content):
    """Extracts boxSize, xInitial, xOffset, and posZ table from the new file content."""

    new_data = {}

    # Extract single variable assignments (boxSize, xInitial, xOffset)
    for var_name in ["boxSize", "xInitial", "xOffset"]:
        match = re.search(rf"{re.escape(var_name)}\s*=\s*(\S+)", new_content)
        if match:
            new_data[var_name] = match.group(1)

    # Extract the multi-line posZ table (List of values)
    posZ_match = re.search(r"posZ\s*=\s*\{([^}]+)\}", new_content, re.DOTALL)
    if posZ_match:
        posZ_values = [v.strip() for v in posZ_match.group(1).split(",") if v.strip()]
        new_data["posZ_values"] = posZ_values
    else:
        new_data["posZ_values"] = []

    return new_data


# --- Script Modification Function (Unchanged in logic) ---
def merge_data(original_content, new_data, filename):
    """Applies the new data to the original script content."""

    modified_content = original_content
    updates_made = False

    # 3.1. Update the three direct variable assignments
    for var_name, new_value in [
        ("boxSize", new_data.get("boxSize")),
        ("xInitial", new_data.get("xInitial")),
        ("xOffset", new_data.get("xOffset")),
    ]:
        if new_value:
            pattern = re.compile(rf"^{re.escape(var_name)}\s*=\s*.*$", re.MULTILINE)
            replacement = f"{var_name} = {new_value}"
            modified_content = pattern.sub(replacement, modified_content, count=1)
            updates_made = True

    # 3.2. Update the posZ values inside the customizations table
    posZ_values = new_data.get("posZ_values", [])

    if posZ_values:
        # Define the replacement function closure
        def replace_posz(match):
            nonlocal posZ_values
            nonlocal index

            # Use index to pull the next value from the list
            if index <= len(posZ_values):
                new_line = f"      posZ = {posZ_values[index - 1]},"
                index += 1
                return new_line
            return match.group(0)  # Should not happen if data is correct

        # This pattern matches the line 'posZ = [value],' including the value.
        posZ_line_pattern = re.compile(r"^\s*posZ\s*=\s*[^,]+[,\}]", re.MULTILINE)

        # Reset index counter before replacement
        index = 1

        modified_content = posZ_line_pattern.sub(replace_posz, modified_content)
        updates_made = True

    if updates_made:
        print(f"✅ Merged data into **{filename}**.")
    else:
        print(f"⚠️ No significant updates applied to **{filename}**.")

    return modified_content


# --- 4. Main Execution Block (Revised) ---
def main():
    print("--- Starting Batch Data Merge ---")
    print(f"New Data Folder: {NEW_DATA_FOLDER}")
    print(f"Original Folder: {ORIGINAL_FOLDER}\n")

    # Check if folders exist
    if not NEW_DATA_FOLDER.is_dir() or not ORIGINAL_FOLDER.is_dir():
        print("Error: One or both specified folders do not exist.")
        return

    # List files in the new data folder to determine which files to process
    new_data_files = [f for f in NEW_DATA_FOLDER.iterdir() if f.is_file()]

    files_processed = 0

    for new_file_path in new_data_files:
        filename = new_file_path.name

        # Construct the path to the original file in the other folder
        original_file_path = ORIGINAL_FOLDER / filename

        if not original_file_path.is_file():
            # Skip files in the new folder that don't have a matching counterpart
            print(f"  Skipping {filename}: No matching file found in original folder.")
            continue

        try:
            # 1. Load new data
            with open(new_file_path, "r", encoding="utf-8") as f:
                new_content = f.read()

            # 2. Load original script
            with open(original_file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            # 3. Extract data from the new file
            extracted_data = extract_new_data(new_content)

            # Check if essential data was extracted
            if not extracted_data.get("boxSize") or not extracted_data.get(
                "posZ_values"
            ):
                print(f"  Skipping {filename}: Could not extract data.")
                continue

            # 4. Merge data
            modified_script = merge_data(original_content, extracted_data, filename)

            # 5. Overwrite the original file
            # Note: Using 'w' mode overwrites existing content
            with open(original_file_path, "w", encoding="utf-8") as f:
                f.write(modified_script)

            files_processed += 1

        except Exception as e:
            print(f"  ❌ An error occurred processing {filename}: {e}")
            continue

    print(f"\n--- Batch Merge Complete: {files_processed} file(s) updated. ---")


if __name__ == "__main__":
    main()
