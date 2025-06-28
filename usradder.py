from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
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

init()

# Configuration
ACCOUNT_SWITCH_THRESHOLD = 20
MAX_FLOOD_ERRORS = 5
MAX_SUCCESSFUL_ADDS = 60
CRITICAL_WAIT_TIME = 3600
MIN_DELAY = 10
MAX_DELAY = 30

# Couleurs
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
    print(f'{info}{g} Multi-Account Group Adder V4.0 {rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx {rs}')
    print(f'{info}{cy} Features: Strict Account Rotation | Military Flood Protection{rs}\n')

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
        
    def add_account(self, phone, api_id, api_hash):
        self.accounts.append({
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash,
            'client': None,
            'is_premium': False,
            'active': True,
            'added_count': 0
        })
    
    def get_current_account(self):
        return self.accounts[self.current_index] if self.accounts else None
    
    def rotate_account(self, force=False):
        if len(self.accounts) <= 1 and not force:
            return False
        
        original_index = self.current_index
        next_index = (original_index + 1) % len(self.accounts)
        
        while next_index != original_index:
            if self.accounts[next_index]['active']:
                self.current_index = next_index
                self.action_count = 0
                self.flood_errors = 0
                print(f'\n{info}{cy} ACCOUNT ROTATION: Switched to {self.get_current_account()["phone"]}{rs}')
                return True
            next_index = (next_index + 1) % len(self.accounts)
        
        return False
    
    def handle_flood_error(self, error_msg):
        wait_time = 0
        if match := re.search(r'A wait of (\d+) seconds', str(error_msg)):
            wait_time = int(match.group(1))
        
        if wait_time > CRITICAL_WAIT_TIME:
            print(f'\n{error}{r} CRITICAL FLOOD: Immediate rotation required{rs}')
            self.accounts[self.current_index]['active'] = False
            return self.rotate_account(force=True)
        
        self.flood_errors += 1
        
        if self.flood_errors >= MAX_FLOOD_ERRORS:
            print(f'\n{error}{r} FLOOD LIMIT REACHED: Rotating immediately{rs}')
            return self.rotate_account()
        
        return False

# Initialisation
account_manager = AccountManager()

if len(sys.argv) < 8:
    print(f'{error} Usage: python usradder.py api_id1 api_hash1 phone1 api_id2 api_hash2 phone2 csv_file group_link')
    sys.exit(1)

# Extraction des paramètres
accounts_data = sys.argv[1:-2]
input_file, group_link = sys.argv[-2], sys.argv[-1]

# Ajout des comptes
for i in range(0, len(accounts_data), 3):
    try:
        api_id, api_hash, phone = accounts_data[i], accounts_data[i+1], accounts_data[i+2]
        account_manager.add_account(phone, int(api_id), api_hash)
    except IndexError:
        print(f'{error} Invalid account parameters format')
        sys.exit(1)

def setup_client(account):
    try:
        client = TelegramClient(f'sessions/{account["phone"]}', account['api_id'], account['api_hash'])
        client.connect()
        
        if not client.is_user_authorized():
            client.send_code_request(account['phone'])
            code = input(f'{info} Enter code for {account["phone"]}: ')
            client.sign_in(account['phone'], code)
        
        # Vérification du compte premium
        account_ttl = client(GetAccountTTLRequest())
        account['is_premium'] = account_ttl.days > 7 if hasattr(account_ttl, 'days') else False
        account['client'] = client
        return True
    except Exception as e:
        print(f'{error} Account setup failed: {str(e)}')
        account['active'] = False
        return False

if not setup_client(account_manager.get_current_account()):
    print(f'{error} Critical: Account initialization failed!')
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

try:
    client = account_manager.get_current_account()['client']
    target_group = client.get_entity(group_link)
    group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    print(f'{info}{g} Target: {target_group.title} | Members: {len(client.get_participants(target_group))}{rs}')
except Exception as e:
    print(f'{error} Group error: {str(e)}')
    sys.exit(1)

# Main loop
start_time = datetime.now()
stats = {'success': 0, 'skip': 0, 'fail': 0, 'invalid': 0}

for index, user in enumerate(users, 1):
    current_account = account_manager.get_current_account()
    
    if not current_account or not current_account['active']:
        print(f'{error} NO ACTIVE ACCOUNTS REMAINING!')
        break
    
    if account_manager.successful_adds >= MAX_SUCCESSFUL_ADDS:
        print(f'\n{info}{cy} ACCOUNT LIMIT REACHED: {MAX_SUCCESSFUL_ADDS} successful adds{rs}')
        if not account_manager.rotate_account():
            break
        continue
    
    if account_manager.action_count >= ACCOUNT_SWITCH_THRESHOLD:
        print(f'\n{info}{cy} MANDATORY ROTATION AFTER {ACCOUNT_SWITCH_THRESHOLD} ACTIONS{rs}')
        if not account_manager.rotate_account():
            print(f'{error} CONTINUING WITH SINGLE ACCOUNT')
    
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
        
        delay_factor = 0.8 if current_account['is_premium'] else 1.2
        delay = random.randint(MIN_DELAY, MAX_DELAY) * delay_factor
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
        if account_manager.handle_flood_error(str(e)):
            continue
        countdown_timer(300)
        
    except UserPrivacyRestrictedError:
        print(f'{error} Privacy restriction for {user["username"]}')
        stats['fail'] += 1
        
    except Exception as e:
        print(f'{error} Failed to add {user["username"]}: {str(e)}')
        stats['fail'] += 1

# Rapport final
duration = datetime.now() - start_time
print(f'\n{info}{g} {"="*60}{rs}')
print(f'{info}{g} OPERATION SUMMARY:{rs}')
print(f'{info}{g} {"-"*60}{rs}')
print(f'{attempt}{g} Successes: {stats["success"]} ({stats["success"]/index:.1%}){rs}')
print(f'{sleep}{cy} Skipped: {stats["skip"]} (existing){rs}')
print(f'{sleep}{ye} Invalid: {stats["invalid"]} (bad usernames){rs}')
print(f'{error}{r} Failures: {stats["fail"]}{rs}')
print(f'{info}{g} Processed: {index}/{len(users)}{rs}')
print(f'{info}{g} Duration: {duration}{rs}')
print(f'{info}{g} Accounts used: {len([acc for acc in account_manager.accounts if acc["active"] and acc["added_count"] > 0])}/{len(account_manager.accounts)}{rs}')
print(f'{info}{g} {"="*60}{rs}')

# Nettoyage
for acc in account_manager.accounts:
    if acc.get('client'):
        acc['client'].disconnect()
