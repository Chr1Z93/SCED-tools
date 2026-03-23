import socket
import json
import re
from pathlib import Path

# --- CONFIGURATION ---
# Add the paths where your .ttslua or .lua source files live
SOURCE_FOLDERS = [Path(r"C:\git\SCED\src"), Path(r"C:\git\SCED-downloads\src")]
HOST = "127.0.0.1"
TTS_LISTEN_PORT = 39999
MY_LISTEN_PORT = 39998

# Regex to find bundled modules: __bundle_register("module/name", function(...)
BUNDLE_PATTERN = re.compile(
    r'__bundle_register\(\"([^"]+)\"\s*,\s*function\(.*?\)\s*(.*?)\nend\)', re.DOTALL
)


def find_source_file(module_name):
    """Searches SOURCE_FOLDERS for a file matching the module name."""
    extensions = [".ttslua", ".lua"]
    for folder in SOURCE_FOLDERS:
        for ext in extensions:
            potential_path = folder / f"{module_name}{ext}"
            if potential_path.exists():
                return potential_path
    return None


def recompile_script(bundled_code):
    """
    Identifies registered modules and refreshes them from disk,
    explicitly skipping the synthetic '__root' module.
    """
    if "__bundle_register" not in bundled_code:
        return bundled_code

    new_code = bundled_code
    # We use findall to get a static list of matches so replacements
    # don't interfere with the iteration
    matches = list(BUNDLE_PATTERN.finditer(bundled_code))

    for match in matches:
        module_name = match.group(1)
        full_match_text = match.group(0)

        # Skip the __root module
        if module_name == "__root":
            continue

        source_path = find_source_file(module_name)
        if source_path:
            # print(f"  -> Refreshing: {module_name}")
            with open(source_path, "r", encoding="utf-8") as f:
                fresh_content = f.read()

            # We reconstruct the registration but keep the specific
            # function signature from the source if possible.
            updated_register = (
                f'__bundle_register("{module_name}", function(require, _LOADED, __bundle_register, __bundle_modules)\n'
                f"{fresh_content}\n"
                f"end)"
            )

            new_code = new_code.replace(full_match_text, updated_register)
        else:
            print(f"  [!] Source not found for: {module_name} (Skipping)")

    return new_code


def communicate_with_tts():
    """Triggers a Get, Recompiles, and Pushes back to TTS."""
    # Ask TTS for current scripts
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps({"messageID": 0}).encode("utf-8"))
        except ConnectionRefusedError:
            return print("TTS is not running.")

    # Listen for the response
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, MY_LISTEN_PORT))
        s.listen(1)
        conn, _ = s.accept()
        with conn:
            data = b"".join(iter(lambda: conn.recv(4096), b""))
            payload = json.loads(data.decode("utf-8"))

    # Process and Recompile
    updated_states = []
    for state in payload.get("scriptStates", []):
        # print(f"Checking {state['name']} ({state['guid']})...")
        original_script = state.get("script", "")

        new_script = recompile_script(original_script)

        if new_script != original_script:
            # Only add to update list if something changed
            state["script"] = new_script
            updated_states.append(state)

    # Push updates back to TTS
    if updated_states:
        print(f"Pushing updates for {len(updated_states)} object{'s' if len(updated_states) != 1 else ''}...")
        update_msg = {"messageID": 1, "scriptStates": updated_states}
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps(update_msg).encode("utf-8"))
        print("Save & Play triggered.")
    else:
        print("\nNo changes detected. Scripts are up to date.")


if __name__ == "__main__":
    communicate_with_tts()
