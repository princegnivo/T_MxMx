from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, AuthKeyUnregisteredError
from telethon.tl.functions.channels import InviteToChannelRequest
import sys
import csv
import time
import random
import pyfiglet
from colorama import init, Fore
import os

init()

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

def banner():
    f = pyfiglet.Figlet(font='slant')
    logo = f.renderText('Telegram')
    print(random.choice(colors) + logo + rs)
    print(f'{info}{g} Telegram Adder[USERNAME] V1.1{rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx{rs}\n')

def clscreen():
    os.system('clear' if os.name != 'nt' else 'cls')

clscreen()
banner()

# Input validation
if len(sys.argv) < 6:
    print(f'{error} Usage: python usradder.py api_id api_hash phone_number csv_file group_link')
    sys.exit(1)

api_id = int(sys.argv[1])
api_hash = str(sys.argv[2])
phone = str(sys.argv[3])
file = str(sys.argv[4])
group = str(sys.argv[5])

class Relog:
    def __init__(self, lst, filename):
        self.lst = lst
        self.filename = filename
    
    def start(self):
        with open(self.filename, 'w', encoding='UTF-8') as f:
            writer = csv.writer(f, delimiter=",", lineterminator="\n")
            writer.writerow(['username', 'user id', 'access hash', 'group', 'group id'])
            for user in self.lst:
                writer.writerow([user['username'], user['user_id'], user['access_hash'], user['group'], user['group_id']])

def update_list(lst, temp_lst):
    count = 0
    while count != len(temp_lst):
        del lst[0]
        count += 1
    return lst

def load_users(filename):
    users = []
    with open(filename, encoding='UTF-8') as f:
        rows = csv.reader(f, delimiter=',', lineterminator='\n')
        next(rows, None)
        for row in rows:
            if len(row) < 5:  # Skip incomplete rows
                continue
            user = {
                'username': row[0],
                'user_id': row[1],
                'access_hash': row[2],
                'group': row[3],
                'group_id': row[4]
            }
            users.append(user)
    return users

def initialize_client(phone, api_id, api_hash):
    session_path = f'sessions/{phone}'  # Changed to forward slash for cross-platform
    client = TelegramClient(session_path, api_id, api_hash)
    
    try:
        client.connect()
        
        if not client.is_user_authorized():
            print(f'{info} Session not authorized. Sending code...')
            client.send_code_request(phone)
            code = input(f'{attempt} Enter verification code: ')
            client.sign_in(phone, code)
        
        return client
    
    except AuthKeyUnregisteredError:
        print(f'{error} Auth key not registered. Removing session file...')
        if os.path.exists(f'{session_path}.session'):
            os.remove(f'{session_path}.session')
        return None
    except Exception as e:
        print(f'{error} Connection error: {str(e)}')
        return None

def get_already_added_users(group_entity):
    """Get list of users already in the group"""
    try:
        participants = client.get_participants(group_entity)
        return {user.username for user in participants if user.username}
    except Exception as e:
        print(f'{error} Error getting group participants: {str(e)}')
        return set()

users = load_users(file)
if not users:
    print(f'{error} No valid users found in {file}')
    sys.exit(1)

client = initialize_client(phone, api_id, api_hash)
if not client:
    print(f'{error} Failed to initialize client for {phone}')
    sys.exit(1)

try:
    target_group = client.get_entity(group)
    entity = InputPeerChannel(target_group.id, target_group.access_hash)
    group_name = target_group.title
    print(f'{info}{g} Adding members to {group_name}{rs}\n')
except Exception as e:
    print(f'{error} Failed to get group entity: {str(e)}')
    client.disconnect()
    sys.exit(1)

# Get list of users already in the group
already_added = get_already_added_users(target_group)
print(f'{info}{g} Found {len(already_added)} users already in the group{rs}')

n = 0
added_users = []
failed_users = []
skipped_users = []

for user in users:
    n += 1
    
    # Skip if user is already in the group
    if user['username'] in already_added:
        print(f'{sleep}{cy} Skipping {user["username"]} - already in group{rs}')
        skipped_users.append(user)
        continue
        
    added_users.append(user)
    
    if n % 50 == 0:
        print(f'{sleep}{g} Sleep 2 min to prevent possible account ban{rs}')
        time.sleep(120)
    
    try:
        if not user['username']:
            continue
            
        print(f'{attempt}{g} Attempting to add {user["username"]}{rs}')
        user_to_add = client.get_input_entity(user['username'])
        client(InviteToChannelRequest(entity, [user_to_add]))
        print(f'{attempt}{g} Successfully added {user["username"]}{rs}')
        
        # Add to already_added set to prevent re-adding
        already_added.add(user['username'])
        
        print(f'{sleep}{g} Sleep 5s after adding a user{rs}')
        time.sleep(5)
        
    except PeerFloodError:
        print(f'{error}{r} Peer Flood Error. Stopping...{rs}')
        update_list(users, added_users)
        if users:
            print(f'{info}{g} Saving remaining users to {file}')
            Relog(users, file).start()
        sys.exit(1)
    except UserPrivacyRestrictedError:
        print(f'{error}{r} User Privacy Restriction for {user["username"]}{rs}')
        failed_users.append(user)
        continue
    except KeyboardInterrupt:
        print(f'{error}{r} Aborted by user{rs}')
        update_list(users, added_users)
        if users:
            print(f'{info}{g} Saving remaining users to {file}')
            Relog(users, file).start()
        sys.exit(0)
    except Exception as e:
        print(f'{error}{r} Error adding {user["username"]}: {str(e)}{rs}')
        failed_users.append(user)
        continue

# Save failed users for retry
if failed_users:
    failed_file = f'failed_{os.path.basename(file)}'
    print(f'{info}{g} Saving {len(failed_users)} failed users to {failed_file}')
    Relog(failed_users, failed_file).start()

client.disconnect()
print(f'{info}{g} Adding complete. Processed {len(added_users)} users.{rs}')
print(f'{info}{cy} Skipped {len(skipped_users)} users already in the group.{rs}')
if os.name == 'nt':
    input('Press enter to exit...')
sys.exit(0)
    
