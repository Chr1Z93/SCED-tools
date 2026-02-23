# Filters files with a FILTER_STRING and then performs a search & replace on these files

import os

# Config
SEARCH_FOLDER = r"C:\git\SCED-downloads\decomposed\campaign\Edge of the Earth\EdgeoftheEarth.895eaa"
ORIGINAL_STRING = ',\n    "PlayerCard"'
REPLACEMENT_STRING = ',\n    "CleanUpHelper_ignore",\n    "PlayerCard"'
FILTER_STRING = '"Nickname": "Dr. Mala Sinha",'  # must be part of file

# Loop through files
count = 0
for root, dirs, files in os.walk(SEARCH_FOLDER):
    if ".git" in dirs:
        dirs.remove(".git")

    if ".vscode" in dirs:
        dirs.remove(".vscode")

    for file in files:
        file_path = os.path.join(root, file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if FILTER_STRING in content:
                new_content = content.replace(ORIGINAL_STRING, REPLACEMENT_STRING)

                if new_content != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Replaced in: {file_path}")
                    count += 1

        except Exception as e:
            print(f"Error at {file_path}: {e}")

print(f"Updated {count} files.")
