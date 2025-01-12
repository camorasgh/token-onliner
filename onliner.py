import websocket
import json
import time
import threading
import requests
from colorama import Fore, Style
import random

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

def get_random_timestamp():
    current_time = int(time.time() * 1000)
    random_past = random.randint(300000, 7200000)
    return {"start": current_time - random_past}

def get_display_name(activity):
    if activity["type"] == 2:
        return f"{activity['details']} - {activity['state']}"
    elif activity["type"] == 4:
        emoji = activity.get("emoji", "")
        return f"{emoji} {activity['state']}"
    elif "details" in activity:
        return activity["details"]
    elif "name" in activity:
        return activity["name"]
    return "Unknown"

def get_random_activity(config):
    activity_type = random.choices(
        ["game", "spotify", "custom"],
        weights=[0.7, 0.2, 0.1]
    )[0]

    if activity_type == "spotify":
        activity = config['spotify'].copy()
        current_time = int(time.time() * 1000)
        activity["timestamps"] = {
            "start": current_time,
            "end": current_time + activity["duration_ms"]
        }
        activity["party"] = {
            "id": f"spotify:{random.randint(100000000, 999999999)}"
        }
        activity["sync_id"] = "".join(random.choices("0123456789abcdef", k=32))
        activity["flags"] = 48
        activity["session_id"] = "".join(random.choices("0123456789abcdef", k=32))
    elif activity_type == "custom":
        activity = config['custom_status'].copy()
    else:
        activity = random.choice(config['activities']).copy()
        activity["timestamps"] = get_random_timestamp()
        activity["created_at"] = int(time.time() * 1000)
        if activity.get("application_id"):
            activity["flags"] = 0
            activity["id"] = str(random.randint(100000000000000000, 999999999999999999))
    
    return activity

def manage_token(token, config):
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

        status = random.choice(config['statuses'])
        activity = get_random_activity(config)

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

        display_name = get_display_name(activity)
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {token[:6]}... | Onlined | {status} | {display_name}")
        
        retries = 0
        max_retries = 3
        
        while True:
            try:
                time.sleep(heartbeat_interval)
                send_heartbeat(ws)
                
                if activity["type"] == 2:
                    activity["timestamps"]["start"] = int(time.time() * 1000)
                    activity["timestamps"]["end"] = activity["timestamps"]["start"] + config['spotify']['duration_ms']
                    activity["sync_id"] = "".join(random.choices("0123456789abcdef", k=32))
                elif activity["type"] == 0 and random.random() < 0.1:
                    activity["timestamps"] = get_random_timestamp()
                    status = random.choice(config['statuses'])
                
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
        manage_token(token, config)
    except Exception as e:
        print(f"{Fore.YELLOW}[-]{Style.RESET_ALL} Error: {str(e)}")
        time.sleep(5)
        manage_token(token, config)
    finally:
        try:
            ws.close()
        except:
            pass

if __name__ == "__main__":
    config = load_config("config.json")
    tokens = load_tokens("tokens.txt")
    threads = []
    for token in tokens:
        thread = threading.Thread(target=manage_token, args=(token, config))
        threads.append(thread)
        thread.start()
        time.sleep(0.5)
    for thread in threads:
        thread.join()
