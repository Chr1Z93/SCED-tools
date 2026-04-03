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
                        m_id = msg.get("messageID")

                        # Debugging
                        # print(f"messageID: {m_id}")

                        # Print/Debug (ID 2)
                        if m_id == 2:
                            print(f"\r[TTS]: {msg.get('message')}\n> ", end="")

                        # Errors (ID 3)
                        elif m_id == 3:
                            print(f"\r[ERR]: {msg.get('error')}\n> ", end="")

                        # Custom Messages (ID 4)
                        elif m_id == 4:
                            custom = msg.get("customMessage")
                            print(f"\r[CUSTOM]: {custom}\n> ", end="")

                        # Return Values (ID 5)
                        elif m_id == 5:
                            print(f"\r[RETURN]: {msg.get('returnValue')}\n> ", end="")

                        # Game Saved (ID 6)
                        elif m_id == 6:
                            print(f"\r[EVENT]: Game Saved\n> ", end="")

                        # Object Created (ID 7)
                        elif m_id == 7:
                            print(
                                f"\r[NEW]: Object Created (GUID: {msg.get('guid')})\n> ",
                                end="",
                            )

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
                sys.exit(0)

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
        sys.exit(0)
