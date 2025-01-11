import websocket
import json
import time
import random
import threading

def load_tokens(file_path):
    with open(file_path, 'r') as file:
        tokens = [line.strip() for line in file]
    return tokens

activities = [
    {"name": "Minecraft", "type": 0},
    {"name": "League of Legends", "type": 0},
    {"name": "Roblox", "type": 0},
    {"name": "Spotify", "type": 2},
    {"name": "Twitch", "type": 0},
    {"name": "YouTube", "type": 0},
    {"name": "Visual Studio Code", "type": 0},
    {"name": "Netflix", "type": 0},
    {"name": "Valorant", "type": 0},
    {"name": "Fortnite", "type": 0},
    {"name": "GTA V", "type": 0}
]

custom_status = "Working on something cool!"  # muss noch gefixt werden weil es nicht geht kp warum token ist nur online ohne irgendein status :3

statuses = ["online", "idle", "dnd"]

def send_status(ws, token):
    """
    Sends a status update to the Discord WebSocket.

    Args:
        ws (websocket.WebSocket): WebSocket connection.
        token (str): Discord account token.
    """
    if random.random() < 0.3:
        activity = {"name": custom_status, "type": 4}
    else:
        activity = random.choice(activities)
    status = random.choice(statuses)
    payload = {
        "op": 3,
        "d": {
            "since": None,
            "activities": [activity],
            "status": status,
            "afk": False
        }
    }
    ws.send(json.dumps(payload))
    print(f"\n┌────────────────────────────")
    print(f"│ Token: {token[:6]}... | Status: {status.capitalize()}")
    print(f"│ Activity: {activity['name']}")
    print(f"└────────────────────────────")

def manage_token(token):
    """
    Establish and manage a WebSocket connection for a given token.

    Args:
        token (str): Discord account token.
    """
    ws_url = "wss://gateway.discord.gg/?v=9&encoding=json"
    ws = websocket.WebSocket()
    ws.connect(ws_url)

    heartbeat_interval = 41

    identify_payload = {
        "op": 2,
        "d": {
            "token": token,
            "properties": {
                "$os": "linux",
                "$browser": "my_library",
                "$device": "my_library"
            },
            "presence": {
                "status": "online",
                "afk": False,
                "activities": []
            }
        }
    }

    ws.send(json.dumps(identify_payload))
    print(f"\n┌────────────────────────────")
    print(f"│ Token: {token[:6]}... | Connected")
    print(f"└────────────────────────────")

    try:
        while True:
            send_status(ws, token)
            time.sleep(heartbeat_interval)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ws.close()

if __name__ == "__main__":
    tokens = load_tokens("tokens.txt")
    threads = []

    for token in tokens:
        thread = threading.Thread(target=manage_token, args=(token,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()