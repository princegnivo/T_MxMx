from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, AuthKeyUnregisteredError
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

# ====================
# CONFIGURATION
# ====================
ACCOUNT_SWITCH_THRESHOLD = 20  # Regular account rotation interval
MAX_FLOOD_ERRORS = 5           # Flood errors before switch
CRITICAL_WAIT_TIME = 3600      # 1 hour (switch immediately if wait > this)

# ====================
# COLOR CONFIGURATION (Original Style)
# ====================
r = Fore.RED
g = Fore.GREEN
rs = Fore.RESET
w = Fore.WHITE
cy = Fore.CYAN
ye = Fore.YELLOW
colors = [r, g, w, ye, cy]
info = g + '[' + w + 'i' + g + ']' + rs
attempt = g + '[' + w + '+' + g + ']' + rs
sleep = g + '[' + w + '*' + g + ']' + rs
error = g + '[' + r + '!' + g + ']' + rs
premium = g + '[' + ye + 'P' + g + ']' + rs
countdown = g + '[' + w + '>' + g + ']' + rs

# =================
# CORE FUNCTIONS (Original)
# =================
def show_banner():
    f = pyfiglet.Figlet(font='slant')
    logo = f.renderText('Telegram')
    print(random.choice(colors) + logo + rs)
    print(f'{info}{g} Telegram Group Adder V2.5 (Emergency Switch Pro){rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx{rs}')
    print(f'{info}{cy} Features: Instant Account Switching | Full Flood Protection | Premium Detection{rs}\n')

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def countdown_timer(seconds):
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        time_str = f'{mins:02d}:{secs:02d}'
        print(f'{countdown} Waiting: {time_str} remaining', end='\r')
        time.sleep(1)
    print(' ' * 50, end='\r')

clear_screen()
show_banner()

# ====================
# ACCOUNT MANAGER (Enhanced)
# ====================
class AccountManager:
    def __init__(self):
        self.accounts = []
        self.current_index = 0
        self.action_count = 0
        self.flood_errors = 0
        
    def add_account(self, phone, api_id, api_hash):
        self.accounts.append({
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash,
            'client': None,
            'is_premium': False,
            'active': True
        })
    
    def get_current_account(self):
        if not self.accounts:
            return None
        return self.accounts[self.current_index]
    
    def rotate_account(self, force=False):
        """Switch to next active account"""
        if len(self.accounts) <= 1 and not force:
            return False
        
        original_index = self.current_index
        attempts = 0
        
        while attempts < len(self.accounts):
            self.current_index = (self.current_index + 1) % len(self.accounts)
            attempts += 1
            
            if self.accounts[self.current_index]['active']:
                self.action_count = 0
                self.flood_errors = 0
                print(f'{info}{cy} Switched to account: {self.get_current_account()["phone"]}{rs}')
                return True
        
        print(f'{error}{r} No active accounts available!{rs}')
        return False
    
    def handle_flood_error(self, error_msg):
        """Process flood error and return required wait time"""
        wait_time = 0
        match = re.search(r'A wait of (\d+) seconds', str(error_msg))
        if match:
            wait_time = int(match.group(1))
        
        # Immediate switch for critical wait times
        if wait_time > CRITICAL_WAIT_TIME:
            print(f'{error}{r} CRITICAL FLOOD: Required wait {wait_time}s{rs}')
            self.accounts[self.current_index]['active'] = False
            return self.rotate_account(force=True)
        
        # Normal flood error handling
        self.flood_errors += 1
        if self.flood_errors >= MAX_FLOOD_ERRORS:
            return self.rotate_account()
        
        return False
    
    def increment_action(self):
        """Regular account rotation"""
        self.action_count += 1
        if self.action_count >= ACCOUNT_SWITCH_THRESHOLD:
            return self.rotate_account()
        return False

# Initialize account manager
account_manager = AccountManager()

# ====================
# INPUT VALIDATION (Original)
# ====================
if len(sys.argv) < 6:
    print(f'{error} Usage: python usradder.py api_id api_hash phone_number csv_file group_link')
    sys.exit(1)

# Add primary account
api_id, api_hash, phone = int(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3])
input_file, group_link = str(sys.argv[4]), str(sys.argv[5])
account_manager.add_account(phone, api_id, api_hash)

# ====================
# CLIENT INITIALIZATION (Enhanced)
# ====================
def setup_telegram_client(account):
    session_path = f'sessions/{account["phone"]}'
    try:
        client = TelegramClient(session_path, account['api_id'], account['api_hash'])
        client.connect()
        
        if not client.is_user_authorized():
            print(f'{info} Auth required for {account["phone"]}')
            client.send_code_request(account['phone'])
            code = input(f'{attempt} Enter code: ')
            client.sign_in(account['phone'], code)
        
        # Premium detection (Original)
        account['is_premium'] = False
        try:
            account_info = client(GetAccountTTLRequest())
            if hasattr(account_info, 'days') and account_info.days < 30:
                account['is_premium'] = True
                print(f'{premium} Premium account detected!')
        except Exception as e:
            print(f'{error} Account check error: {str(e)}')
        
        account['client'] = client
        return True
    
    except Exception as e:
        print(f'{error} Connection failed: {str(e)}')
        account['active'] = False
        return False

# Initialize all accounts
if not setup_telegram_client(account_manager.get_current_account()):
    print(f'{error} Failed to initialize primary account!')
    sys.exit(1)

# ====================
# DATA HANDLING (Original)
# ====================
def load_user_data(filename):
    users = []
    with open(filename, encoding='UTF-8') as f:
        reader = csv.reader(f, delimiter=',', lineterminator='\n')
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 5:
                users.append({
                    'username': row[0],
                    'user_id': row[1],
                    'access_hash': row[2],
                    'group': row[3],
                    'group_id': row[4]
                })
    return users

user_data = load_user_data(input_file)
if not user_data:
    print(f'{error} No valid users in {input_file}')
    sys.exit(1)

# ====================
# GROUP SETUP (Original)
# ====================
try:
    current_account = account_manager.get_current_account()
    target_group = current_account['client'].get_entity(group_link)
    group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    print(f'{info}{g} Target group: {target_group.title}{rs}')
except Exception as e:
    print(f'{error} Group error: {str(e)}')
    sys.exit(1)

# Get existing members (Original)
current_members = set()
try:
    participants = current_account['client'].get_participants(target_group)
    current_members = {user.username for user in participants if user.username}
    print(f'{info}{g} Found {len(current_members)} existing members{rs}')
except Exception as e:
    print(f'{error} Member fetch error: {str(e)}')

# ===================
# PROCESSING LOOP (Enhanced)
# ===================
total_processed = 0
success_count = 0
skip_count = 0
fail_count = 0
start_time = datetime.now()

for user in user_data:
    total_processed += 1
    current_account = account_manager.get_current_account()
    
    # Check for active account
    if not current_account or not current_account['active']:
        print(f'{error}{r} No active accounts remaining!{rs}')
        break
    
    client = current_account['client']
    is_premium = current_account['is_premium']
    
    # Configure delays (Original)
    min_delay = 5 if is_premium else 10
    max_delay = 10 if is_premium else 30
    batch_size = 100 if is_premium else 75
    
    # Skip existing (Original)
    if user['username'] in current_members:
        print(f'{sleep}{cy} Skipping {user["username"]} (exists){rs}')
        skip_count += 1
        continue
    
    # Batch pause (Original)
    if total_processed % batch_size == 0:
        print(f'{sleep}{g} Batch completed. 2-minute break...{rs}')
        countdown_timer(120)
    
    # Random delay (Original)
    delay = random.randint(min_delay, max_delay)
    print(f'{sleep}{g} Next in {delay}s | Acc: {current_account["phone"]}{rs}')
    countdown_timer(delay)
    
    # Account rotation (Original + Enhanced)
    if account_manager.increment_action():
        current_account = account_manager.get_current_account()
        client = current_account['client']
    
    # Attempt addition
    try:
        print(f'{attempt}{g} Adding {user["username"]} ({total_processed}/{len(user_data)}){rs}')
        target_user = client.get_input_entity(user['username'])
        client(InviteToChannelRequest(group_entity, [target_user]))
        
        success_count += 1
        current_members.add(user['username'])
        print(f'{attempt}{g} Added successfully!{rs}')
    
    except PeerFloodError as e:
        # Enhanced flood handling
        if account_manager.handle_flood_error(e):
            current_account = account_manager.get_current_account()
            if not current_account:
                break  # No accounts left
            continue
        
        # Original flood delay
        delay = min(delay * 2, 300)  # Max 5 min delay
        print(f'{sleep}{ye} Flood protection: Waiting {delay}s{rs}')
        countdown_timer(delay)
        continue
    
    except UserPrivacyRestrictedError:
        print(f'{error}{r} Privacy restriction for {user["username"]}{rs}')
        fail_count += 1
    
    except KeyboardInterrupt:
        print(f'\n{error}{r} INTERRUPTED! Saving progress...{rs}')
        break
    
    except Exception as e:
        print(f'{error}{r} Failed to add {user["username"]}: {str(e)}{rs}')
        fail_count += 1

# ===================
# FINAL REPORT (Original Style)
# ===================
end_time = datetime.now()
duration = end_time - start_time

print(f'\n{info}{g} {"="*50}{rs}')
print(f'{info}{g} PROCESSING SUMMARY:{rs}')
print(f'{info}{g} {"-"*50}{rs}')
print(f'{attempt}{g} Success: {success_count}{rs}')
print(f'{sleep}{cy} Skipped: {skip_count}{rs}')
print(f'{error}{r} Failed: {fail_count}{rs}')
print(f'{info}{g} Processed: {total_processed}/{len(user_data)}{rs}')
print(f'{info}{g} Active accounts: {len([a for a in account_manager.accounts if a["active"]])}/{len(account_manager.accounts)}{rs}')
print(f'{info}{g} Time: {duration}{rs}')
print(f'{info}{g} {"="*50}{rs}')

# Cleanup
for account in account_manager.accounts:
    if account['client']:
        account['client'].disconnect()

if os.name == 'nt':
    input('\nPress ENTER to exit...')
sys.exit(0)
