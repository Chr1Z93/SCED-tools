import socket
import json

# Configuration
HOST = "127.0.0.1"
TTS_LISTEN_PORT = 39999  # Where we send commands TO
MY_LISTEN_PORT = 39998  # Where TTS sends data TO us


def listen_for_tts_response():
    """Starts a temporary server to catch the data TTS sends back."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, MY_LISTEN_PORT))
        s.listen(1)
        print(f"Listening for TTS data on {MY_LISTEN_PORT}...")

        conn, addr = s.accept()
        with conn:
            data = b""
            while True:
                part = conn.recv(4096)
                if not part:
                    break
                data += part

            return json.loads(data.decode("utf-8"))


def send_to_tts(message_dict):
    """Sends a JSON command to Tabletop Simulator."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, TTS_LISTEN_PORT))
            s.sendall(json.dumps(message_dict).encode("utf-8"))
            print("Request sent to TTS.")
    except ConnectionRefusedError:
        print("Error: Could not connect to TTS. Is the game running?")
        return False
    return True


def get_all_scripts():
    """Main flow to trigger a refresh and capture the data."""
    print("Requesting script states...")

    # Send the request, then immediately start listening
    if send_to_tts({"messageID": 0}):
        scripts_data = listen_for_tts_response()
        return scripts_data
    return None


# --- Execution ---
if __name__ == "__main__":
    all_data = get_all_scripts()

    if all_data and "scriptStates" in all_data:
        print(f"\nSuccessfully retrieved {len(all_data['scriptStates'])} objects.")
        for obj in all_data["scriptStates"]:
            print(f"- {obj['name']} (GUID: {obj['guid']})")
            # Here is where we will eventually inject your specific logic
    else:
        print("Failed to retrieve data.")
