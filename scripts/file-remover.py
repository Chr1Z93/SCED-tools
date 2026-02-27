import os


def cleanup_copies(folder_path):
    # Check if the directory exists
    if not os.path.exists(folder_path):
        print("The specified folder does not exist.")
        return

    print(f"Scanning folder: {folder_path}\n")

    for filename in os.listdir(folder_path):
        # Check if "copy" is in the filename (case-insensitive)
        if " copy" in filename.lower():
            file_path = os.path.join(folder_path, filename)

            # Ensure we are deleting a file and not a subfolder
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted: {filename}")
                except Exception as e:
                    print(f"Error deleting {filename}: {e}")


cleanup_copies(r"C:\git\SCED\objects\AdditionalPlayerCards.2cba6b")
