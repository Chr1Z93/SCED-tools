import json
from pathlib import Path

FOLDER = Path(
    r"C:\git\SCED-downloads\decomposed\language-pack\Polish - Player Cards\Polish-PlayerCards.PolishI\Taboo.6b2def"
)

SUFFIX_MAP = {
    "German": "Tabu",
    "Spanish": "Tabú",
    "Polish": "Tabu",
}


def get_suffix(path: Path) -> str:
    """Determine suffix based on the language-pack directory."""
    parts = path.parts

    try:
        index = parts.index("language-pack")
        language = parts[index + 1].split()[0]
    except (ValueError, IndexError):
        raise ValueError(f"Could not determine language from path: {path}")

    try:
        return SUFFIX_MAP[language]
    except KeyError:
        raise ValueError(f"No suffix configured for language: {language}")


def update_nickname(data: dict, suffix: str) -> bool:
    """Append suffix to Nickname if it isn't already present."""
    nickname = data.get("Nickname")

    if not isinstance(nickname, str):
        return False

    nickname_suffix = f" ({suffix})"

    if nickname.endswith(nickname_suffix):
        return False

    data["Nickname"] = nickname + nickname_suffix
    return True


def main():
    for path in FOLDER.rglob("*.json"):
        try:
            suffix = get_suffix(path)

            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not update_nickname(data, suffix):
                continue

            name, identifier = path.stem.rsplit(".", 1)
            new_path = path.with_name(f"{name}{suffix}.{identifier}{path.suffix}")

            if new_path.exists():
                raise FileExistsError(f"Target file already exists: {new_path}")

            with new_path.open("w", encoding="utf-8", newline="\n") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
                file.write("\n")

            path.unlink()

            print(f"Renamed: {path.name} -> {new_path.name}")

        except (json.JSONDecodeError, OSError, ValueError) as error:
            print(f"Failed: {path} ({error})")


if __name__ == "__main__":
    main()
