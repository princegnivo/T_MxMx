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
ACCOUNT_SWITCH_THRESHOLD = 20  # Switch accounts every 20 actions
MAX_FLOOD_ERRORS = 5           # Flood errors before switch
CRITICAL_WAIT_TIME = 3600      # 1 hour (switch immediately if wait > this)
MAX_DELAY = 600                # 10 minutes maximum delay (added missing constant)

# ====================
# COLOR CONFIGURATION
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
# CORE FUNCTIONS
# =================
def show_banner():
    """Display the classic banner"""
    f = pyfiglet.Figlet(font='slant')
    logo = f.renderText('Telegram')
    print(random.choice(colors) + logo + rs)
    print(f'{info}{g} Telegram Group Adder V2.6 (Ultimate Pro){rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx{rs}')
    print(f'{info}{cy} Features: AI Account Switching | Military Flood Protection | Premium Turbo{rs}\n')

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def countdown_timer(seconds):
    """Enhanced countdown with visual feedback"""
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        progress = '█' * int(50 * (remaining/seconds))
        print(f'{countdown} [{progress.ljust(50)}] {mins:02d}:{secs:02d}', end='\r')
        time.sleep(1)
    print(' ' * 70, end='\r')

clear_screen()
show_banner()

# ====================
# ACCOUNT MANAGER
# ====================
class AccountManager:
    def __init__(self):
        self.accounts = []
        self.current_index = 0
        self.action_count = 0
        self.flood_errors = 0
        
    def add_account(self, phone, api_id, api_hash):
        """Add account with performance tracking"""
        self.accounts.append({
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash,
            'client': None,
            'is_premium': False,
            'active': True,
            'success_rate': 0
        })
    
    def get_current_account(self):
        """Get current active account"""
        if not self.accounts:
            return None
        return self.accounts[self.current_index]
    
    def rotate_account(self, force=False):
        """AI-optimized account rotation"""
        if len(self.accounts) <= 1 and not force:
            return False
        
        original_index = self.current_index
        best_score = -1
        best_index = -1
        
        # Find best available account
        for i, acc in enumerate(self.accounts):
            if not acc['active']:
                continue
                
            # Score based on success rate and freshness
            score = acc['success_rate'] * 100 + (10 if i != original_index else 0)
            
            if score > best_score:
                best_score = score
                best_index = i
        
        if best_index != -1 and best_index != original_index:
            self.current_index = best_index
            self.action_count = 0
            self.flood_errors = 0
            print(f'{info}{cy} Switched to optimal account: {self.get_current_account()["phone"]} '
                 f'(Score: {best_score:.1f}){rs}')
            return True
        
        return False
    
    def handle_flood_error(self, error_msg):
        """Military-grade flood protection"""
        wait_time = 0
        match = re.search(r'A wait of (\d+) seconds', str(error_msg))
        if match:
            wait_time = int(match.group(1))
        
        # Critical error - switch immediately
        if wait_time > CRITICAL_WAIT_TIME:
            print(f'{error}{r} CRITICAL FLOOD: Required wait {wait_time}s{rs}')
            self.accounts[self.current_index]['active'] = False
            return self.rotate_account(force=True)
        
        # Adaptive error counting
        self.flood_errors += max(1, wait_time // 60)
        
        if self.flood_errors >= MAX_FLOOD_ERRORS:
            return self.rotate_account()
        
        return False
    
    def update_success(self):
        """Update success metrics"""
        acc = self.get_current_account()
        if acc:
            acc['success_rate'] = 0.9 * acc['success_rate'] + 0.1
    
    def update_failure(self):
        """Update failure metrics"""
        acc = self.get_current_account()
        if acc:
            acc['success_rate'] = 0.9 * acc['success_rate']

# Initialize account manager
account_manager = AccountManager()

# ====================
# INPUT VALIDATION
# ====================
if len(sys.argv) < 6:
    print(f'{error} Usage: python usradder.py api_id api_hash phone_number csv_file group_link')
    sys.exit(1)

# Add primary account
api_id, api_hash, phone = int(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3])
input_file, group_link = str(sys.argv[4]), str(sys.argv[5])
account_manager.add_account(phone, api_id, api_hash)

# ====================
# CLIENT INITIALIZATION
# ====================
def setup_telegram_client(account):
    """Enhanced client setup with retries"""
    session_path = f'sessions/{account["phone"]}'
    max_retries = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            client = TelegramClient(session_path, account['api_id'], account['api_hash'])
            client.connect()
            
            if not client.is_user_authorized():
                print(f'{info} Auth required for {account["phone"]} (Attempt {attempt}/{max_retries})')
                client.send_code_request(account['phone'])
                code = input(f'{attempt} Enter code: ')
                client.sign_in(account['phone'], code)
            
            # Premium detection
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
            print(f'{error} Connection attempt {attempt} failed: {str(e)}')
            if attempt == max_retries:
                account['active'] = False
                return False
            time.sleep(2 ** attempt)
    
    return False

if not setup_telegram_client(account_manager.get_current_account()):
    print(f'{error} Critical: Account initialization failed!')
    sys.exit(1)

# ====================
# DATA PROCESSING
# ====================
def load_user_data(filename):
    """Robust CSV loader with validation"""
    users = []
    try:
        with open(filename, encoding='UTF-8') as f:
            reader = csv.reader(f, delimiter=',', lineterminator='\n')
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 5:  # Verify all required fields
                    users.append({
                        'username': row[0],
                        'user_id': row[1],
                        'access_hash': row[2],
                        'group': row[3],
                        'group_id': row[4]
                    })
        if not users:
            print(f'{error} File exists but contains no valid user data')
        return users
    except Exception as e:
        print(f'{error} Error reading file: {str(e)}')
        return []

user_data = load_user_data(input_file)
if not user_data:
    print(f'{error} No valid users found in {input_file}')
    sys.exit(1)

# ====================
# GROUP MANAGEMENT
# ====================
try:
    current_account = account_manager.get_current_account()
    target_group = current_account['client'].get_entity(group_link)
    group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    print(f'{info}{g} Target group: {target_group.title}{rs}')
except Exception as e:
    print(f'{error} Group access error: {str(e)}')
    sys.exit(1)

# ====================
# MEMBER CACHE
# ====================
def get_existing_members(client, group_entity):
    """Optimized member fetcher"""
    try:
        participants = client.get_participants(group_entity)
        return {user.username for user in participants if user.username}
    except Exception as e:
        print(f'{error} Member fetch error: {str(e)}')
        return set()

current_members = get_existing_members(current_account['client'], group_entity)
print(f'{info}{g} Found {len(current_members)} existing members{rs}')

# ===================
# PROCESSING LOOP
# ===================
total_processed = 0
success_count = 0
skip_count = 0
fail_count = 0
start_time = datetime.now()

for index, user in enumerate(user_data, 1):
    total_processed = index
    current_account = account_manager.get_current_account()
    
    if not current_account or not current_account['active']:
        print(f'{error} No active accounts remaining!')
        break
    
    client = current_account['client']
    is_premium = current_account['is_premium']
    
    # Dynamic configuration
    min_delay = 5 if is_premium else 10
    max_delay = 10 if is_premium else 30
    batch_size = 120 if is_premium else 80
    
    # Skip existing members
    if user['username'] in current_members:
        print(f'{sleep}{cy} Skipping {user["username"]} (exists){rs}')
        skip_count += 1
        continue
    
    # Smart batching
    if total_processed % batch_size == 0:
        cool_down = random.randint(120, 180)  # 2-3 minute randomized break
        print(f'{sleep}{g} Batch completed. Cooling down for {cool_down}s...{rs}')
        countdown_timer(cool_down)
    
    # Jitter-added delay
    base_delay = random.randint(min_delay, max_delay)
    jitter = random.uniform(-0.2, 0.2) * base_delay
    actual_delay = max(min_delay, base_delay + jitter)
    print(f'{sleep}{g} Next in {actual_delay:.1f}s | Acc: {current_account["phone"]}{rs}')
    countdown_timer(int(actual_delay))
    
    # Strategic account rotation
    if account_manager.action_count >= ACCOUNT_SWITCH_THRESHOLD:
        account_manager.rotate_account()
        current_account = account_manager.get_current_account()
        client = current_account['client']
    
    # Attempt addition
    try:
        print(f'{attempt}{g} Adding {user["username"]} ({total_processed}/{len(user_data)}){rs}')
        target_user = client.get_input_entity(user['username'])
        client(InviteToChannelRequest(group_entity, [target_user]))
        
        success_count += 1
        current_members.add(user['username'])
        account_manager.update_success()
        account_manager.action_count += 1
        print(f'{attempt}{g} Added successfully!{rs}')
    
    except PeerFloodError as e:
        account_manager.update_failure()
        if account_manager.handle_flood_error(str(e)):
            continue
        
        # Adaptive backoff with MAX_DELAY now properly defined
        backoff = min(2 + (account_manager.flood_errors / 2), 5)
        new_delay = min(actual_delay * backoff, MAX_DELAY)
        print(f'{sleep}{ye} Flood protection: Waiting {new_delay:.1f}s{rs}')
        countdown_timer(int(new_delay))
    
    except UserPrivacyRestrictedError:
        print(f'{error}{r} Privacy restriction for {user["username"]}{rs}')
        fail_count += 1
        account_manager.update_failure()
    
    except KeyboardInterrupt:
        print(f'\n{error}{r} INTERRUPTED! Saving progress...{rs}')
        break
    
    except Exception as e:
        print(f'{error}{r} Failed to add {user["username"]}: {str(e)}{rs}')
        fail_count += 1
        account_manager.update_failure()

# ===================
# FINAL REPORT
# ===================
end_time = datetime.now()
duration = end_time - start_time

print(f'\n{info}{g} {"="*60}{rs}')
print(f'{info}{g} MISSION SUMMARY:{rs}')
print(f'{info}{g} {"-"*60}{rs}')
print(f'{attempt}{g} Successes: {success_count} ({success_count/max(1,total_processed):.1%}){rs}')
print(f'{sleep}{cy} Skipped: {skip_count}{rs}')
print(f'{error}{r} Failures: {fail_count}{rs}')
print(f'{info}{g} Processed: {total_processed}/{len(user_data)}{rs}')
active_accounts = sum(1 for acc in account_manager.accounts if acc['active'])
print(f'{info}{g} Account Health: {active_accounts}/{len(account_manager.accounts)} active{rs}')
print(f'{info}{g} Duration: {duration}{rs}')
print(f'{info}{g} {"="*60}{rs}')

# Cleanup
for account in account_manager.accounts:
    if account['client']:
        account['client'].disconnect()

if os.name == 'nt':
    input('\nPress ENTER to exit...')
sys.exit(0)
