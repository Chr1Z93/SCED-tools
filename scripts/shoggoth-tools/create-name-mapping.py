import json
from pathlib import Path

script_path = Path(__file__).parent.resolve()
english_path = script_path / "alice_en.json"
german_path = script_path / "alice_de.json"


def create_mapping():
    with open(english_path, encoding="utf-8") as file:
        english_project = json.load(file)

    with open(german_path, encoding="utf-8") as file:
        german_project = json.load(file)

    mapping = {}

    print(f"English Project contains {len(english_project["cards"])} cards.")
    print(f"German Project contains {len(german_project["cards"])} cards.")

    german_by_project_number = {
        str(card["project_number"]): card["name"]
        .replace("<dbl>", "")
        .replace("</dbl>", "")
        .strip()
        for card in german_project["cards"]
        if "project_number" in card
    }

    for en_card in english_project["cards"]:
        project_number = str(en_card.get("project_number"))

        if project_number in german_by_project_number:
            en_name = en_card["name"].replace("<dbl>", "").replace("</dbl>", "").strip()
            mapping[en_name] = german_by_project_number[project_number]

    output_file = script_path / "mapping.json"
    output_file.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(f"Name mapping successfully created.")


if __name__ == "__main__":
    create_mapping()
