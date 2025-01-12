import websocket
import json
import time
import threading
import requests
from colorama import Fore, Style

def load_tokens(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

def check_token(token):
    headers = {'Authorization': token}
    response = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
    return response.status_code == 200

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

custom_status = "Working on something cool!"
statuses = ["online", "idle", "dnd"]

def send_heartbeat(ws):
    heartbeat_payload = {"op": 1, "d": None}
    ws.send(json.dumps(heartbeat_payload))

def manage_token(token, status_index, activity_index):
    if not check_token(token):
        print(f"{Fore.RED}[-]{Style.RESET_ALL} Token Invalid: {token[:6]}...")
        return
        
    ws_url = "wss://gateway.discord.gg/?v=9&encoding=json"
    ws = websocket.WebSocket()
    try:
        ws.connect(ws_url)
        event = json.loads(ws.recv())
        heartbeat_interval = event['d']['heartbeat_interval'] / 1000

        status = statuses[status_index % len(statuses)]
        
        if activity_index % 4 == 3:
            activity = {
                "type": 4,
                "state": custom_status,
                "name": "Custom Status"
            }
        else:
            activity = activities[activity_index % len(activities)]

        identify_payload = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "windows",
                    "$browser": "Discord",
                    "$device": "desktop"
                },
                "presence": {
                    "status": status,
                    "since": 0,
                    "activities": [activity],
                    "afk": False
                }
            }
        }
        ws.send(json.dumps(identify_payload))

        presence_update = {
            "op": 3,
            "d": {
                "status": status,
                "since": 0,
                "activities": [activity],
                "afk": False
            }
        }
        ws.send(json.dumps(presence_update))

        display_name = activity.get("state", activity["name"])
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {token[:6]}... | Onlined | {status} | {display_name}")
        
        while True:
            time.sleep(heartbeat_interval)
            send_heartbeat(ws)
            ws.send(json.dumps(presence_update))
            
    except websocket.WebSocketException:
        print(f"{Fore.RED}[-]{Style.RESET_ALL} Token Invalid: {token[:6]}...")
    except Exception as e:
        print(f"{Fore.YELLOW}[-]{Style.RESET_ALL} Error: {str(e)}")
    finally:
        ws.close()

if __name__ == "__main__":
    tokens = load_tokens("tokens.txt")
    threads = []
    for i, token in enumerate(tokens):
        thread = threading.Thread(target=manage_token, args=(token, i, i))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()