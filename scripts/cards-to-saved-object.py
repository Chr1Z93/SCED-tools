# This script turns an input folder of card images into a saved object for Tabletop Simulator
# Each subfolder will be turned into a separate bag

import copy
import json
import os
import platform
from pathlib import Path
import re

from datetime import datetime
from modules import tts_templates

BACK_URL = "https://steamusercontent-a.akamaihd.net/ugc/1862806463732171728/E2EBDA19EAF2265F39F3F36C197C7104CA4802E3/"
SOURCE_FOLDER = Path(r"C:\Users\pulsc\Downloads\cards")
START_ID = {"Artifact": 3201, "Item": 3101}
CARD_SCALE = 2.3
EXPANSION = "Surprise Shipment"
GAME_SHORTHAND = "Arnak"
PLATFORM = platform.system()


def natural_sort_key(path: Path):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def get_windows_documents_dir() -> Path:
    """Helper to safely retrieve the Windows Documents folder via registry."""
    try:
        import winreg

        sub_key = (
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        )
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            # 'Personal' is the registry key for the Documents folder
            doc_path_str, _ = winreg.QueryValueEx(key, "Personal")

            # Expand environment variables like %USERPROFILE% if present
            return Path(os.path.expandvars(doc_path_str))
    except Exception:
        # Fallback to standard guess if registry lookup fails
        return Path.home() / "Documents"


def get_output_folder():
    if PLATFORM == "Windows":
        base_dir = get_windows_documents_dir() / "My Games"
    elif PLATFORM == "Darwin":  # macOS
        base_dir = Path.home() / "Library"
    else:  # Linux
        base_dir = Path.home() / ".local" / "share"

    return base_dir / Path("Tabletop Simulator") / "Saves" / "Saved Objects"


def build_card_data(image: Path, card_type: str, card_id: int):
    # Create a copy of the template
    card = copy.deepcopy(tts_templates.CARD)

    # Determine the back url
    # If a file with the same name and "-back" appended exists, use it
    # Otherwise use BACK_URL
    back_image = image.with_name(f"{image.stem}-back{image.suffix}")

    if back_image.exists():
        back_url = str(back_image)
    else:
        back_url = BACK_URL

    # Metadata
    card["GMNotes"] = (
        json.dumps(
            {
                "id": str(card_id),
                "type": card_type,
                "boot": 1,
                "boat": 1,
                "car": 1,
                "plane": 1,
                "cost": 1,
                "points": 1,
                "expansion": EXPANSION,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    card["GUID"] = f"{GAME_SHORTHAND}_{card_id}"

    # Use file name as nickname
    card["Nickname"] = image.stem

    # Image data
    card["CardID"] = "100"
    card["CustomDeck"] = {
        "1": {
            "FaceURL": str(image),
            "BackURL": back_url,
            "NumWidth": 1,
            "NumHeight": 1,
            "BackIsHidden": True,
            "UniqueBack": back_url != BACK_URL,
            "Type": 0,
        }
    }

    # Transform
    card["Transform"]["scaleX"] = CARD_SCALE
    card["Transform"]["scaleZ"] = CARD_SCALE

    return card


def build_bag(card_type: str, images: list[Path], next_id: int):
    """Build a bag containing all cards of one type."""

    contained_objects = []

    for image in sorted(images):
        card_id = next_id
        next_id += 1
        print(f"Processing {image.name} -> {card_id}")

        card = build_card_data(image, card_type, card_id)
        contained_objects.append(card)

    bag = copy.deepcopy(tts_templates.BAG)
    bag["Nickname"] = card_type
    bag["GUID"] = f"{GAME_SHORTHAND}_{card_type}_Bag"
    bag["ContainedObjects"] = contained_objects
    bag["Transform"]["scaleX"] = CARD_SCALE
    bag["Transform"]["scaleY"] = CARD_SCALE
    bag["Transform"]["scaleZ"] = CARD_SCALE

    return bag


def build_tts_json():
    print("Building Saved Object...")

    # Group images by folder
    cards_by_type = {}

    # Loop through all cards in the source folder
    for image in sorted(SOURCE_FOLDER.rglob("*"), key=natural_sort_key):
        if not image.is_file():
            continue

        # If this is a back, skip it
        if image.stem.endswith("-back"):
            continue

        card_type = image.parent.name
        cards_by_type.setdefault(card_type, []).append(image)

    # Create one bag per type
    contained_bags = []

    for card_type, images in sorted(cards_by_type.items()):
        bag = build_bag(
            card_type,
            images,
            START_ID.get(card_type, 1),
        )

        contained_bags.append(bag)

    # Build master bag
    master_Bag = copy.deepcopy(tts_templates.BAG)
    date_stamp = datetime.now().strftime("%Y-%m-%d")
    bag_name = f"{date_stamp} - {GAME_SHORTHAND}"

    master_Bag["Nickname"] = bag_name
    master_Bag["GUID"] = f"{GAME_SHORTHAND}_Bag"
    master_Bag["ContainedObjects"] = contained_bags
    master_Bag["Transform"]["scaleX"] = CARD_SCALE
    master_Bag["Transform"]["scaleY"] = CARD_SCALE
    master_Bag["Transform"]["scaleZ"] = CARD_SCALE

    # Final saved object
    saved_object = copy.deepcopy(tts_templates.SAVED_OBJECT)
    saved_object["ObjectStates"] = [master_Bag]
    out_file = Path(f"{bag_name}.json")

    complete_output_path = get_output_folder() / out_file

    with complete_output_path.open("w", encoding="utf-8") as f:
        json.dump(
            saved_object,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Export complete: {out_file}")


if __name__ == "__main__":
    build_tts_json()
