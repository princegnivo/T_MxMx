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
from datetime import datetime, timedelta

init()

# ====================
# CONFIGURATION
# ====================
ACCOUNT_SWITCH_THRESHOLD = 20  # Switch accounts every 20 actions
MAX_FLOOD_ERRORS_BEFORE_SWITCH = 5
MAX_ALLOWED_WAIT_TIME = 3600  # 1 hour (if wait time > this, switch account immediately)

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
    """Display the stylized banner"""
    f = pyfiglet.Figlet(font='slant')
    logo = f.renderText('Telegram')
    print(random.choice(colors) + logo + rs)
    print(f'{info}{g} Telegram Group Adder V2.4 (Emergency Switch){rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx{rs}')
    print(f'{info}{cy} Features: Emergency Account Switching | Flood Protection | Premium Detection{rs}\n')

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def countdown_timer(seconds):
    """Display animated countdown timer"""
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        time_str = f'{mins:02d}:{secs:02d}'
        print(f'{countdown} Waiting: {time_str} remaining', end='\r')
        time.sleep(1)
    print(' ' * 50, end='\r')

clear_screen()
show_banner()

# ====================
# ACCOUNT MANAGEMENT
# ====================
class AccountManager:
    def __init__(self):
        self.accounts = []
        self.current_index = 0
        self.action_count = 0
        self.flood_errors = 0
        
    def add_account(self, phone, api_id, api_hash):
        """Add a new account to the pool"""
        self.accounts.append({
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash,
            'client': None,
            'is_premium': False,
            'banned': False
        })
    
    def get_current_account(self):
        """Get current active account"""
        if not self.accounts:
            return None
        return self.accounts[self.current_index]
    
    def rotate_account(self):
        """Switch to next available account"""
        if len(self.accounts) <= 1:
            return False
        
        original_index = self.current_index
        while True:
            self.current_index = (self.current_index + 1) % len(self.accounts)
            
            # Stop if we've checked all accounts
            if self.current_index == original_index:
                return False
                
            # Skip banned accounts
            if not self.accounts[self.current_index]['banned']:
                self.action_count = 0
                self.flood_errors = 0
                print(f'{info}{cy} Rotated to account: {self.get_current_account()["phone"]}{rs}')
                return True
    
    def mark_account_banned(self, wait_time):
        """Mark current account as banned if wait time is excessive"""
        if wait_time > MAX_ALLOWED_WAIT_TIME:
            self.accounts[self.current_index]['banned'] = True
            print(f'{error}{r} Account temporarily banned (wait {wait_time}s). Marked as inactive.{rs}')
            return True
        return False
    
    def increment_action(self):
        """Track actions and rotate if threshold reached"""
        self.action_count += 1
        if self.action_count >= ACCOUNT_SWITCH_THRESHOLD:
            return self.rotate_account()
        return False
    
    def increment_flood_error(self):
        """Track flood errors and rotate if needed"""
        self.flood_errors += 1
        if self.flood_errors >= MAX_FLOOD_ERRORS_BEFORE_SWITCH:
            return self.rotate_account()
        return False

# Initialize account manager
account_manager = AccountManager()

# ====================
# INPUT VALIDATION
# ====================
if len(sys.argv) < 6:
    print(f'{error} Usage: python usradder.py api_id api_hash phone_number csv_file group_link')
    sys.exit(1)

# Add primary account from command line
api_id, api_hash, phone = int(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3])
input_file, group_link = str(sys.argv[4]), str(sys.argv[5])
account_manager.add_account(phone, api_id, api_hash)

# ====================
# CLIENT INITIALIZATION
# ====================
def setup_telegram_client(account):
    """Initialize and authenticate Telegram client"""
    session_path = f'sessions/{account["phone"]}'
    client = TelegramClient(session_path, account['api_id'], account['api_hash'])
    
    try:
        client.connect()
        
        if not client.is_user_authorized():
            print(f'{info} Authentication required for {account["phone"]}')
            client.send_code_request(account['phone'])
            code = input(f'{attempt} Enter verification code: ')
            client.sign_in(account['phone'], code)
        
        # Premium account detection
        is_premium = False
        try:
            account_info = client(GetAccountTTLRequest())
            if hasattr(account_info, 'days') and account_info.days < 30:
                is_premium = True
                print(f'{premium} Premium account detected!')
        except Exception as e:
            print(f'{error} Account check error: {str(e)}')
        
        account['client'] = client
        account['is_premium'] = is_premium
        return True
    
    except AuthKeyUnregisteredError:
        print(f'{error} Invalid session for {account["phone"]}')
        if os.path.exists(f'{session_path}.session'):
            os.remove(f'{session_path}.session')
        return False
    except Exception as e:
        print(f'{error} Connection failed: {str(e)}')
        return False

# Initialize all accounts
for account in account_manager.accounts:
    if not setup_telegram_client(account):
        print(f'{error} Failed to initialize account {account["phone"]}')
        sys.exit(1)

# ====================
# DATA HANDLING CLASS
# ====================
class UserDatabase:
    def __init__(self, user_data, filename):
        self.user_data = user_data
        self.filename = filename
    
    def save(self):
        """Save user data to CSV"""
        with open(self.filename, 'w', encoding='UTF-8') as f:
            writer = csv.writer(f, delimiter=",", lineterminator="\n")
            writer.writerow(['username', 'user id', 'access hash', 'group', 'group id'])
            for user in self.user_data:
                writer.writerow([user['username'], user['user_id'], user['access_hash'], user['group'], user['group_id']])

# ====================
# LOAD USER DATA
# ====================
def load_user_data(filename):
    """Load users from CSV file"""
    users = []
    with open(filename, encoding='UTF-8') as f:
        reader = csv.reader(f, delimiter=',', lineterminator='\n')
        next(reader, None)  # Skip header
        for row in reader:
            if len(row) < 5: continue  # Skip invalid rows
            users.append({
                'username': row[0],
                'user_id': row[1],
                'access_hash': row[2],
                'group': row[3],
                'group_id': row[4]
            })
    return users

# ====================
# GROUP MANAGEMENT
# ====================
def get_existing_members(client, group_entity):
    """Retrieve current group members"""
    try:
        participants = client.get_participants(group_entity)
        return {user.username for user in participants if user.username}
    except Exception as e:
        print(f'{error} Group member fetch error: {str(e)}')
        return set()

# ===================
# MAIN EXECUTION
# ===================
user_data = load_user_data(input_file)
if not user_data:
    print(f'{error} No valid users found in {input_file}')
    sys.exit(1)

# Load target group
try:
    current_account = account_manager.get_current_account()
    target_group = current_account['client'].get_entity(group_link)
    group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    group_title = target_group.title
    print(f'{info}{g} Target group: {group_title}{rs}')
except Exception as e:
    print(f'{error} Group access error: {str(e)}')
    sys.exit(1)

# Get existing members
current_members = get_existing_members(current_account['client'], target_group)
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
    client = current_account['client']
    is_premium = current_account['is_premium']
    
    # Configure delays based on account type
    if is_premium:
        min_delay = 5
        max_delay = 10
        batch_size = 100
        max_delay_flood = 150
    else:
        min_delay = 10
        max_delay = 30
        batch_size = 75
        max_delay_flood = 300
    
    # Skip existing members
    if user['username'] in current_members:
        print(f'{sleep}{cy} Skipping {user["username"]} (already member){rs}')
        skip_count += 1
        continue
    
    # Extended break every batch
    if total_processed % batch_size == 0:
        print(f'\n{sleep}{g} Batch completed. Taking extended 2-minute break...{rs}')
        countdown_timer(120)
        print(f'{attempt}{g} Resuming operations...{rs}')
    
    # Account rotation every N actions
    if account_manager.increment_action():
        current_account = account_manager.get_current_account()
        client = current_account['client']
        is_premium = current_account['is_premium']
        print(f'{info}{cy} Continuing with account: {current_account["phone"]}{rs}')
    
    # Random delay between operations
    current_delay = random.randint(min_delay, max_delay)
    print(f'{sleep}{g} Next operation in {current_delay} seconds{rs}')
    countdown_timer(current_delay)
    
    # Attempt to add user
    while True:
        try:
            print(f'\n{attempt}{g} Processing user {total_processed}/{len(user_data)}')
            print(f'{attempt}{g} Account: {current_account["phone"]} | User: {user["username"]}{rs}')
            
            target_user = client.get_input_entity(user['username'])
            client(InviteToChannelRequest(group_entity, [target_user]))
            
            success_count += 1
            current_members.add(user['username'])
            print(f'{attempt}{g} Successfully added!{rs}')
            break
            
        except PeerFloodError as e:
            # Extract wait time from error message
            wait_time = 0
            if "A wait of" in str(e):
                try:
                    wait_time = int(str(e).split("A wait of ")[1].split(" ")[0])
                except:
                    pass
            
            print(f'\n{error}{r} Flood limit reached! (Wait {wait_time}s){rs}')
            
            # Emergency switch if wait time is too long
            if wait_time > MAX_ALLOWED_WAIT_TIME:
                if account_manager.mark_account_banned(wait_time):
                    if not account_manager.rotate_account():
                        print(f'{error}{r} No available accounts! Stopping...{rs}')
                        sys.exit(1)
                    current_account = account_manager.get_current_account()
                    client = current_account['client']
                    is_premium = current_account['is_premium']
                    continue
            
            # Normal flood error handling
            if account_manager.increment_flood_error():
                current_account = account_manager.get_current_account()
                client = current_account['client']
                is_premium = current_account['is_premium']
                print(f'{info}{cy} Switched to account: {current_account["phone"]}{rs}')
            
            current_delay = min(int(current_delay * 1.5), max_delay_flood)
            print(f'{sleep}{ye} New delay: {current_delay}s{rs}')
            countdown_timer(current_delay)
            continue
            
        except UserPrivacyRestrictedError:
            print(f'{error}{r} Privacy restriction for {user["username"]}{rs}')
            fail_count += 1
            break
        except KeyboardInterrupt:
            print(f'\n{error}{r} Process interrupted! Saving progress...{rs}')
            if user_data:
                remaining_users = user_data[total_processed-1:]
                UserDatabase(remaining_users, input_file).save()
                print(f'{info} Saved {len(remaining_users)} remaining users')
            sys.exit(0)
        except Exception as e:
            print(f'{error}{r} Addition failed: {str(e)}{rs}')
            fail_count += 1
            break

# ===================
# FINAL REPORT
# ===================
for account in account_manager.accounts:
    if account['client']:
        account['client'].disconnect()

end_time = datetime.now()
duration = end_time - start_time

print(f'\n{info}{g} {"="*50}{rs}')
print(f'{info}{g} PROCESSING COMPLETED:{rs}')
print(f'{info}{g} {"-"*50}{rs}')
print(f'{attempt}{g} Successful additions: {success_count}{rs}')
print(f'{sleep}{cy} Skipped (existing): {skip_count}{rs}')
print(f'{error}{r} Failed attempts: {fail_count}{rs}')
print(f'{info}{g} Active accounts used: {len([a for a in account_manager.accounts if not a["banned"]])}{rs}')
print(f'{info}{g} Banned accounts: {len([a for a in account_manager.accounts if a["banned"]])}{rs}')
print(f'{info}{g} Total processed: {total_processed}/{len(user_data)}{rs}')
print(f'{info}{g} {"-"*50}{rs}')
print(f'{info}{g} Time elapsed: {duration}{rs}')
print(f'{info}{g} {"="*50}{rs}')

# Save failed users if any
if fail_count > 0:
    failed_users = [u for u in user_data if u['username'] not in current_members and u not in user_data[:total_processed]]
    if failed_users:
        failure_file = f'failed_{os.path.basename(input_file)}'
        UserDatabase(failed_users, failure_file).save()
        print(f'{info} Saved {len(failed_users)} failed attempts to {failure_file}')

if os.name == 'nt':
    input('\nPress ENTER to exit...')
sys.exit(0)
