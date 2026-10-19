import re
import sys
from pathlib import Path

PATTERN = re.compile(
    r'(?P<prefix>"CardID"\s*:\s*)\d+'
    r'(?P<middle>\s*,\s*"CustomDeck"\s*:\s*\{\s*)'
    r'(?P<quote>")\d+(?P<suffix>"\s*:\s*\{)'
)

folder = Path(r"C:\git\SCED-downloads\decomposed\scenario\Traces to Nowhere\TracestoNowhere.63b532\CardSource.238gh2")

def update_file(file_path: Path, counter) -> int:
    text = file_path.read_text(encoding="utf-8")

    def replace(match: re.Match) -> str:
        nonlocal counter
        counter += 1

        return (
            f'{match.group("prefix")}{counter * 100}'
            f'{match.group("middle")}'
            f'{match.group("quote")}{counter}'
            f'{match.group("suffix")}'
        )

    updated_text = PATTERN.sub(replace, text)

    if updated_text != text:
        file_path.write_text(updated_text, encoding="utf-8")
        print(f"{file_path}: updated {counter} block(s)")
    else:
        print(f"{file_path}: no matching blocks found")

    return counter


def main() -> None:
    if not folder.is_dir():
        print(f"Error: folder does not exist: {folder}")
        sys.exit(1)

    files = sorted(folder.rglob("*.json"))

    if not files:
        print(f"No JSON files found in {folder}")
        return

    counter = 0

    for file_path in files:
        counter = update_file(file_path, counter)

    print(f"\nFinished. Updated {counter} block(s) across {len(files)} file(s).")


if __name__ == "__main__":
    main()
