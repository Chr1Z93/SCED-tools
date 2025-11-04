import socket
import json

# Define the data you want to send
data_to_send = {"messageID": 1, "scriptStates": []}

# The Tabletop Simulator External Editor API listens on port 39999
HOST = "127.0.0.1"  # localhost
PORT = 39999

# Convert the Python dictionary to a JSON string and then encode it to bytes
json_string = json.dumps(data_to_send)
message = json_string.encode("utf-8")

try:
    # Create a socket object using IPv4 and TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Connect to the TTS listener
        s.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}")

        # Send the JSON message
        s.sendall(message)
        print("Data sent successfully.")

except ConnectionRefusedError:
    print(f"Connection refused. Ensure TTS is running and a game is loaded.")
except Exception as e:
    print(f"An error occurred: {e}")
