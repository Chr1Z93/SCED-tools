import json
import re
import os
import platform
import socket
import subprocess
import sys
import tempfile
import time
import threading

# Configuration
HOST = "127.0.0.1"
TTS_LISTEN_PORT = 39999
MY_LISTEN_PORT = 39998
TEMP_DIR = tempfile.gettempdir()
PLATFORM = platform.system()

# State Management
state = {
    "target_guid": "-1",
    "temp_lua": None,
    "temp_xml": None,
    "temp_name": None,
    "temp_guid": None,
    "waiting_for_pull": False,
    "last_errors": {},  # Stores { "error_text": timestamp }
}


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

                        if m_id == 0:
                            states = msg.get("scriptStates", [])
                            obj = states[0]
                            sync_files(
                                obj["name"],
                                obj.get("script", ""),
                                obj.get("ui", ""),
                                obj["guid"],
                                silent=False,
                            )
                        elif m_id == 1:
                            states = msg.get("scriptStates", [])
                            found_target = False

                            for obj in states:
                                # Open editor only if it matches current target
                                if obj["guid"] == state["target_guid"]:
                                    sync_files(
                                        obj["name"],
                                        obj.get("script", ""),
                                        obj.get("ui", ""),
                                        obj["guid"],
                                        silent=not state["waiting_for_pull"],
                                    )
                                    found_target = True

                            state["waiting_for_pull"] = False
                            if not found_target:
                                print(
                                    f"[ERR] Couldn't find target (received {len(states)} scripts)"
                                )
                        elif m_id == 2:
                            print(f"[TTS] {msg.get('message')}")
                        elif m_id == 3:
                            error_text = msg.get("error", "Unknown Error")
                            log_error_throttled(error_text, window=2)
                        elif m_id == 5:
                            print(f"[RET] {msg.get('returnValue')}")
                        elif m_id == 7:
                            print(f"[NEW] Object created ({msg.get('guid')})")
                    except:
                        pass


def log_error_throttled(error_msg, window=5):
    """Prints an error only if it hasn't been printed in the last 'window' seconds."""
    current_time = time.time()
    last_seen = state["last_errors"].get(error_msg, 0)

    if current_time - last_seen > window:
        print(f"[ERR] {error_msg}")
        state["last_errors"][error_msg] = current_time


def get_script_paths(name, guid):
    """Generates standardized paths for Lua and XML files."""
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", name)
    lua_path = os.path.join(TEMP_DIR, f"{clean_name}.{guid}.ttslua")
    xml_path = os.path.join(TEMP_DIR, f"{clean_name}.{guid}.xml")
    return lua_path, xml_path


def sync_files(name, lua_content, xml_content, guid, silent=True):
    """Writes the script and XML to disk and returns the paths."""
    lua_path, xml_path = get_script_paths(name, guid)

    with open(lua_path, "w", encoding="utf-8", newline="") as f:
        f.write(lua_content)
    with open(xml_path, "w", encoding="utf-8", newline="") as f:
        f.write(xml_content)

    if not silent:
        state["temp_lua"] = lua_path
        state["temp_xml"] = xml_path
        state["temp_guid"] = guid
        state["temp_name"] = name

        # Open Lua file last so it is selected
        if os.path.exists(xml_path):
            open_file(xml_path)
        if os.path.exists(lua_path):
            open_file(lua_path)
        print(f"[SYS] Files for {name}.{guid} loaded.")

    return lua_path, xml_path


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


def send_reload(lua_script="", xml_ui=""):
    """Sends Message ID 1 to TTS to trigger a full 'Save & Play' (reloads all scripts)."""
    payload = {
        "messageID": 1,
        "scriptStates": [
            {
                "name": "Global",
                "guid": "-1",
                "script": lua_script,
                "ui": xml_ui,
            }
        ],
    }
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps(payload).encode("utf-8"))
        print("[SYS] Reload command sent to TTS (Save & Play)")
    except Exception as e:
        print(f"[ERR] Reload failed: {e}")


def send_pull():
    """
    Sends Message ID 0 to TTS.
    TTS will respond by sending ALL scripts (ID 1) to our listener.
    """
    state["waiting_for_pull"] = True
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps({"messageID": 0}).encode("utf-8"))
        print("[SYS] Requesting script from TTS...")
    except Exception as e:
        state["waiting_for_pull"] = False
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
        f" ACTIVE LUA     : {os.path.basename(state['temp_lua']) if state['temp_lua'] else 'None'}"
    )
    print(
        f" ACTIVE XML     : {os.path.basename(state['temp_xml']) if state['temp_xml'] else 'None'}"
    )

    print("\n INFO:")
    print("  Use 'global' or '-1' as guid for the Global script.")
    print("  Pushing to Global will reload the savegame.")

    print("\n INTERNAL COMMANDS:")
    print("  target [guid] - Change who receives the Lua code.")
    print("  pull          - Open the Lua and XML as temp files.")
    print("  push          - Send the temp files back to the game.")
    print("  reload        - Reloads the currently loaded TTS game.")
    print("  exit          - Clean up temp files and close.")

    print("\n WORKFLOW:")
    print("  1. In TTS:  Right-click object -> Scripting Editor.")
    print("  2. In Code: Edit the files that just opened.")
    print("  3. In Tool: Type 'push' to live-reload the object.")

    print("\n LUA EXECUTION:")
    print("  Anything else you type is sent directly to the")
    print("  current target (e.g., 'print(self.getName())').")
    print("=" * 50 + "\n")


def send_push():
    # Initialize as empty strings so the variables always exist
    updated_lua = ""
    updated_xml = ""

    # Check if temp files exist
    lua_exist = state["temp_lua"] and os.path.exists(state["temp_lua"])
    xml_exist = state["temp_xml"] and os.path.exists(state["temp_xml"])

    if lua_exist or xml_exist:
        if lua_exist:
            with open(state["temp_lua"], "r", encoding="utf-8") as f:
                updated_lua = f.read()

        if xml_exist:
            with open(state["temp_xml"], "r", encoding="utf-8") as f:
                updated_xml = f.read()

        if state["temp_guid"] == "-1":
            send_reload(updated_lua, updated_xml)
        else:
            # Use [====[ to avoid collisions with scripts containing [[ or ]]
            # Update both Lua and XML via Lua injection
            reload_cmd = (
                f"local obj = getObjectFromGUID('{state['temp_guid']}') "
                f"if obj then "
                f"  obj.setLuaScript([====[{updated_lua}]====]) "
                f"  obj.UI.setXml([====[{updated_xml}]====]) "
                f"  obj.reload() "
                f"else "
                f"  print('Push failed: Object {state['temp_name']}.{state['temp_guid']} no longer exists') "
                f"end"
            )
            send_command(reload_cmd, target_override="-1")
            print(
                f"[SYS] Pushed Lua and XML updates to {state['temp_name']}.{state['temp_guid']}."
            )
    else:
        print("[ERR] No temp files found. Pull a script first.")


def remove_temp_files():
    for key in ["temp_lua", "temp_xml"]:
        if state[key] and os.path.exists(state[key]):
            os.remove(state[key])


if __name__ == "__main__":
    # Start the listener in the background
    threading.Thread(target=listener, daemon=True).start()

    print("=" * 50)
    print("           TTS INTERACTIVE CONSOLE")
    print("-" * 50)
    print("Type 'help' for info, 'exit' to close")
    print("or enter Lua code to execute in TTS.")
    print("=" * 50)

    try:
        while True:
            user_input = input().strip()
            if not user_input:
                continue

            parts = user_input.lower().split()

            if user_input == "exit":
                remove_temp_files()
                sys.exit(0)
            elif user_input == "reload":
                send_reload()
            elif user_input == "help":
                send_help()
            elif user_input == "pull":
                send_pull()
            elif user_input == "push":
                send_push()
            elif parts[0] == "target":
                state["target_guid"] = (
                    "-1" if len(parts) < 2 or parts[1] == "global" else parts[1]
                )
                print(f"[SYS] Target: {state['target_guid']}")

            # --- Send to TTS ---
            else:
                send_command(user_input)

    except KeyboardInterrupt:
        sys.exit(0)
