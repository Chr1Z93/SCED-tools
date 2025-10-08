# Deletes all files that contain the FILTER_STRING in the SEARCH_FOLDER

import os

# Config
SEARCH_FOLDER = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack Korean - Campaigns\LanguagePackKorean-Campaigns.KoreanC"
EXCLUDED_FOLDER = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German\LanguagePackGerman.3ac577\Grundspiel.3c77b5"
FILTER_STRING = "https://steamusercontent-a.akamaihd.net/ugc/2260310642906139495/3EB5D0C93B2343DC206FF062EE00894EBA269B57/"

# Normalize excluded path for comparison
EXCLUDED_FOLDER = os.path.normpath(EXCLUDED_FOLDER)

# Loop through files
for root, dirs, files in os.walk(SEARCH_FOLDER):
    if ".git" in dirs:
        dirs.remove(".git")

    if ".vscode" in dirs:
        dirs.remove(".vscode")

    # Skip excluded folder
    if os.path.commonpath([os.path.normpath(root), EXCLUDED_FOLDER]) == EXCLUDED_FOLDER:
        continue

    for file in files:
        file_path = os.path.join(root, file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if FILTER_STRING in content:
                print(f"Deleting: {file_path}")
                os.remove(file_path)

        except Exception as e:
            print(f"Error at {file_path}: {e}")
