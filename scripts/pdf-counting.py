import os
from pypdf import PdfReader

def count_pdf_pages_in_folder(folder_path):
    """Counts the pages of all PDF files in a specified folder."""
    print(f"Scanning folder: **{folder_path}**\n")

    # Check if the folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    total_pages = 0

    # Iterate over all files in the directory
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)

            try:
                reader = PdfReader(file_path)
                page_count = len(reader.pages)

                print(f"  {filename}: {page_count} pages")
                total_pages += page_count

            except Exception as e:
                print(f"  Error reading {filename}: {e}")

    print(f"\n---")
    print(f"Total pages across all PDF files: {total_pages}")

# --- Example Usage ---
folder_path = r'C:\Users\pulsc\OneDrive\Dateien\Brettspiele\Arkham Horror\2025-11-30 mbprint Order'
count_pdf_pages_in_folder(folder_path)