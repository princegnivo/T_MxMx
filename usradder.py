import json
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.account import GetAccountTTLRequest
from telethon.network import ConnectionTcpMTProxyAbridged as ConnectionTcpMTProxy  # Updated import
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
ACCOUNT_SWITCH_THRESHOLD = 15  # Reduced for better rotation
MAX_FLOOD_ERRORS = 3            # More sensitive to flood errors
MAX_SUCCESSFUL_ADDS = 50        # Conservative limit per account
CRITICAL_WAIT_TIME = 1800       # 30 minutes (reduced from 1 hour)
MIN_DELAY = 8                   # Slightly reduced base delay
MAX_DELAY = 25                  # Reduced maximum delay
PROXY_TEST_TIMEOUT = 5          # Seconds to test proxy connection

# Load proxies from JSON file
def load_proxies():
    try:
        with open('proxy_list.json') as f:
            proxies = json.load(f)
            # Validate proxy format
            return [p for p in proxies if all(k in p for k in ['server', 'port', 'secret'])]
    except Exception:
        return []
        

# Color setup
r, g, rs, w, cy, ye = Fore.RED, Fore.GREEN, Fore.RESET, Fore.WHITE, Fore.CYAN, Fore.YELLOW
colors = [r, g, w, ye, cy]
info = g + '[' + w + 'i' + g + ']' + rs
attempt = g + '[' + w + '+' + g + ']' + rs
sleep = g + '[' + w + '*' + g + ']' + rs
error = g + '[' + r + '!' + g + ']' + rs
premium = g + '[' + ye + 'P' + g + ']' + rs

# Banner
def show_banner():
    f = pyfiglet.Figlet(font='slant')
    logo = random.choice(colors) + f.renderText('Telegram') + rs
    print(logo)
    print(f'{info}{g} Multi-Account Group Adder V5.0 {rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx {rs}')
    print(f'{info}{cy} Features: Intelligent Rotation | Proxy Support | Military Anti-Flood{rs}\n')

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
        self.proxies = load_proxies()
        self.current_proxy = None
    
    def get_next_proxy(self):
        if not self.proxies:
            return None
        
        # Try to find a working proxy
        for attempt in range(3):
            proxy = random.choice(self.proxies)
            try:
                # Test proxy connection
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
            'last_active': datetime.now(),
            'performance_score': 100,  # Initial score
            'errors': 0
        })
    
    def get_current_account(self):
        return self.accounts[self.current_index] if self.accounts else None
    
    def rotate_account(self, reason=""):
        if not self.accounts:
            return False
        
        print(f'\n{info}{cy} Rotation requested ({reason}){rs}')

        # Mark current account based on rotation reason
        current = self.get_current_account()
        if "flood" in reason.lower():
            current['performance_score'] -= 30
        elif "quota" in reason.lower():
            current['performance_score'] -= 10
        elif "error" in reason.lower():
            current['errors'] += 1
            current['performance_score'] -= 20 * current['errors']
        
        # Sort accounts by performance score (higher is better)
        self.accounts.sort(key=lambda x: x['performance_score'], reverse=True)
        
        original_index = self.current_index
        for idx, acc in enumerate(self.accounts):
            if idx == original_index:
                continue
            if acc['active']:
                self.current_index = idx
                self.action_count = 0
                self.flood_errors = 0
                
                # Random small delay between rotations
                time.sleep(random.uniform(0.5, 2))
                
                # Initialize client with proxy if available
                proxy = self.get_next_proxy()
                if proxy and self.setup_client(acc, proxy):
                    acc['last_active'] = datetime.now()
                    print(f'{info}{cy} Switched to {acc["phone"]} (Score: {acc["performance_score"]}){rs}')
                    if proxy:
                        print(f'{info}{cy} Using proxy: {proxy["server"]}:{proxy["port"]}{rs}')
                    return True
        
        return False
    
    def setup_client(self, account, proxy=None):
        try:
            proxy_config = None
            if proxy:
                proxy_config = (ConnectionTcpMTProxy, {
                    'ip': proxy['server'],
                    'port': proxy['port'],
                    'dc_id': 4,  # Doesn't matter for MTProxy
                    'mtproto_secret': bytes.fromhex(proxy['secret'])
                })
            
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
            account['errors'] = 0  # Reset error count
            return True
            
        except Exception as e:
            print(f'{error} Client setup failed: {str(e)}')
            account['active'] = False
            account['errors'] += 1
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
            return self.rotate_account("Critical flood wait")
        
        if self.flood_errors >= MAX_FLOOD_ERRORS:
            print(f'\n{error}{r} FLOOD LIMIT REACHED: Rotating immediately{rs}')
            return self.rotate_account("Flood limit reached")
        
        # Adaptive wait time with jitter
        adjusted_wait = wait_time * (1 + random.uniform(-0.2, 0.2))
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

# Initialize first account with proxy
current_account = account_manager.get_current_account()
if not account_manager.setup_client(current_account, account_manager.get_next_proxy()):
    print(f'{error} Critical: First account initialization failed!')
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
    client = current_account['client']
    target_group = client.get_entity(group_link)
    group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    print(f'{info}{g} Target: {target_group.title} | Members: {len(client.get_participants(target_group))}{rs}')
    
    # Get approximate group limits
    group_size = len(client.get_participants(target_group))
    if group_size > 10000:
        MAX_SUCCESSFUL_ADDS = 30  # Stricter limits for large groups
        print(f'{info}{cy} Large group detected - Adjusting limits for safety{rs}')
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
    
    # Check for proactive rotation conditions
    if (account_manager.successful_adds >= MAX_SUCCESSFUL_ADDS or
            account_manager.action_count >= ACCOUNT_SWITCH_THRESHOLD or
            (datetime.now() - current_account['last_active']).total_seconds() > 3600):
        
        reason = ""
        if account_manager.successful_adds >= MAX_SUCCESSFUL_ADDS:
            reason = "Usage quota reached"
        elif account_manager.action_count >= ACCOUNT_SWITCH_THRESHOLD:
            reason = "Action threshold"
        else:
            reason = "Inactivity timeout"
        
        if not account_manager.rotate_account(reason):
            print(f'{error} CONTINUING WITH SINGLE ACCOUNT')
    
    try:
        if not user['username']:
            print(f'{sleep}{ye} Skipping empty username{rs}')
            stats['invalid'] += 1
            continue
            
        client = current_account['client']
        
        # Check existing members (with caching would be better)
        participants = [p.username for p in client.get_participants(target_group) if p.username]
        if user['username'] in participants:
            print(f'{sleep}{cy} Skip: {user["username"]} exists{rs}')
            stats['skip'] += 1
            continue
        
        # Dynamic delay calculation
        base_delay = random.randint(MIN_DELAY, MAX_DELAY)
        if current_account['is_premium']:
            base_delay *= 0.7  # Premium accounts can go faster
        elif current_account['performance_score'] < 70:
            base_delay *= 1.3  # Slower for poorly performing accounts
        
        # Add random jitter
        final_delay = base_delay * (1 + random.uniform(-0.15, 0.15))
        
        print(f'\n{sleep} Delay: {final_delay:.1f}s | Acc: {current_account["phone"]} (Score: {current_account["performance_score"]})')
        countdown_timer(int(final_delay))
        
        print(f'\n{attempt} Adding {user["username"]} ({index}/{len(users)})')
        client(InviteToChannelRequest(group_entity, [client.get_input_entity(user['username'])]))
        
        stats['success'] += 1
        account_manager.action_count += 1
        account_manager.successful_adds += 1
        current_account['added_count'] += 1
        current_account['performance_score'] = min(100, current_account['performance_score'] + 1)  # Reward success
        
        print(f'{attempt}{g} Success! (Total: {account_manager.successful_adds}/{MAX_SUCCESSFUL_ADDS}){rs}')
        
    except PeerFloodError as e:
        stats['fail'] += 1
        current_account['performance_score'] -= 10
        if account_manager.handle_flood_error(str(e)):
            current_account = account_manager.get_current_account()
            continue
        countdown_timer(300)
        
    except UserPrivacyRestrictedError:
        print(f'{error} Privacy restriction for {user["username"]}')
        stats['fail'] += 1
        current_account['performance_score'] -= 5
        
    except Exception as e:
        print(f'{error} Failed to add {user["username"]}: {str(e)}')
        stats['fail'] += 1
        current_account['errors'] += 1
        current_account['performance_score'] -= 15
        
        # Critical error - rotate immediately
        if "auth" in str(e).lower() or "session" in str(e).lower():
            print(f'{error} CRITICAL ERROR: Rotating account')
            account_manager.rotate_account("Authentication error")

# Final report
duration = datetime.now() - start_time
accounts_used = len([acc for acc in account_manager.accounts if acc['active'] and acc['added_count'] > 0])
success_rate = stats['success'] / max(1, index) * 100

print(f'\n{info}{g} {"="*60}{rs}')
print(f'{info}{g} OPERATION COMPLETE:{rs}')
print(f'{info}{g} {"-"*60}{rs}')
print(f'{attempt}{g} Successes: {stats["success"]} ({success_rate:.1f}%){rs}')
print(f'{sleep}{cy} Skipped: {stats["skip"]} (existing){rs}')
print(f'{sleep}{ye} Invalid: {stats["invalid"]} (bad usernames){rs}')
print(f'{error}{r} Failures: {stats["fail"]}{rs}')
print(f'\n{info}{g} Accounts used: {accounts_used}/{len(account_manager.accounts)}{rs}')
print(f'{info}{g} Duration: {duration}{rs}')
print(f'{info}{g} Proxy usage: {account_manager.current_proxy["server"] if account_manager.current_proxy else "None"}{rs}')
print(f'{info}{g} {"="*60}{rs}')

# Cleanup
for acc in account_manager.accounts:
    if acc.get('client'):
        try:
            acc['client'].disconnect()
        except:
            pass
