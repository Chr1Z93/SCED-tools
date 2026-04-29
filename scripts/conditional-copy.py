import shutil
from pathlib import Path

# --- CONFIGURATION ---
SEARCH_FOLDER = Path(r"C:\git\SCED-downloads\decomposed\campaign")  # Folder to scan
SEARCH_TEXT = '"CampaignGuide"'  # Text to look for
TARGET_FOLDER = Path(
    r"C:\git\SCED-downloads\decomposed\language-pack\German - Campaigns\German-Campaigns.GermanC\PDFs.pdfpdf"
)  # Where to copy results


def copy_matching_files():
    # Create target folder if it doesn't exist
    TARGET_FOLDER.mkdir(parents=True, exist_ok=True)

    match_count = 0

    # rglob("*") searches recursively through all subfolders
    for file_path in SEARCH_FOLDER.rglob("*"):

        # Ensure we are only looking at files, not directories
        if file_path.is_file():
            try:
                # Read file content; using errors='ignore' prevents crashes on binary files
                if SEARCH_TEXT in file_path.read_text(
                    encoding="utf-8", errors="ignore"
                ):

                    # Define the destination path
                    dest_path = TARGET_FOLDER / file_path.name

                    # Handle duplicate filenames (optional: appends index if file exists)
                    if dest_path.exists():
                        print(f"ℹ️ Skipped {file_path.name}")
                    else:
                        shutil.copy2(file_path, dest_path)
                        print(f"✅ Copied: {file_path.name}")
                        match_count += 1

            except Exception as e:
                print(f"❌ Could not read {file_path.name}: {e}")

    print(f"\nDone! Copied {match_count} files to '{TARGET_FOLDER.absolute()}'")


if __name__ == "__main__":
    copy_matching_files()
