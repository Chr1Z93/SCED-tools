from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
import json
import os
import time

# Config
ROOT_PATH = r"C:\git\SCED-downloads\decomposed"
LP_PATH = r"C:\git\SCED-downloads\decomposed\language-pack\German - Campaigns"
CACHE_FILE = r"C:\git\SCED-tools\scripts\language-pack-completion-stats_cache.json"

EXCLUDED_FOLDERS = {"language-pack", "misc", ".git", ".vscode", "__pycache__"}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_file(dirpath, filename):
    file_path = os.path.join(dirpath, filename)
    found_id = None

    try:
        # Extract the ID (external .gmnotes)
        gmnotes_file = os.path.splitext(file_path)[0] + ".gmnotes"
        if os.path.exists(gmnotes_file):
            with open(gmnotes_file, "r", encoding="utf-8") as f:
                gm_data = json.load(f)
                if "TtsZoopGuid" in gm_data:
                    return None
                found_id = gm_data.get("id")

        if not found_id:
            # Extract the ID (internal)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                gm_notes_raw = data.get("GMNotes", "")
                if gm_notes_raw:
                    try:
                        gm_data = json.loads(gm_notes_raw)
                        if "TtsZoopGuid" in gm_data:
                            return None
                        found_id = gm_data.get("id")
                    except (json.JSONDecodeError, TypeError):
                        pass

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

    start_time = time.perf_counter()

    # 1. Scanning Phase
    logging.info(f"Starting scan in {ROOT_PATH}")
    with ThreadPoolExecutor(max_workers=8) as executor:
        for dirpath, dirs, filenames in os.walk(ROOT_PATH):
            # This modifies the dirs list in-place, so os.walk won't visit them
            dirs[:] = [d for d in dirs if d not in EXCLUDED_FOLDERS]

            for filename in filenames:
                if filename.endswith(".json"):
                    tasks.append(executor.submit(process_file, dirpath, filename))

        scan_done = time.perf_counter()
        logging.info(
            f"Scan complete. Found {len(tasks)} JSON files in {scan_done - start_time:.2f}s"
        )

        # 2. Processing Phase
        for task in tasks:
            result = task.result()
            if result:
                card_id, folder_path = result
                id_to_folder_map[card_id] = folder_path

    end_time = time.perf_counter()
    logging.info(f"Processing complete in {end_time - scan_done:.2f}s")
    logging.info(f"Total time: {end_time - start_time:.2f}s")

    return id_to_folder_map


def generate_lang_id_set(lang_root):
    """
    Crawls the language folder and returns a simple set of all found IDs.
    We reuse the 'process_file' logic but ignore the 'main_folder' return.
    """
    found_ids = set()
    tasks = []

    logging.info(f"Scanning language pack: {lang_root}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        for dirpath, dirs, filenames in os.walk(lang_root):
            # Still exclude noise
            dirs[:] = [d for d in dirs if d not in EXCLUDED_FOLDERS]
            for filename in filenames:
                if filename.endswith(".json"):
                    tasks.append(executor.submit(process_file, dirpath, filename))

        for task in tasks:
            result = task.result()
            if result:
                card_id, _ = result  # We ignore the folder here
                found_ids.add(card_id)

    return found_ids


def get_master_map(force_refresh=False):
    """
    Loads the map from disk if it exists, otherwise generates and saves it.
    """
    if os.path.exists(CACHE_FILE) and not force_refresh:
        logging.info(f"Loading master map from cache: {CACHE_FILE}")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    logging.info("Cache not found or refresh forced. Scanning English files...")
    master_map = generate_id_map()

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(master_map, f, indent=4)

    logging.info(f"Master map cached to {CACHE_FILE}")
    return master_map


def run_localization_report(lang_path, english_map):
    # 1. Map English IDs to their Campaigns for grouping
    campaign_to_ids = defaultdict(set)
    for card_id, campaign in english_map.items():
        campaign_to_ids[campaign].add(card_id)

    # 2. Get all IDs present in the Language Pack
    lang_ids = generate_lang_id_set(lang_path)
    english_ids = set(english_map.keys())

    # 3. Analyze
    unsorted_report = {}
    orphans = lang_ids - english_ids

    for campaign, required_ids in campaign_to_ids.items():
        found = required_ids.intersection(lang_ids)
        missing = required_ids - lang_ids

        total = len(required_ids)
        count = len(found)
        percent = (count / total * 100) if total > 0 else 0

        unsorted_report[campaign] = {
            "completion": f"{percent:.2f}%",
            "stats": f"{count}/{total}",
            "missing": sorted(list(missing)),
        }

    # 4. Sort the report by Campaign Name (the dictionary key)
    # This ensures "Campaign A" appears before "Campaign B" in the JSON and Console
    sorted_report = {k: unsorted_report[k] for k in sorted(unsorted_report)}

    return sorted_report, sorted(list(orphans))


def save_reports(report, orphans, lang_name):
    """Saves the analysis results to timestamped JSON files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ensure a reports directory exists
    report_dir = "localization_reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    # 1. Save Campaign Report
    report_file = os.path.join(report_dir, f"{lang_name}_completion_{timestamp}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    # 2. Save Orphans (only if they exist)
    if orphans:
        orphan_file = os.path.join(
            report_dir, f"{lang_name}_mismatches_{timestamp}.json"
        )
        with open(orphan_file, "w", encoding="utf-8") as f:
            json.dump({"orphans": orphans}, f, indent=4)
        logging.info(f"Orphans saved to: {orphan_file}")

    logging.info(f"Full completion report saved to: {report_file}")


# --- Main Execution ---
if __name__ == "__main__":
    # Step 1: Get the English Source of Truth
    english_id_map = get_master_map()

    # Step 2: Analyze Language Pack
    # Extract language name for the filename (e.g., "German - Campaigns")
    lang_name = os.path.basename(LP_PATH)

    campaign_report, mismatches = run_localization_report(LP_PATH, english_id_map)

    # Output Console Summary
    print(f"\n--- LOCALIZATION REPORT: {lang_name} ---")
    for campaign, data in campaign_report.items():
        print(f"{campaign:.<60} {data['completion']} ({data['stats']})")

    if mismatches:
        print(f"\n[!] Found {len(mismatches)} Orphans (IDs not in English).")

    # Step 3: Export to Files
    save_reports(campaign_report, mismatches, lang_name)
