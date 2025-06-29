import json
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.account import GetAccountTTLRequest
import sys
import csv
import time
import random
import pyfiglet
from colorama import init, Fore
import os
import re
from datetime import datetime
import socket

init()

# Configuration
ACCOUNT_SWITCH_THRESHOLD = 15
MAX_FLOOD_ERRORS = 2
MAX_SUCCESSFUL_ADDS = 50
CRITICAL_WAIT_TIME = 1800
MIN_DELAY = 8
MAX_DELAY = 25
PROXY_TEST_TIMEOUT = 5

# Color setup
r, g, rs, w, cy, ye = Fore.RED, Fore.GREEN, Fore.RESET, Fore.WHITE, Fore.CYAN, Fore.YELLOW
colors = [r, g, w, ye, cy]
info = g + '[' + w + 'i' + g + ']' + rs
attempt = g + '[' + w + '+' + g + ']' + rs
sleep = g + '[' + w + '*' + g + ']' + rs
error = g + '[' + r + '!' + g + ']' + rs
premium = g + '[' + ye + 'P' + g + ']' + rs

def show_banner():
    f = pyfiglet.Figlet(font='slant')
    logo = random.choice(colors) + f.renderText('Telegram') + rs
    print(logo)
    print(f'{info}{g} Multi-Account Group Adder V1.1 {rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx {rs}')
    print(f'{info}{cy} Features: Smart Rotation | Proxy Support | Anti-Flood{rs}\n')

clear_screen = lambda: os.system('cls' if os.name == 'nt' else 'clear')

def countdown_timer(seconds):
    while seconds:
        mins, secs = divmod(seconds, 60)
        print(f'{sleep} Waiting: {mins:02d}:{secs:02d}', end='\r')
        time.sleep(1)
        seconds -= 1
    print(' ' * 30, end='\r')

clear_screen()
show_banner()

class AccountManager:
    def __init__(self):
        self.accounts = []
        self.current_index = 0
        self.action_count = 0
        self.flood_errors = 0
        self.successful_adds = 0
        self.proxies = self.load_proxies()
        self.current_proxy = None
    
    def load_proxies(self):
        try:
            with open('proxy_list.json') as f:
                proxies = json.load(f)
                return [p for p in proxies if all(k in p for k in ['server', 'port'])]
        except Exception:
            return []
    
    def get_next_proxy(self):
        if not self.proxies:
            return None
        
        for proxy in random.sample(self.proxies, len(self.proxies)):
            try:
                sock = socket.create_connection(
                    (proxy['server'], proxy['port']), 
                    timeout=PROXY_TEST_TIMEOUT
                )
                sock.close()
                self.current_proxy = proxy
                return proxy
            except Exception:
                continue
        return None
    
    def add_account(self, phone, api_id, api_hash):
        self.accounts.append({
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash,
            'client': None,
            'is_premium': False,
            'active': True,
            'added_count': 0,
            'last_active': None,
            'errors': 0
        })
    
    def get_current_account(self):
        return self.accounts[self.current_index] if self.accounts else None
    
    def rotate_account(self, reason=""):
        """Rotate to next available account with simple round-robin"""
        if len(self.accounts) <= 1:
            return False
        
        print(f'\n{info}{cy} ACCOUNT ROTATION: {reason}{rs}')
        
        original_index = self.current_index
        for i in range(1, len(self.accounts)):
            next_index = (original_index + i) % len(self.accounts)
            if self.accounts[next_index]['active']:
                self.current_index = next_index
                self.action_count = 0
                self.flood_errors = 0
                time.sleep(random.uniform(1, 3))
                
                proxy = self.get_next_proxy()
                if self.setup_client(self.get_current_account(), proxy):
                    print(f'{info}{cy} Switched to {self.get_current_account()["phone"]}{rs}')
                    return True
        
        print(f'{error} All accounts exhausted or inactive{rs}')
        return False
    
    def setup_client(self, account, proxy=None):
        try:
            proxy_config = None
            if proxy:
                proxy_config = (proxy['server'], proxy['port'])
            
            client = TelegramClient(
                f'sessions/{account["phone"]}',
                account['api_id'],
                account['api_hash'],
                proxy=proxy_config
            )
            client.connect()
            
            if not client.is_user_authorized():
                client.send_code_request(account['phone'])
                code = input(f'{info} Enter code for {account["phone"]}: ')
                client.sign_in(account['phone'], code)
            
            # Premium check with fallback
            try:
                account_ttl = client(GetAccountTTLRequest())
                account['is_premium'] = account_ttl.days > 7 if hasattr(account_ttl, 'days') else False
            except Exception:
                account['is_premium'] = False
            
            account['client'] = client
            account['last_active'] = datetime.now()
            return True
            
        except Exception as e:
            print(f'{error} Account setup failed: {str(e)}')
            account['active'] = False
            return False
    
    def handle_flood_error(self, error_msg):
        wait_time = 0
        if isinstance(error_msg, FloodWaitError):
            wait_time = error_msg.seconds
        elif isinstance(error_msg, str):
            match = re.search(r'A wait of (\d+) seconds', error_msg)
            if match:
                wait_time = int(match.group(1))
        
        self.flood_errors += 1
        
        if wait_time > CRITICAL_WAIT_TIME:
            print(f'\n{error}{r} CRITICAL FLOOD: {wait_time}s wait - Immediate rotation{rs}')
            return self.rotate_account("Critical flood")
        
        if self.flood_errors >= MAX_FLOOD_ERRORS:
            print(f'\n{error}{r} FLOOD LIMIT REACHED: Rotating immediately{rs}')
            return self.rotate_account("Flood limit")
        
        adjusted_wait = wait_time * random.uniform(0.8, 1.2)
        countdown_timer(int(adjusted_wait))
        return False

# Initialize account manager
account_manager = AccountManager()

if len(sys.argv) < 8:
    print(f'{error} Usage: python usradder.py api_id1 api_hash1 phone1 api_id2 api_hash2 phone2 csv_file group_link')
    sys.exit(1)

# Process account arguments
accounts_data = sys.argv[1:-2]
input_file, group_link = sys.argv[-2], sys.argv[-1]

for i in range(0, len(accounts_data), 3):
    try:
        api_id, api_hash, phone = accounts_data[i], accounts_data[i+1], accounts_data[i+2]
        account_manager.add_account(phone, int(api_id), api_hash)
    except (IndexError, ValueError) as e:
        print(f'{error} Invalid account parameters: {str(e)}')
        sys.exit(1)

# Initialize first account
if not account_manager.setup_client(account_manager.get_current_account(), account_manager.get_next_proxy()):
    print(f'{error} First account initialization failed!')
    sys.exit(1)

def load_users(filename):
    try:
        with open(filename, encoding='UTF-8') as f:
            return [{
                'username': row[0].strip(),
                'user_id': row[1],
                'access_hash': row[2],
                'group': row[3],
                'group_id': row[4]
            } for row in csv.reader(f) if len(row) >= 5 and row[0].strip()]
    except Exception as e:
        print(f'{error} File error: {str(e)}')
        return []

users = load_users(input_file)
if not users:
    print(f'{error} No valid users found in {input_file}')
    sys.exit(1)

# Group setup
try:
    client = account_manager.get_current_account()['client']
    target_group = client.get_entity(group_link)
    group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    print(f'{info}{g} Target: {target_group.title} | Members: {len(client.get_participants(target_group))}{rs}')
except Exception as e:
    print(f'{error} Group error: {str(e)}')
    sys.exit(1)

# Main processing loop
start_time = datetime.now()
stats = {'success': 0, 'skip': 0, 'fail': 0, 'invalid': 0}

for index, user in enumerate(users, 1):
    current_account = account_manager.get_current_account()
    
    if not current_account or not current_account['active']:
        print(f'{error} NO ACTIVE ACCOUNTS REMAINING!')
        break
    
    # Check all rotation triggers if multiple accounts available
    if len(account_manager.accounts) > 1:
        rotation_triggers = [
            (account_manager.flood_errors >= MAX_FLOOD_ERRORS, f"{MAX_FLOOD_ERRORS}+ flood errors"),
            (account_manager.action_count >= ACCOUNT_SWITCH_THRESHOLD, f"{ACCOUNT_SWITCH_THRESHOLD} action threshold"),
            (current_account['errors'] >= 3, "3+ account errors"),
            (account_manager.successful_adds >= MAX_SUCCESSFUL_ADDS, f"{MAX_SUCCESSFUL_ADDS} quota reached"),
            ((datetime.now() - current_account['last_active']).total_seconds() > 1800, "30m inactivity"),
            (not current_account['is_premium'] and random.random() < 0.1, "Random non-premium rotation")
        ]

        for condition, reason in rotation_triggers:
            if condition:
                if account_manager.rotate_account(reason):
                    current_account = account_manager.get_current_account()
                    client = current_account['client']
                break
    
    try:
        if not user['username']:
            print(f'{sleep}{ye} Skipping empty username{rs}')
            stats['invalid'] += 1
            continue
            
        client = current_account['client']
        
        participants = [p.username for p in client.get_participants(target_group) if p.username]
        if user['username'] in participants:
            print(f'{sleep}{cy} Skip: {user["username"]} exists{rs}')
            stats['skip'] += 1
            continue
        
        # Random delay with premium adjustment
        delay = random.randint(MIN_DELAY, MAX_DELAY) * (0.7 if current_account['is_premium'] else 1.0)
        print(f'\n{sleep} Delay: {delay:.1f}s | Acc: {current_account["phone"]}')
        countdown_timer(int(delay))
        
        print(f'\n{attempt} Adding {user["username"]} ({index}/{len(users)})')
        client(InviteToChannelRequest(group_entity, [client.get_input_entity(user['username'])]))
        
        stats['success'] += 1
        account_manager.action_count += 1
        account_manager.successful_adds += 1
        current_account['added_count'] += 1
        print(f'{attempt}{g} Success! (Total: {account_manager.successful_adds}/{MAX_SUCCESSFUL_ADDS}){rs}')
        
    except PeerFloodError as e:
        stats['fail'] += 1
        current_account['errors'] += 1
        if account_manager.handle_flood_error(str(e)):
            continue
        countdown_timer(300)
        
    except UserPrivacyRestrictedError:
        print(f'{error} Privacy restriction for {user["username"]}')
        stats['fail'] += 1
        current_account['errors'] += 1
        
    except Exception as e:
        print(f'{error} Failed to add {user["username"]}: {str(e)}')
        stats['fail'] += 1
        current_account['errors'] += 1
        
        if "auth" in str(e).lower() or "session" in str(e).lower():
            print(f'{error} CRITICAL ERROR: Rotating account')
            account_manager.rotate_account("Authentication error")

# Final report
duration = datetime.now() - start_time
print(f'\n{info}{g} {"="*60}{rs}')
print(f'{info}{g} OPERATION COMPLETE:{rs}')
print(f'{info}{g} {"-"*60}{rs}')
print(f'{attempt}{g} Successes: {stats["success"]} ({stats["success"]/len(users):.1%}){rs}')
print(f'{sleep}{cy} Skipped: {stats["skip"]} (existing){rs}')
print(f'{sleep}{ye} Invalid: {stats["invalid"]} (bad usernames){rs}')
print(f'{error}{r} Failures: {stats["fail"]}{rs}')
print(f'{info}{g} Processed: {len(users)}{rs}')
print(f'{info}{g} Duration: {duration}{rs}')
print(f'{info}{g} Accounts used: {len([acc for acc in account_manager.accounts if acc["added_count"] > 0])}/{len(account_manager.accounts)}{rs}')
print(f'{info}{g} Proxy usage: {account_manager.current_proxy["server"] if account_manager.current_proxy else "None"}{rs}')
print(f'{info}{g} {"="*60}{rs}')

# Cleanup
for acc in account_manager.accounts:
    if acc.get('client'):
        acc['client'].disconnect()
    
