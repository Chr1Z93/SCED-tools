import json
import re
import os
import platform
import socket
import subprocess
import sys
import tempfile
import threading

# Configuration
HOST = "127.0.0.1"
TTS_LISTEN_PORT = 39999
MY_LISTEN_PORT = 39998
TEMP_DIR = tempfile.gettempdir()
PLATFORM = platform.system()

# State Management
state = {"target_guid": "-1", "temp_file": None, "temp_guid": None}


def listener():
    """Background thread to catch TTS messages."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, MY_LISTEN_PORT))
        s.listen()
        while True:
            conn, _ = s.accept()
            with conn:
                # Loop to ensure we get ALL data from the stream
                chunks = []
                while True:
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)

                data = b"".join(chunks)
                if data:
                    try:
                        msg = json.loads(data.decode("utf-8"))
                        m_id = msg.get("messageID")

                        # ID 0 & 1: Script Data
                        if m_id in [0, 1]:
                            states = msg.get("scriptStates", [])
                            found_target = False

                            for obj in states:
                                # Open editor only if it matches current target
                                if obj["guid"] == state["target_guid"]:
                                    sync_file(
                                        obj["name"],
                                        obj["script"],
                                        obj["guid"],
                                        silent=False,
                                    )
                                    found_target = True

                            if not found_target:
                                print(
                                    f"[ERR] Received {len(states)} scripts, but didn't find target."
                                )

                        elif m_id == 2:
                            print(f"[TTS] {msg.get('message')}")
                        elif m_id == 3:
                            print(f"[ERR] {msg.get('error')}")
                        elif m_id == 5:
                            print(f"[RET] {msg.get('returnValue')}")
                        elif m_id == 7:
                            print(f"[NEW] Object Created ({msg.get('guid')})")
                    except:
                        pass


def get_script_path(name, guid):
    """Generates a standardized path for a script file."""
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", name)
    return os.path.join(TEMP_DIR, f"{clean_name}.{guid}.ttslua")


def sync_file(name, content, guid, silent=True):
    """Writes the script to disk and returns the path."""
    file_path = get_script_path(name, guid)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    if not silent:
        state["temp_file"] = file_path
        state["temp_guid"] = guid
        open_file(file_path)
        print(f"[EDIT] Received script for '{name}' ({guid})")
        print(f"[EDIT] File ready at: {file_path}")
        print(f"[EDIT] Type 'push' to send changes back to TTS.")

    return file_path


def open_file(file_path):
    try:
        if PLATFORM == "Windows":
            os.startfile(file_path)
        elif PLATFORM == "Darwin":  # macOS
            subprocess.call(["open", file_path])
        elif PLATFORM == "Linux":
            subprocess.call(["xdg-open", file_path])
        else:
            print("[ERR] Unknown platform!")
    except Exception as e:
        print(f"[ERR] Could not open file: {e}")


def send_reload(global_script=None):
    """Sends Message ID 1 to TTS to trigger a full 'Save & Play' (reloads all scripts)."""
    payload = {"messageID": 1, "scriptStates": []}

    if global_script:
        payload = {
            "messageID": 1,
            "scriptStates": [{"name": "Global", "guid": "-1", "script": global_script}],
        }
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps(payload).encode("utf-8"))
        print("[SYSTEM] Reload command sent to TTS (Save & Play)")
    except Exception as e:
        print(f"[ERR] Reload failed: {e}")


def send_pull():
    """
    Sends Message ID 0 to TTS.
    TTS will respond by sending ALL scripts (ID 1) to our listener.
    """
    payload = {"messageID": 0}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps(payload).encode("utf-8"))
        print("[SYSTEM] Requesting script from TTS...")
    except Exception as e:
        print(f"[ERR] Pull failed: {e}")


def send_command(script_code, target_override=None):
    """
    Sends Lua code to TTS.
    Uses target_override if provided, otherwise falls back to state['target_guid'].
    """
    # Use override if provided, otherwise use the current global state
    guid = target_override if target_override is not None else state["target_guid"]

    payload = {"messageID": 3, "guid": guid, "script": script_code}

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps(payload).encode("utf-8"))
    except Exception as e:
        print(f"[ERR] Send failed: {e}")


def send_help():
    print("\n" + "=" * 50)
    print(
        f" CURRENT TARGET : {state['target_guid']} "
        + ("(Global)" if state["target_guid"] == "-1" else "")
    )
    print(
        f" ACTIVE TEMP    : {os.path.basename(state['temp_file']) if state['temp_file'] else 'None'}"
    )

    print("\n INFO:")
    print("  Use 'global' or '-1' as guid for the Global script.")
    print("  Pushing to Global will reload the savegame.")

    print("\n INTERNAL COMMANDS:")
    print("  target [guid] - Change who receives the Lua code.")
    print("  pull          - Open the Lua code as temp file.")
    print("  push          - Send the temp file back to the game.")
    print("  reload        - Reloads the currently loaded TTS game.")
    print("  exit          - Clean up temp files and close.")

    print("\n WORKFLOW:")
    print("  1. In TTS: Right-click object -> Scripting Editor.")
    print("  2. In Code: Edit the file that just opened.")
    print("  3. In Tool: Type 'push' to live-reload the object.")

    print("\n LUA EXECUTION:")
    print("  Anything else you type is sent directly to the")
    print("  current target (e.g., 'print(self.getName())').")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    # Start the listener in the background
    threading.Thread(target=listener, daemon=True).start()

    print("=" * 50)
    print("           TTS INTERACTIVE CONSOLE")
    print("-" * 50)
    print("Type 'help' for commands, 'exit' to close")
    print("or enter Lua code to execute in TTS.")
    print("=" * 50)

    try:
        while True:
            user_input = input("> ").strip()
            if not user_input:
                continue

            parts = user_input.lower().split()

            # --- Internal Commands ---
            if user_input == "exit":
                # Clean up temp file on exit
                if state["temp_file"] and os.path.exists(state["temp_file"]):
                    os.remove(state["temp_file"])
                sys.exit(0)
            elif user_input == "reload":
                send_reload()
            elif user_input == "help":
                send_help()
            elif user_input == "pull":
                send_pull()
            elif user_input == "push":
                if state["temp_file"] and os.path.exists(state["temp_file"]):
                    with open(state["temp_file"], "r", encoding="utf-8") as f:
                        updated_script = f.read()

                    if state["temp_guid"] == "-1":
                        send_reload(updated_script)
                    else:
                        # Use [====[ to avoid collisions with scripts containing [[ or ]]
                        reload_cmd = (
                            f"local obj = getObjectFromGUID('{state['temp_guid']}') "
                            f"if obj then "
                            f"  obj.setLuaScript([====[{updated_script}]====]) "
                            f"  obj.reload() "
                            f"else "
                            f"  print('Push failed: Object {state['temp_guid']} no longer exists') "
                            f"end"
                        )
                        send_command(reload_cmd, target_override="-1")
                        print(f"[SYSTEM] Pushed updates to {state['temp_guid']}.")
                else:
                    print("[ERR] No temp file found. Pull a script first.")

            elif parts[0] == "target":
                state["target_guid"] = (
                    "-1" if len(parts) < 2 or parts[1] == "global" else parts[1]
                )
                print(f"[SYSTEM] Target: {state['target_guid']}")

            # --- Send to TTS ---
            else:
                send_command(user_input)

    except KeyboardInterrupt:
        sys.exit(0)
