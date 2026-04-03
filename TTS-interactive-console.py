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
                data = conn.recv(65536)
                if data:
                    try:
                        msg = json.loads(data.decode("utf-8"))
                        m_id = msg.get("messageID")

                        # ID 0: Script Data (User clicked 'Scripting Editor' in-game)
                        if m_id == 0:
                            states = msg.get("scriptStates", [])
                            if states:
                                obj = states[0]
                                handle_incoming_script(
                                    obj["name"], obj["script"], obj["guid"]
                                )

                        elif m_id == 2:
                            print(f"\r[TTS]: {msg.get('message')}\n> ", end="")
                        elif m_id == 3:
                            print(f"\r[ERR]: {msg.get('error')}\n> ", end="")
                        elif m_id == 5:
                            print(f"\r[RET]: {msg.get('returnValue')}\n> ", end="")
                        elif m_id == 7:
                            print(
                                f"\r[NEW]: Object Created ({msg.get('guid')})\n> ",
                                end="",
                            )
                    except:
                        pass


def handle_incoming_script(name, content, guid):
    """Saves the incoming script to a named temp file."""
    # Clean the name: Replace non-alphanumeric with underscores
    clean_name = re.sub(r"[^a-zA-Z0-9]", "_", name)
    filename = f"{clean_name}.{guid}.ttslua"
    file_path = os.path.join(TEMP_DIR, filename)

    # Write the content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    state["temp_file"] = file_path
    state["temp_guid"] = guid

    # Attempt to open temp file
    try:
        if PLATFORM == "Windows":
            os.startfile(file_path)
        elif PLATFORM == "Darwin":  # macOS
            subprocess.call(["open", file_path])
        elif PLATFORM == "Linux":
            subprocess.call(["xdg-open", file_path])
        else:
            print("Unknown platform!")
    except Exception as e:
        print(f"[!] Could not auto-open file: {e}")

    print(f"\n\r[EDIT]: Received script for '{name}' ({guid})")
    print(f"[EDIT]: File ready at: {file_path}")
    print(f"[EDIT]: Type 'push' to send changes back to TTS.\n> ", end="")


def send_reload():
    """Sends Message ID 1 to TTS to trigger a full 'Save & Play' (reloads all scripts)."""
    payload = {"messageID": 1, "scriptStates": []}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps(payload).encode("utf-8"))
        print("\r[SYSTEM]: Reload command sent to TTS (Save & Play).\n> ", end="")
    except Exception as e:
        print(f"\r[!] Reload failed: {e}\n> ", end="")


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
        print(f"\r[!] Send failed: {e}\n> ", end="")


def send_help():
    print("\n" + "=" * 50)
    print(
        f" CURRENT TARGET : {state['target_guid']} "
        + ("(Global)" if state["target_guid"] == "-1" else "")
    )
    print(
        f" ACTIVE TEMP    : {os.path.basename(state['temp_file']) if state['temp_file'] else 'None'}"
    )

    print("\n INTERNAL COMMANDS:")
    print("  target [guid] - Change who receives your Lua code.")
    print("  target global - Switch back to Global script (-1).")
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
            elif user_input == "push":
                if state["temp_file"] and os.path.exists(state["temp_file"]):
                    with open(state["temp_file"], "r", encoding="utf-8") as f:
                        updated_script = f.read()

                    # Logic: Use self.setLuaScript to update the object
                    # We wrap the file content in a long-string [[ ]] to handle quotes/newlines
                    reload_cmd = (
                        f"local obj = getObjectFromGUID('{state['temp_guid']}') "
                        f"if obj then "
                        f"  obj.setLuaScript([[{updated_script}]]) "
                        f"  obj.reload() "
                        f"else "
                        f"  print('Push failed: Object {state['temp_guid']} no longer exists') "
                        f"end"
                    )

                    # We send this to Global (-1) to ensure the target object can be found and reloaded
                    send_command(reload_cmd, target_override="-1")

                    print(f"Pushed updates to {state['temp_guid']}.")
                else:
                    print("No temp file found. Pull a script from TTS first.")

            elif parts[0] == "target":
                state["target_guid"] = (
                    "-1" if len(parts) < 2 or parts[1] == "global" else parts[1]
                )
                print(f"Target: {state['target_guid']}")

            # --- Send to TTS ---
            else:
                send_command(user_input)

    except KeyboardInterrupt:
        sys.exit(0)
