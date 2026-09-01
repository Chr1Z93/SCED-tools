# Automatically escapes / unescapes the clipboard content
import json
import pyperclip


def main():
    text = pyperclip.paste().strip()

    try:
        # Try to decode as JSON
        result = json.loads(text)

        if isinstance(result, str):
            pyperclip.copy(result)
            print(f"Decoded JSON string: {len(text):,} → {len(result):,} characters.")
            return

    except json.JSONDecodeError:
        pass

    # Alternatively, encode as JSON
    result = json.dumps(text, ensure_ascii=False).replace("\\r", "")
    pyperclip.copy(result)
    print(f"Encoded to JSON string: {len(text):,} → {len(result):,} characters.")


if __name__ == "__main__":
    main()
