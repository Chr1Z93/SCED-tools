import os
import json
from concurrent.futures import ThreadPoolExecutor

ROOT_PATH = r"C:\git\SCED-downloads\decomposed\scenario"
EXCLUDED_FOLDERS = {"language-pack", "misc", ".git", ".vscode", "__pycache__"}


def process_file(dirpath, filename):
    file_path = os.path.join(dirpath, filename)
    found_id = None

    try:
        # 1. Extract the ID (external)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            gm_notes_raw = data.get("GMNotes", "")
            if gm_notes_raw:
                try:
                    gm_data = json.loads(gm_notes_raw)
                    found_id = gm_data.get("id")
                except (json.JSONDecodeError, TypeError):
                    pass

        # 2. Extract the ID (external .gmnotes) if not found internally
        if not found_id:
            gmnotes_file = os.path.splitext(file_path)[0] + ".gmnotes"
            if os.path.exists(gmnotes_file):
                with open(gmnotes_file, "r", encoding="utf-8") as f:
                    gm_data = json.load(f)
                    found_id = gm_data.get("id")

        if not found_id:
            return None

        # Split the full path into a list of folder names
        path_parts = dirpath.split(os.sep)

        try:
            # Find where "decomposed" sits in the path
            idx = path_parts.index("decomposed")

            # Grab the two levels immediately following "decomposed"
            # Example: .../decomposed/campaign/Night of the Zealot/cards -> "campaign/Night of the Zealot"
            main_folder = os.path.join(path_parts[idx + 1], path_parts[idx + 2])
            return str(found_id), main_folder
        except (ValueError, IndexError):
            # This happens if "decomposed" isn't in the path or there aren't 2 levels after it.
            return None

    except Exception:
        return None


def generate_id_map():
    id_to_folder_map = {}
    tasks = []

    # Using Max Workers to prevent hitting I/O bottlenecks too hard
    with ThreadPoolExecutor(max_workers=8) as executor:
        for dirpath, dirs, filenames in os.walk(ROOT_PATH):
            # This modifies the dirs list in-place, so os.walk won't visit them
            dirs[:] = [d for d in dirs if d not in EXCLUDED_FOLDERS]

            for filename in filenames:
                if filename.endswith(".json"):
                    tasks.append(executor.submit(process_file, dirpath, filename))

        for task in tasks:
            result = task.result()
            if result:
                card_id, folder_path = result
                id_to_folder_map[card_id] = folder_path

    return id_to_folder_map


if __name__ == "__main__":
    final_map = generate_id_map()
    print(f"Successfully mapped {len(final_map)} IDs.")

    # Optional: Save to a file for review
    with open("id_folder_map.json", "w", encoding="utf-8") as f:
        json.dump(final_map, f, indent=4)
