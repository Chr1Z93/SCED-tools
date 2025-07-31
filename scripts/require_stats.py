import os
import re
from collections import defaultdict
from pathlib import Path

# Configuration: Path to your Tabletop Simulator project folder
PROJECT_FOLDER = r"C:\git\SCED"
PROJECT_FOLDER_2 = r"C:\git\SCED-downloads"


def analyze_ttsl_requires(base_folder):
    counts = defaultdict(int)
    require_pattern = re.compile(r'require\("([^"]+)"\)')

    for root, _, files in os.walk(base_folder):
        for file_name in files:
            if file_name.endswith((".lua", ".ttslua")):
                with open(Path(root) / file_name, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = require_pattern.findall(content)
                    for required_path_raw in matches:
                        counts[required_path_raw] += 1

    sorted_requires = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return sorted_requires


if __name__ == "__main__":
    if not os.path.isdir(PROJECT_FOLDER):
        print(f"Error: The specified project folder does not exist: {PROJECT_FOLDER}")
        print("Please update the 'PROJECT_FOLDER' variable.")
    else:
        print(f"Scanning '{PROJECT_FOLDER}' for Lua/TTSLua file dependencies...\n")
        ranked_dependencies = analyze_ttsl_requires(PROJECT_FOLDER)

        if ranked_dependencies:
            print("Required File Ranking (> 1):")
            print("----------------------")
            for file_path, count in ranked_dependencies:
                if count > 9:
                    print(f"{count} - {file_path}")
                elif count > 1:
                    print(f" {count} - {file_path}")
        else:
            print("No 'require' statements found.")
