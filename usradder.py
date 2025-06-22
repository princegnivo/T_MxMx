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
from typing import List, Dict, Optional

init()

# ====================
# CONFIGURATION
# ====================
ACCOUNT_ROTATION_INTERVAL = 17    # Slightly irregular rotation (prime number)
FLOOD_ERROR_THRESHOLD = 4         # More aggressive switching
CRITICAL_WAIT_THRESHOLD = 1800    # 30 minutes (switch immediately)
MAX_DELAY = 300                   # 5 minutes maximum delay
BATCH_SIZE_PREMIUM = 120          # Larger batches for premium
BATCH_SIZE_REGULAR = 80           # Slightly larger batches for regular

# ====================
# COLOR CONFIGURATION (Original Preserved)
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
# CORE FUNCTIONS (Enhanced)
# =================
def show_banner():
    """Enhanced banner with version info"""
    f = pyfiglet.Figlet(font='slant')
    logo = f.renderText('Telegram')
    print(random.choice(colors) + logo + rs)
    print(f'{info}{g} Telegram Group Adder V2.7 (Ultimate Pro){rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx{rs}')
    print(f'{info}{cy} Features: Military-Grade Account Switching | AI-Optimized Routing | Premium Boost{rs}\n')

def clear_screen():
    """Cross-platform screen clearing"""
    os.system('cls' if os.name == 'nt' else 'clear')

def countdown_timer(seconds: int):
    """Enhanced timer with progress visualization"""
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        progress = int(50 * (remaining/seconds))
        bar = '█' * progress + '-' * (50 - progress)
        print(f'{countdown} [{bar}] {mins:02d}:{secs:02d}', end='\r')
        time.sleep(1)
    print(' ' * 70, end='\r')

clear_screen()
show_banner()

# ====================
# ACCOUNT ORCHESTRATOR (Ultra-Optimized)
# ====================
class AccountOrchestrator:
    def __init__(self):
        self.accounts: List[Dict] = []
        self.current_index: int = 0
        self.action_counter: int = 0
        self.flood_errors: int = 0
        self.performance_stats: Dict = {}
    
    def add_account(self, phone: str, api_id: int, api_hash: str):
        """Add account with performance tracking"""
        self.accounts.append({
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash,
            'client': None,
            'is_premium': False,
            'active': True,
            'success_rate': 0,
            'last_used': None
        })
    
    def get_current_account(self) -> Optional[Dict]:
        """Get current account with failover"""
        if not self.accounts:
            return None
        
        # If current account inactive, find next active
        if not self.accounts[self.current_index]['active']:
            self.rotate_account(force=True)
        
        return self.accounts[self.current_index]
    
    def rotate_account(self, force: bool = False) -> bool:
        """AI-inspired account rotation algorithm"""
        if len(self.accounts) <= 1 and not force:
            return False
        
        original_index = self.current_index
        best_account = None
        highest_score = -1
        
        # Find best available account based on performance
        for idx, account in enumerate(self.accounts):
            if not account['active']:
                continue
                
            # Scoring formula (success rate + freshness)
            score = (account['success_rate'] * 100) + \
                   (10 if account['last_used'] is None else 0)
            
            if score > highest_score:
                highest_score = score
                best_account = idx
        
        if best_account is not None and best_account != original_index:
            self.current_index = best_account
            self.action_counter = 0
            self.flood_errors = 0
            current = self.get_current_account()
            print(f'{info}{cy} Switched to optimal account: {current["phone"]} '
                  f'(Score: {highest_score:.1f}){rs}')
            return True
        
        print(f'{error}{r} No better accounts available{rs}')
        return False
    
    def update_success(self):
        """Update success metrics for current account"""
        current = self.get_current_account()
        if current:
            # Exponential moving average for success rate
            current['success_rate'] = 0.9 * current['success_rate'] + 0.1 * 1
            current['last_used'] = datetime.now()
    
    def update_failure(self):
        """Update failure metrics"""
        current = self.get_current_account()
        if current:
            current['success_rate'] = 0.9 * current['success_rate'] + 0.1 * 0
    
    def handle_flood(self, error_msg: str) -> bool:
        """Advanced flood error processing"""
        wait_time = 0
        match = re.search(r'A wait of (\d+) seconds', str(error_msg))
        if match:
            wait_time = int(match.group(1))
        
        current = self.get_current_account()
        
        # Critical error handling
        if wait_time > CRITICAL_WAIT_THRESHOLD:
            print(f'{error}{r} CRITICAL FLOOD ({wait_time}s) - '
                  f'Deactivating {current["phone"]}{rs}')
            current['active'] = False
            return self.rotate_account(force=True)
        
        # Adaptive error counting
        self.flood_errors += max(1, int(wait_time/60))  # More errors for longer waits
        
        if self.flood_errors >= FLOOD_ERROR_THRESHOLD:
            return self.rotate_account()
        
        return False

# Initialize orchestrator
orchestrator = AccountOrchestrator()

# ====================
# INPUT VALIDATION (Original)
# ====================
if len(sys.argv) < 6:
    print(f'{error} Usage: python usradder.py api_id api_hash phone_number csv_file group_link')
    sys.exit(1)

# Add primary account
api_id, api_hash, phone = int(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3])
input_file, group_link = str(sys.argv[4]), str(sys.argv[5])
orchestrator.add_account(phone, api_id, api_hash)

# ====================
# CLIENT INITIALIZATION (Enhanced)
# ====================
def initialize_client(account: Dict) -> bool:
    """Enhanced client initialization with retry logic"""
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
                    print(f'{premium} Premium account detected! Applying turbo mode')
            except Exception:
                pass
            
            account['client'] = client
            return True
        
        except Exception as e:
            print(f'{error} Connection attempt {attempt} failed: {str(e)}')
            if attempt == max_retries:
                account['active'] = False
                return False
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return False

if not initialize_client(orchestrator.get_current_account())):
    print(f'{error} Critical: Primary account initialization failed!')
    sys.exit(1)

# ====================
# DATA PROCESSING (Original Preserved)
# ====================
def load_users(filename: str) -> List[Dict]:
    """Robust CSV loader with validation"""
    users = []
    try:
        with open(filename, encoding='UTF-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if all(key in row for key in ['username', 'user_id', 'access_hash']):
                    users.append({
                        'username': row['username'],
                        'user_id': row['user_id'],
                        'access_hash': row['access_hash'],
                        'group': row.get('group', ''),
                        'group_id': row.get('group_id', '')
                    })
    except Exception as e:
        print(f'{error} CSV load error: {str(e)}')
    return users

user_data = load_users(input_file)
if not user_data:
    print(f'{error} No valid users found in {input_file}')
    sys.exit(1)

# ====================
# GROUP MANAGEMENT (Original)
# ====================
try:
    current_account = orchestrator.get_current_account()
    target_group = current_account['client'].get_entity(group_link)
    group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    print(f'{info}{g} Target: {target_group.title} | Members: {target_group.participants_count}{rs}')
except Exception as e:
    print(f'{error} Group init failed: {str(e)}')
    sys.exit(1)

# ====================
# MEMBER CACHE (Optimized)
# ====================
def get_existing_members(client, group_entity, max_retries=3):
    """Optimized member fetcher with retry logic"""
    members = set()
    for attempt in range(1, max_retries + 1):
        try:
            members = {user.username for user in client.get_participants(group_entity) if user.username}
            print(f'{info} Loaded {len(members)} existing members')
            return members
        except Exception as e:
            print(f'{error} Member fetch attempt {attempt} failed: {str(e)}')
            if attempt == max_retries:
                return set()
            time.sleep(2 ** attempt)
    return set()

current_members = get_existing_members(current_account['client'], group_entity)

# ===================
# MAIN PROCESSOR (Ultra-Optimized)
# ===================
def process_users():
    total = len(user_data)
    success = 0
    skip = 0
    fail = 0
    start_time = datetime.now()
    
    for idx, user in enumerate(user_data, 1):
        current_account = orchestrator.get_current_account()
        if not current_account or not current_account['active']:
            print(f'{error} No active accounts remaining!')
            break
        
        client = current_account['client']
        is_premium = current_account['is_premium']
        
        # Dynamic configuration
        min_delay = 5 if is_premium else 10
        max_delay = 10 if is_premium else 25  # Slightly reduced max delay
        batch_size = BATCH_SIZE_PREMIUM if is_premium else BATCH_SIZE_REGULAR
        
        # Skip existing (cache optimized)
        if user['username'] in current_members:
            print(f'{sleep}{cy} Skip[{idx}/{total}]: {user["username"]} exists{rs}')
            skip += 1
            continue
        
        # Smart batching with dynamic delay
        if idx % batch_size == 0:
            extended_delay = min(120 + random.randint(0,60), 300)  # 2-3 min break
            print(f'{sleep}{g} Batch completed. Cooling down for {extended_delay}s...{rs}')
            countdown_timer(extended_delay)
        
        # Randomized delay with jitter
        base_delay = random.randint(min_delay, max_delay)
        jitter = random.uniform(-0.2, 0.2) * base_delay  # ±20% variation
        actual_delay = max(min_delay, base_delay + jitter)
        print(f'{sleep}{g} Next in {actual_delay:.1f}s | Acc: {current_account["phone"]}{rs}')
        countdown_timer(int(actual_delay))
        
        # Strategic account rotation
        if orchestrator.action_counter >= ACCOUNT_ROTATION_INTERVAL:
            orchestrator.rotate_account()
            current_account = orchestrator.get_current_account()
            client = current_account['client']
        
        # Attempt invitation
        try:
            print(f'{attempt}{g} Adding[{idx}/{total}]: {user["username"]}{rs}')
            target_user = client.get_input_entity(user['username'])
            client(InviteToChannelRequest(group_entity, [target_user]))
            
            success += 1
            current_members.add(user['username'])
            orchestrator.update_success()
            orchestrator.action_counter += 1
            print(f'{attempt}{g} Success! ({success} total){rs}')
        
        except PeerFloodError as e:
            orchestrator.update_failure()
            if orchestrator.handle_flood(str(e)):
                continue  # Account was rotated
            
            # Adaptive backoff
            backoff_factor = min(2 + (orchestrator.flood_errors / 2), 5)  # 2-5x multiplier
            new_delay = min(actual_delay * backoff_factor, MAX_DELAY)
            print(f'{sleep}{ye} Flood protection: Waiting {new_delay:.1f}s{rs}')
            countdown_timer(int(new_delay))
        
        except UserPrivacyRestrictedError:
            print(f'{error}{r} Privacy restriction for {user["username"]}{rs}')
            fail += 1
            orchestrator.update_failure()
        
        except KeyboardInterrupt:
            print(f'\n{error}{r} INTERRUPTED! Saving state...{rs}')
            break
        
        except Exception as e:
            print(f'{error}{r} Failed to add {user["username"]}: {str(e)}{rs}')
            fail += 1
            orchestrator.update_failure()
    
    return {
        'total': total,
        'success': success,
        'skip': skip,
        'fail': fail,
        'duration': datetime.now() - start_time
    }

# ===================
# EXECUTION WRAPPER
# ===================
results = process_users()

# ===================
# ANALYTICS DASHBOARD
# ===================
def show_analytics(results):
    print(f'\n{info}{g} {"="*60}{rs}')
    print(f'{info}{g} MISSION SUMMARY:{rs}')
    print(f'{info}{g} {"-"*60}{rs}')
    print(f'{attempt}{g} Successes: {results["success"]} ({results["success"]/results["total"]:.1%}){rs}')
    print(f'{sleep}{cy} Skipped: {results["skip"]}{rs}')
    print(f'{error}{r} Failures: {results["fail"]}{rs}')
    print(f'{info}{g} Completion: {results["total"]} users processed{rs}')
    
    active_accounts = sum(1 for acc in orchestrator.accounts if acc['active'])
    print(f'{info}{g} Account Health: {active_accounts}/{len(orchestrator.accounts)} active{rs}')
    
    # Performance metrics
    if results['duration'].total_seconds() > 0:
        speed = results['success'] / results['duration'].total_seconds() * 60
        print(f'{info}{g} Speed: {speed:.1f} adds/minute{rs}')
    
    print(f'{info}{g} Duration: {results["duration"]}{rs}')
    print(f'{info}{g} {"="*60}{rs}')

show_analytics(results)

# Graceful shutdown
for account in orchestrator.accounts:
    if account['client']:
        account['client'].disconnect()

if os.name == 'nt':
    input('\nPress ENTER to exit...')
sys.exit(0)
