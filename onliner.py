import websocket
import json
import time
import threading
import requests
from colorama import Fore, Style

def load_tokens(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def check_token(token):
    headers = {'Authorization': token}
    try:
        response = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
        return response.status_code == 200
    except:
        return False

def force_online(token):
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    payload = {
        "status": "online",
        "since": 0,
        "activities": [],
        "afk": False
    }
    try:
        requests.patch('https://discord.com/api/v9/users/@me/settings', headers=headers, json=payload)
    except:
        pass

def send_heartbeat(ws):
    heartbeat_payload = {"op": 1, "d": None}
    ws.send(json.dumps(heartbeat_payload))

def manage_token(token, status_index, activity_index, config):
    if not check_token(token):
        print(f"{Fore.RED}[-]{Style.RESET_ALL} Token Invalid: {token[:6]}...")
        return

    force_online(token)
    time.sleep(1)

    ws_url = "wss://gateway.discord.gg/?v=9&encoding=json"
    ws = websocket.WebSocket()
    try:
        ws.connect(ws_url)
        event = json.loads(ws.recv())
        heartbeat_interval = event['d']['heartbeat_interval'] / 1000

        status = config['statuses'][status_index % len(config['statuses'])]
        
        if activity_index % 4 == 3:
            activity = {
                "type": 4,
                "state": config['custom_status'],
                "name": "Custom Status"
            }
        elif activity_index % 4 == 0:
            activity = config['spotify'].copy()
            activity["timestamps"] = {
                "start": int(time.time() * 1000),
                "end": int(time.time() * 1000) + config['spotify']['duration_ms']
            }
        else:
            activity = config['activities'][activity_index % len(config['activities'])]

        identify_payload = {
            "op": 2,
            "d": {
                "token": token,
                "capabilities": 16381,
                "properties": {
                    "os": "Windows",
                    "browser": "Chrome",
                    "device": "",
                    "system_locale": "en-US",
                    "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "browser_version": "120.0.0.0",
                    "os_version": "10",
                    "referrer": "",
                    "referring_domain": "",
                    "referrer_current": "",
                    "referring_domain_current": "",
                    "release_channel": "stable",
                    "client_build_number": 245535,
                    "client_event_source": None
                },
                "presence": {
                    "status": status,
                    "since": 0,
                    "activities": [activity],
                    "afk": False
                },
                "compress": False,
                "client_state": {
                    "guild_versions": {},
                    "highest_last_message_id": "0",
                    "read_state_version": 0,
                    "user_guild_settings_version": -1,
                    "user_settings_version": -1,
                    "private_channels_version": "0",
                    "api_code_version": 0
                }
            }
        }
        ws.send(json.dumps(identify_payload))

        display_name = activity.get("details", activity.get("name", "Unknown"))
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {token[:6]}... | Onlined | {status} | {display_name}")
        
        retries = 0
        max_retries = 3
        
        while True:
            try:
                time.sleep(heartbeat_interval)
                send_heartbeat(ws)
                
                if "timestamps" in activity:
                    activity["timestamps"]["start"] = int(time.time() * 1000)
                    activity["timestamps"]["end"] = activity["timestamps"]["start"] + config['spotify']['duration_ms']
                
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
                retries = 0
                
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    raise e
                time.sleep(5)
                continue
            
    except websocket.WebSocketException:
        print(f"{Fore.RED}[-]{Style.RESET_ALL} Connection Lost: {token[:6]}...")
        time.sleep(5)
        manage_token(token, status_index, activity_index, config)
    except Exception as e:
        print(f"{Fore.YELLOW}[-]{Style.RESET_ALL} Error: {str(e)}")
        time.sleep(5)
        manage_token(token, status_index, activity_index, config)
    finally:
        try:
            ws.close()
        except:
            pass

if __name__ == "__main__":
    config = load_config("config.json")
    tokens = load_tokens("tokens.txt")
    threads = []
    for i, token in enumerate(tokens):
        thread = threading.Thread(target=manage_token, args=(token, i, i, config))
        threads.append(thread)
        thread.start()
        time.sleep(0.5)
    for thread in threads:
        thread.join()