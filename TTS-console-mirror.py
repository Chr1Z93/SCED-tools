import socket
import json
import threading

# Configuration
HOST = "127.0.0.1"
TTS_LISTEN_PORT = 39999  # Port where TTS listens for commands
MY_LISTEN_PORT = 39998  # Port where TTS sends console logs


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
    """Sends Lua code to TTS to be executed."""
    payload = {"messageID": 3, "guid": "-1", "script": script_code}  # Global
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps(payload).encode("utf-8"))
    except ConnectionRefusedError:
        print("\r[!] Could not connect to TTS. Is the game running?")


if __name__ == "__main__":
    # Start the listener in the background
    threading.Thread(target=listener, daemon=True).start()

    print("--- TTS Interactive Console ---")
    print("Type Lua code and press Enter to execute (Global).")
    print("Example: print('Hello from Python!') or broadcastMsg('Alert')")
    print("-" * 30)

    try:
        while True:
            cmd = input("> ")
            if cmd.strip():
                send_command(cmd)
    except KeyboardInterrupt:
        print("\nExiting...")
