import os
import json
from pathlib import Path
from collections import OrderedDict
from tool_gui import ToolGUI

# Folders that should never be processed
EXCLUDED_DIRS = {".git", ".github", ".vscode"}

# Setup for the GUI
OPTIONS = {
    "input_folder": {
        "type": "folder",
        "label": "Input folder",
        "default": r"C:\git\SCED-downloads\decomposed\language-pack",
    },
    "types": {
        "type": "multiselect",
        "label": "Card Types",
        "values": ["act", "agenda", "location", "scenario", "enemy", "treachery"],
        "default": ["act", "agenda", "scenario"],
    },
    "max_chars": {"type": "text", "label": "Maximum Character Length"},
}


def embed_metadata(log, input_folder, max_chars):
    """
    Loops through all .json files and embeds GMNotes content if it's short enough.
    """
    log(f"Scanning folder: {input_folder}")
    log(f"Maximum allowed GMNotes character count: {max_chars} characters")

    if not input_folder.exists():
        log(f"Error: The directory {input_folder} was not found.")
        return

    for root, dirs, files in os.walk(input_folder):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        root = Path(root)

        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            file_path = root / file_name

            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # Check for the "GMNotes_path" field
            gmnotes_path_str = json_data.get("GMNotes_path")
            if not gmnotes_path_str:
                continue

            # Construct the path to the .gmnotes file in the same directory
            gmnotes_path = file_path.with_suffix(".gmnotes")

            if not gmnotes_path.exists():
                log(f"Warning: .gmnotes file not found for {file_path}.")
                continue

            # Read the content of the .gmnotes file
            with open(gmnotes_path, "r", encoding="utf-8") as f_gmnotes:
                gmnotes_content = f_gmnotes.read()

            # Check the character count of the content
            note_length = len(gmnotes_content)
            if note_length <= max_chars:
                # Delete the .gmnotes file
                os.remove(gmnotes_path)

                # Add the content as a new "GMNotes" field, removing newline from the end of the string
                json_data["GMNotes"] = gmnotes_content.rstrip("\n")

                # Delete the old "GMNotes_path" field
                del json_data["GMNotes_path"]

                # Sort JSON fields alphabetically before writing
                sorted_json_data = OrderedDict(sorted(json_data.items()))

                # Write the updated JSON back to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(sorted_json_data, f, indent=2, ensure_ascii=False)
                    f.write("\n")  # Add an empty line at the end

                log(f"{json_data["Nickname"]}: Embedded GMNotes")

    log("\nScript finished.")


def run_tool(config, log):
    input_folder = Path(config["input_folder"])
    max_chars = int(config["max_chars"] or 1000)
    embed_metadata(log, input_folder, max_chars)


if __name__ == "__main__":
    ToolGUI("Embed Metadata", OPTIONS, run_tool).show()
