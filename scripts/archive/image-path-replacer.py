# Replaces the image path based on a Excel table

import pandas as pd
import os
import re

DATA_PATH = r"C:\git\SCED-tools\scripts\image-path-replacer-data.xlsx"
FOLDER_PATH = r"C:\git\SCED\objects\AllPlayerCards.15bb07"

def load_excel_data(excel_path):
    df = pd.read_excel(excel_path, dtype={"ID": int, "URL": str})
    return {str(row.ID + 55000): row.URL for _, row in df.iterrows()}


def update_json_files(folder_path, replacements):
    json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]

    for json_file in json_files:
        json_path = os.path.join(folder_path, json_file)

        with open(json_path, "r", encoding="utf-8") as file:
            content = file.read()

        modified = False

        for id_key, new_url in replacements.items():
            pattern = (
                rf'"{id_key}": {{\s*"BackIsHidden": true,\s*"BackURL": '
                rf'"https://steamusercontent-a\.akamaihd\.net/ugc/2342503777940352139/[A-Z0-9]+/",\s*'
                rf'"FaceURL": "([^"]+)"'
            )

            if re.search(pattern, content):
                content = re.sub(
                    pattern,
                    rf'"{id_key}": {{ "BackIsHidden": true, "BackURL": '
                    rf'"https://steamusercontent-a.akamaihd.net/ugc/2342503777940352139/A2D42E7E5C43D045D72CE5CFC907E4F886C8C690/", '
                    rf'"FaceURL": "{new_url}"',
                    content,
                )
                modified = True

        if modified:
            with open(json_path, "w", encoding="utf-8") as file:
                file.write(content)
            print(f"Updated: {json_file}")


def main():
    replacements = load_excel_data(DATA_PATH)
    update_json_files(FOLDER_PATH, replacements)


if __name__ == "__main__":
    main()
