# Checks for the existence of a front for each back in a folder of Arkham image files

import os

INPUT_FOLDER = r"C:\Users\pulsc\Downloads\To-Do\FHV - DE\Encounter Cards\output"
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff")


def analyse():
    for root, _, files in os.walk(INPUT_FOLDER):
        for file_name in files:
            if file_name.lower().endswith(VALID_EXTENSIONS) and "-back" in file_name:
                # Look for front (without "-back")
                file_path = os.path.join(root, file_name.replace("-back", ""))
                if not os.path.exists(file_path):
                    print(f"Missing front for {file_name}!")


if __name__ == "__main__":
    analyse()
    print("Analysis completed.")
