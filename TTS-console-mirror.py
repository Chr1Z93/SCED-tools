import socket
import json
import threading
import sys

# Configuration
HOST = "127.0.0.1"
TTS_LISTEN_PORT = 39999
MY_LISTEN_PORT = 39998

# Simple object to hold our state so the sender can see it
state = {"target_guid": "-1"}


def listener():
    """Background thread to catch and print TTS console messages."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, MY_LISTEN_PORT))
        s.listen()
        while True:
            conn, _ = s.accept()
            with conn:
                data = conn.recv(8192)
                if data:
                    try:
                        msg = json.loads(data.decode("utf-8"))
                        if msg.get("messageID") == 2:
                            print(f"\r[TTS]: {msg.get('message')}\n> ", end="")
                        elif msg.get("messageID") == 3:
                            print(f"\r[ERR]: {msg.get('error')}\n> ", end="")
                    except:
                        pass


def send_command(script_code):
    """Sends Lua code to the currently targeted GUID."""
    payload = {"messageID": 3, "guid": state["target_guid"], "script": script_code}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps(payload).encode("utf-8"))
    except ConnectionRefusedError:
        print(f"\r[!] Connection failed. Is TTS running?\n> ", end="")


def end_session():
    print("\nExiting...")
    sys.exit(0)


if __name__ == "__main__":
    # Start the listener in the background
    threading.Thread(target=listener, daemon=True).start()

    print("--- TTS Interactive Console ---")
    print(f"Default Target: {state['target_guid']} (Global)")
    print("Commands: 'target [guid]', 'target global', 'exit', 'help'")
    print("-" * 30)

    try:
        while True:
            user_input = input("> ").strip()
            if not user_input:
                continue

            parts = user_input.lower().split()

            # --- Internal Commands ---
            if user_input == "exit":
                end_session()

            elif user_input == "help":
                print("\nInternal Commands:")
                print("  target [guid] : Set target object (e.g., 'target abc123')")
                print("  target global : Set target back to Global (-1)")
                print("  exit          : Close script")
                print("\nCurrent Target:", state["target_guid"])

            elif parts[0] == "target":
                if len(parts) > 1:
                    new_guid = "-1" if parts[1] == "global" else parts[1]
                    state["target_guid"] = new_guid
                    print(f"Target switched to: {state['target_guid']}")
                else:
                    print(f"Current target: {state['target_guid']}")

            # --- Send to TTS ---
            else:
                send_command(user_input)

    except KeyboardInterrupt:
        end_session()
