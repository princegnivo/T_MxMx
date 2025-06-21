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
    print(f'{info}{g} Telegram Group Adder V2.2 (Ultimate){rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx{rs}')
    print(f'{info}{cy} Premium/Standard Auto-Detect | Flood Protection | Live Counters{rs}\n')

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
    print(' ' * 50, end='\r')  # Clear line

clear_screen()
show_banner()

# ====================
# INPUT VALIDATION
# ====================
if len(sys.argv) < 6:
    print(f'{error} Usage: python usradder.py api_id api_hash phone_number csv_file group_link')
    sys.exit(1)

api_id, api_hash, phone = int(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3])
input_file, group_link = str(sys.argv[4]), str(sys.argv[5])

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
# CLIENT INITIALIZATION
# ====================
def setup_telegram_client(phone, api_id, api_hash):
    """Initialize and authenticate Telegram client"""
    session_path = f'sessions/{phone}'
    client = TelegramClient(session_path, api_id, api_hash)
    
    try:
        client.connect()
        
        if not client.is_user_authorized():
            print(f'{info} Authentication required. Sending code...')
            client.send_code_request(phone)
            code = input(f'{attempt} Enter verification code: ')
            client.sign_in(phone, code)
        
        # Premium account detection
        is_premium = False
        try:
            account_info = client(GetAccountTTLRequest())
            if hasattr(account_info, 'days') and account_info.days < 30:
                is_premium = True
                print(f'{premium} Premium account detected! Applying optimized settings')
        except Exception as e:
            print(f'{error} Account check error: {str(e)}')
        
        return client, is_premium
    
    except AuthKeyUnregisteredError:
        print(f'{error} Invalid session. Cleaning up...')
        if os.path.exists(f'{session_path}.session'):
            os.remove(f'{session_path}.session')
        return None, False
    except Exception as e:
        print(f'{error} Connection failed: {str(e)}')
        return None, False

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

client, is_premium_account = setup_telegram_client(phone, api_id, api_hash)
if not client:
    print(f'{error} Client initialization failed for {phone}')
    sys.exit(1)

# Load target group
try:
    target_group = client.get_entity(group_link)
    group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    group_title = target_group.title
    print(f'{info}{g} Target group: {group_title}{rs}')
except Exception as e:
    print(f'{error} Group access error: {str(e)}')
    client.disconnect()
    sys.exit(1)

# Get existing members
current_members = get_existing_members(client, target_group)
print(f'{info}{g} Found {len(current_members)} existing members{rs}')

# ===================
# CONFIGURATION
# ===================
if is_premium_account:
    base_delay = 5      # Shorter delay for premium
    flood_factor = 1   # Less aggressive backoff
    max_delay = 150      # 2.5 minutes maximum
    batch_size = 100      # Larger batch for premium
else:
    base_delay = 10      # Standard account delay
    flood_factor = 1.5     # Standard backoff
    max_delay = 300     # 5 minutes maximum
    batch_size = 75      # Standard batch size

# ===================
# PROCESSING LOOP
# ===================
total_processed = 0
success_count = 0
skip_count = 0
fail_count = 0
current_delay = base_delay
start_time = datetime.now()

for index, user in enumerate(user_data, 1):
    total_processed = index
    
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
    
    # Attempt to add user
    while True:
        try:
            print(f'\n{attempt}{g} Processing user {total_processed}/{len(user_data)}')
            print(f'{attempt}{g} Username: {user["username"]}{rs}')
            
            target_user = client.get_input_entity(user['username'])
            client(InviteToChannelRequest(group_entity, [target_user]))
            
            # Update counts and membership
            success_count += 1
            current_members.add(user['username'])
            current_delay = base_delay  # Reset delay on success
            
            print(f'{attempt}{g} Successfully added!{rs}')
            print(f'{sleep}{g} Standard delay: {base_delay}s{rs}')
            countdown_timer(base_delay)
            break
            
        except PeerFloodError:
            print(f'\n{error}{r} Flood limit reached!{rs}')
            print(f'{sleep}{ye} Current delay: {current_delay}s{rs}')
            countdown_timer(current_delay)
            
            # Exponential backoff
            current_delay = min(int(current_delay * flood_factor), max_delay)
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
client.disconnect()
end_time = datetime.now()
duration = end_time - start_time

print(f'\n{info}{g} {"="*50}{rs}')
print(f'{info}{g} PROCESSING COMPLETED:{rs}')
print(f'{info}{g} {"-"*50}{rs}')
print(f'{attempt}{g} Successful additions: {success_count}{rs}')
print(f'{sleep}{cy} Skipped (existing): {skip_count}{rs}')
print(f'{error}{r} Failed attempts: {fail_count}{rs}')
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
