import json
import pyperclip


def main():
    code = pyperclip.paste().strip()
    result = json.loads(code)

    if not isinstance(result, str):
        raise ValueError("Clipboard contents must be a JSON-encoded string.")

    pyperclip.copy(result)
    print(f"Converted {len(code):,} → {len(result):,} characters.")


if __name__ == "__main__":
    main()
