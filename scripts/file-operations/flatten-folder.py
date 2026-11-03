import shutil
from pathlib import Path

FOLDER_PATH = r"C:\Users\pulsc\Downloads\To-Do\Chapter 1 Core Encounters"


def flatten_folder(target_dir):
    # Convert string path to a Path object
    base_path = Path(target_dir).resolve()

    if not base_path.is_dir():
        print(f"Error: {target_dir} is not a valid directory.")
        return

    # Iterate through all files in all subdirectories
    # rglob('*') finds everything recursively
    for item in base_path.rglob("*"):
        if item.is_file():
            # Define the new path (the main folder + the filename)
            destination = base_path / item.name

            # Handle potential filename collisions
            if destination.exists():
                print(
                    f"Skipping {item.name}: A file with this name already exists in the root."
                )
                continue

            # Move the file
            shutil.move(str(item), str(destination))
            print(f"Moved: {item.relative_to(base_path)}")

    # Cleanup empty subfolders
    for folder in sorted(base_path.glob("**/"), reverse=True):
        if folder != base_path:
            try:
                folder.rmdir()  # Only deletes if the folder is empty
            except OSError:
                pass  # Folder wasn't empty, likely due to skipped files


if __name__ == "__main__":
    flatten_folder(FOLDER_PATH)
