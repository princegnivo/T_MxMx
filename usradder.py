import json
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.errors.rpcerrorlist import (
    PeerFloodError, 
    UserPrivacyRestrictedError, 
    FloodWaitError,
    ChannelInvalidError,
    ChannelPrivateError
)
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
import asyncio
import aiohttp

init()

# Enhanced Configuration
ACCOUNT_SWITCH_THRESHOLD = 15
MAX_FLOOD_ERRORS = 2
MAX_SUCCESSFUL_ADDS = 50
CRITICAL_WAIT_TIME = 1800
MIN_DELAY = 8
MAX_DELAY = 25
PROXY_TEST_TIMEOUT = 5
MAX_RETRIES = 3
CHANNEL_VALIDATION_RETRIES = 2
PROXY_REFRESH_INTERVAL = 30  # Minutes between proxy refreshes
PROXY_ROTATION_COUNT = 10  # Rotate proxy after adding this many members
SUCCESS_RATE_THRESHOLD = 0.7  # Minimum success rate to maintain
MAX_USER_CACHE_SIZE = 1000  # Maximum number of users to cache

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
    print(f'{info}{g} Ultimate Group Adder V3.2 {rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx {rs}')
    print(f'{info}{cy} Features: Auto-Proxy Retrieval | Smart Rotation | Premium Detection | Anti-Flood{rs}\n')
    print(f'{info}{ye} Advanced Features: User Caching | Performance Tracking | Adaptive Rate Limiting{rs}\n')

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

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_proxy = None
        self.last_refresh = None
        self.proxy_usage_count = 0
        self.proxy_stats = {}  # Track proxy performance
    
    async def fetch_proxies_from_channel(self, client):
        """Enhanced proxy fetching from @ProxyMTProto with robust parsing"""
        try:
            print(f'{info} Fetching fresh proxies from @ProxyMTProto')
            channel = await client.get_entity("https://t.me/ProxyMTProto")
            messages = await client.get_messages(channel, limit=100)  # Get more messages
            
            new_proxies = []
            proxy_patterns = [
                # Pattern 1: Standard MTProto format
                re.compile(
                    r'(?:server|host|ip|адрес)[:\s]*([^\n]+)\n'
                    r'(?:port|порт)[:\s]*(\d{1,5})\n'
                    r'(?:secret|ключ|секрет)[:\s]*([^\n]+)',
                    re.IGNORECASE
                ),
                # Pattern 2: Inline format (server:port:secret)
                re.compile(
                    r'([^\s:]+)[:\s](\d{1,5})[:\s]([^\s]+)'
                ),
                # Pattern 3: JSON-like format
                re.compile(
                    r'{[^{}]*"server"[^"]*"([^"]+)"[^{}]*"port"[^"]*"(\d{1,5})"[^{}]*"secret"[^"]*"([^"]+)"[^{}]*}',
                    re.IGNORECASE
                )
            ]
            
            for msg in messages:
                if msg.text:
                    text = msg.text.replace('`', '')  # Remove code markdown
                    for pattern in proxy_patterns:
                        matches = pattern.finditer(text)
                        for match in matches:
                            try:
                                server = match.group(1).strip()
                                port = self.parse_proxy_port(match.group(2))
                                secret = match.group(3).strip()
                                
                                if not all([server, port, secret]):
                                    continue
                                    
                                proxy = {
                                    'server': server,
                                    'port': port,
                                    'secret': secret,
                                    'source': 'ProxyMTProto',
                                    'last_checked': datetime.now().isoformat(),
                                    'success_rate': 1.0,
                                    'response_time': 0,
                                    'last_used': None
                                }
                                
                                new_proxies.append(proxy)
                            except (IndexError, AttributeError, ValueError):
                                continue
            
            # Remove duplicates
            unique_proxies = []
            seen = set()
            for p in new_proxies:
                key = (p['server'], p['port'])
                if key not in seen:
                    seen.add(key)
                    unique_proxies.append(p)
            
            if unique_proxies:
                self.proxies = unique_proxies
                self.last_refresh = datetime.now()
                self.save_proxies()
                print(f'{info} Found {len(self.proxies)} valid proxies')
                return True
            else:
                print(f'{error} No valid proxies found in channel messages')
                return False
            
        except Exception as e:
            print(f'{error} Failed to fetch proxies: {str(e)}')
            return False
    
    def parse_proxy_port(self, port_str):
        """Safe port number parsing"""
        try:
            port = int(''.join(filter(str.isdigit, port_str)))
            return port if 1 <= port <= 65535 else None
        except ValueError:
            return None
    
    def load_proxies(self):
        """Load proxies from JSON file"""
        try:
            if os.path.exists('proxy_list.json'):
                with open('proxy_list.json', 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.proxies = data
                        self.last_refresh = datetime.now()
                        print(f'{info} Loaded {len(self.proxies)} proxies from file')
                        return True
            return False
        except Exception as e:
            print(f'{error} Failed to load proxies: {str(e)}')
            return False
    
    def save_proxies(self):
        """Save proxies to JSON file with pretty formatting"""
        try:
            with open('proxy_list.json', 'w') as f:
                json.dump(self.proxies, f, indent=2, ensure_ascii=False)
                print(f'{info} Saved {len(self.proxies)} proxies to proxy_list.json')
        except Exception as e:
            print(f'{error} Failed to save proxies: {str(e)}')
    
    async def get_next_proxy(self, client=None):
        """Get the next working proxy with intelligent selection"""
        # Rotate if we've used current proxy enough times or it's performing poorly
        if (self.proxy_usage_count >= PROXY_ROTATION_COUNT or 
            (self.current_proxy and self.current_proxy.get('success_rate', 1.0) < SUCCESS_RATE_THRESHOLD)):
            self.proxy_usage_count = 0
            self.current_proxy = None
        
        # Return current proxy if still valid
        if self.current_proxy and await self.test_proxy(self.current_proxy):
            self.proxy_usage_count += 1
            self.current_proxy['last_used'] = datetime.now()
            return self.current_proxy
        
        # Check if we need to refresh proxies
        if (not self.proxies or 
            not self.last_refresh or
            (datetime.now() - self.last_refresh).total_seconds() > PROXY_REFRESH_INTERVAL * 60):
            if client:
                await self.fetch_proxies_from_channel(client)
            else:
                self.load_proxies()
        
        if not self.proxies:
            print(f'{error} No proxies available')
            return None
        
        # Sort proxies by success rate, response time, and freshness
        sorted_proxies = sorted(
            self.proxies,
            key=lambda x: (
                -x.get('success_rate', 1.0), 
                x.get('response_time', 0),
                x.get('last_used', datetime.min) if x.get('last_used') else datetime.min
            )
        )
        
        # Test top proxies until we find a working one
        for proxy in sorted_proxies[:20]:  # Only test top 20 performers
            if await self.test_proxy(proxy):
                self.current_proxy = proxy
                self.proxy_usage_count = 1
                proxy['last_used'] = datetime.now()
                return proxy
        
        print(f'{error} No working proxies found')
        return None
    
    async def test_proxy(self, proxy):
        """Test if proxy is working with connection and speed test"""
        try:
            start_time = time.time()
            
            # Test TCP connection first
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(proxy['server'], proxy['port']),
                timeout=PROXY_TEST_TIMEOUT
            )
            writer.close()
            await writer.wait_closed()
            
            # Record response time
            proxy['response_time'] = time.time() - start_time
            return True
        except Exception:
            return False
    
    def update_proxy_stats(self, success):
        """Update proxy performance metrics"""
        if not self.current_proxy:
            return
            
        proxy_key = (self.current_proxy['server'], self.current_proxy['port'])
        
        # Initialize stats if not exists
        if proxy_key not in self.proxy_stats:
            self.proxy_stats[proxy_key] = {
                'attempts': 0,
                'successes': 0,
                'response_times': []
            }
        
        stats = self.proxy_stats[proxy_key]
        stats['attempts'] += 1
        if success:
            stats['successes'] += 1
            stats['response_times'].append(self.current_proxy['response_time'])
            if len(stats['response_times']) > 10:
                stats['response_times'].pop(0)
        
        # Calculate success rate and average response time
        success_rate = stats['successes'] / stats['attempts'] if stats['attempts'] > 0 else 1.0
        avg_response = sum(stats['response_times'])/len(stats['response_times']) if stats['response_times'] else 0
        
        self.current_proxy['success_rate'] = success_rate
        self.current_proxy['response_time'] = avg_response

class AccountManager:
    def __init__(self, group_link):
        self.accounts = []
        self.current_index = 0
        self.action_count = 0
        self.flood_errors = 0
        self.successful_adds = 0
        self.proxy_manager = ProxyManager()
        self.group_entity = None
        self.target_group = None
        self.group_link = group_link
        self.user_cache = {}  # Cache user entities to reduce API calls
        self.participants_cache = {
            'users': set(),
            'last_updated': None,
            'valid_for': 300  # 5 minutes cache validity
        }
    
    def add_account(self, phone, api_id, api_hash):
        self.accounts.append({
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash,
            'client': None,
            'is_premium': False,
            'added_count': 0,
            'last_active': None,
            'errors': 0,
            'is_active': True,
            'success_rate': 1.0,
            'last_10_results': [],
            'total_attempts': 0,
            'total_successes': 0,
            'consecutive_fails': 0
        })
    
    def get_current_account(self):
        return self.accounts[self.current_index] if self.accounts else None
    
    def get_best_account(self):
        """Get the most effective account based on performance metrics"""
        active_accounts = [acc for acc in self.accounts if acc['is_active']]
        if not active_accounts:
            return None
        
        # Sort by success rate (higher first), then by premium status
        active_accounts.sort(
            key=lambda x: (
                x['success_rate'], 
                x['is_premium'],
                -x['errors'],
                -x['consecutive_fails']
            ), 
            reverse=True
        )
        return active_accounts[0]
    
    def calculate_delay(self, account):
        """Calculate adaptive delay based on account performance"""
        base_delay = random.uniform(MIN_DELAY, MAX_DELAY)
        
        # Premium accounts get shorter delays
        if account['is_premium']:
            base_delay *= 0.6  # More aggressive reduction for premium
        
        # Adjust based on recent success rate
        if account['success_rate'] < SUCCESS_RATE_THRESHOLD:
            base_delay *= (1.0 + (1.0 - account['success_rate']))  # Exponential backoff for failing accounts
        elif account['success_rate'] > 0.9:
            base_delay *= 0.7  # More aggressive reduction for high performers
            
        # Increase delay if we have consecutive failures
        if account['consecutive_fails'] > 0:
            base_delay *= (1.0 + (account['consecutive_fails'] * 0.3))
            
        return max(MIN_DELAY, min(MAX_DELAY * 2, base_delay))  # Allow longer delays when needed
    
    async def rotate_account(self, reason=""):
        """Rotate to best available account with proper cleanup"""
        if len(self.accounts) <= 1:
            return False
        
        print(f'\n{info}{cy} ACCOUNT ROTATION: {reason}{rs}')
        
        # Properly disconnect current client
        current_acc = self.get_current_account()
        if current_acc and current_acc['client']:
            try:
                await current_acc['client'].disconnect()
            except:
                pass
        
        # Find the best available account
        best_account = self.get_best_account()
        if not best_account:
            print(f'{error} All accounts exhausted or inactive{rs}')
            return False
        
        self.current_index = self.accounts.index(best_account)
        self.action_count = 0
        self.flood_errors = 0
        
        time.sleep(random.uniform(1, 3))
        
        proxy = await self.proxy_manager.get_next_proxy(self.get_current_account()['client'])
        if await self.setup_client(self.get_current_account(), proxy):
            print(f'{info}{cy} Switched to {self.get_current_account()["phone"]} (Success: {self.get_current_account()["success_rate"]:.0%}){rs}')
            return True
        
        return False
    
    async def setup_client(self, account, proxy=None):
        try:
            proxy_config = None
            if proxy:
                # Enhanced MTProto proxy configuration
                proxy_config = {
                    'proxy_type': 'mtproto',
                    'addr': proxy['server'],
                    'port': proxy['port'],
                    'secret': proxy.get('secret', '')
                }
            
            client = TelegramClient(
                f'sessions/{account["phone"]}',
                account['api_id'],
                account['api_hash'],
                proxy=proxy_config,
                connection_retries=3,
                request_retries=3,
                auto_reconnect=True
            )
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.send_code_request(account['phone'])
                code = input(f'{info} Enter code for {account["phone"]}: ')
                await client.sign_in(account['phone'], code)
            
            try:
                account_ttl = await client(GetAccountTTLRequest())
                account['is_premium'] = account_ttl.days > 7 if hasattr(account_ttl, 'days') else False
            except Exception:
                account['is_premium'] = False
            
            account['client'] = client
            account['last_active'] = datetime.now()
            account['is_active'] = True
            
            # Fetch fresh proxies on first setup
            if not self.proxy_manager.proxies:
                await self.proxy_manager.fetch_proxies_from_channel(client)
            
            return True
            
        except Exception as e:
            print(f'{error} Account setup failed: {str(e)}')
            account['is_active'] = False
            account['errors'] += 1
            return False
    
    async def handle_flood_error(self, error_msg):
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
            return await self.rotate_account("Critical flood")
        
        if self.flood_errors >= MAX_FLOOD_ERRORS:
            print(f'\n{error}{r} FLOOD LIMIT REACHED: Rotating immediately{rs}')
            return await self.rotate_account("Flood limit")
        
        adjusted_wait = wait_time * random.uniform(0.8, 1.2)
        countdown_timer(int(adjusted_wait))
        return False
    
    async def validate_channel(self, client):
        """Validate the channel connection with retries"""
        for attempt in range(CHANNEL_VALIDATION_RETRIES):
            try:
                self.target_group = await client.get_entity(self.group_link)
                self.group_entity = InputPeerChannel(
                    self.target_group.id, 
                    self.target_group.access_hash
                )
                return True
            except (ChannelInvalidError, ChannelPrivateError) as e:
                print(f'{error} Channel validation failed (attempt {attempt + 1}/{CHANNEL_VALIDATION_RETRIES}): {str(e)}')
                if attempt < CHANNEL_VALIDATION_RETRIES - 1:
                    time.sleep(5)
                    continue
                return False
            except Exception as e:
                print(f'{error} Unexpected channel validation error: {str(e)}')
                return False
    
    async def get_participants(self, client, force_refresh=False):
        """Get channel participants with caching"""
        if (not force_refresh and 
            self.participants_cache['last_updated'] and 
            (datetime.now() - self.participants_cache['last_updated']).total_seconds() < self.participants_cache['valid_for']):
            return self.participants_cache['users']
        
        try:
            participants = await client.get_participants(self.target_group)
            self.participants_cache['users'] = {p.username for p in participants if p.username}
            self.participants_cache['last_updated'] = datetime.now()
            return self.participants_cache['users']
        except Exception as e:
            print(f'{error} Failed to get participants: {str(e)}')
            return set()
    
    def update_account_stats(self, account, success):
        """Update account performance metrics"""
        account['last_10_results'].append(success)
        if len(account['last_10_results']) > 10:
            account['last_10_results'].pop(0)
        
        account['total_attempts'] += 1
        if success:
            account['total_successes'] += 1
            account['consecutive_fails'] = 0
        else:
            account['consecutive_fails'] += 1
        
        account['success_rate'] = (
            account['total_successes'] / account['total_attempts'] 
            if account['total_attempts'] > 0 
            else 1.0
        )
    
    def cleanup_user_cache(self):
        """Clean up user cache if it gets too large"""
        if len(self.user_cache) > MAX_USER_CACHE_SIZE:
            # Remove oldest entries
            cache_items = sorted(self.user_cache.items(), key=lambda x: x[1]['last_used'])
            for i in range(len(cache_items) - MAX_USER_CACHE_SIZE):
                del self.user_cache[cache_items[i][0]]

async def main():
    # Flexible argument handling
    if len(sys.argv) < 6:
        print(f'\n{error} Usage:')
        print(f'{info} Single account: python usradder.py api_id api_hash phone csv_file groupname')
        print(f'{info} Multiple accounts: python usradder.py api_id1 api_hash1 phone1 api_id2 api_hash2 phone2 csv_file groupname')
        return

    # Extract csv_file and group_link
    input_file = sys.argv[-2]
    group_link = sys.argv[-1]

    # Initialize account manager with group link
    account_manager = AccountManager(group_link)

    # Process account arguments
    account_args = sys.argv[1:-2]
    if len(account_args) % 3 != 0:
        print(f'{error} Each account requires 3 parameters: api_id api_hash phone')
        return

    for i in range(0, len(account_args), 3):
        try:
            api_id = int(account_args[i])
            api_hash = account_args[i+1]
            phone = account_args[i+2]
            account_manager.add_account(phone, api_id, api_hash)
        except (ValueError, IndexError) as e:
            print(f'{error} Invalid account parameters: {str(e)}')
            return

    # Initialize first account and set up group entity
    if not await account_manager.setup_client(account_manager.get_current_account()):
        print(f'{error} First account initialization failed!')
        return

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
        return

    # Group setup - with validation
    if not await account_manager.validate_channel(account_manager.get_current_account()['client']):
        print(f'{error} Failed to validate target group!')
        return

    try:
        client = account_manager.get_current_account()['client']
        participants = await account_manager.get_participants(client, force_refresh=True)
        print(f'{info}{g} Target: {account_manager.target_group.title} | Members: {len(participants)}{rs}')
    except Exception as e:
        print(f'{error} Group error: {str(e)}')
        return

    start_time = datetime.now()
    stats = {'success': 0, 'skip': 0, 'fail': 0, 'invalid': 0}

    for index, user in enumerate(users, 1):
        current_account = account_manager.get_current_account()
        
        # Smart account rotation based on multiple factors
        rotation_triggers = [
            (account_manager.flood_errors >= MAX_FLOOD_ERRORS, f"{MAX_FLOOD_ERRORS}+ flood errors"),
            (account_manager.action_count >= ACCOUNT_SWITCH_THRESHOLD, f"{ACCOUNT_SWITCH_THRESHOLD} action threshold"),
            (current_account['errors'] >= 3, "3+ account errors"),
            (account_manager.successful_adds >= MAX_SUCCESSFUL_ADDS, f"{MAX_SUCCESSFUL_ADDS} quota reached"),
            ((datetime.now() - current_account['last_active']).total_seconds() > 1800, "30m inactivity"),
            (current_account['success_rate'] < 0.5, "Low success rate (<50%)"),
            (current_account['consecutive_fails'] > 2, f"{current_account['consecutive_fails']} consecutive fails"),
            (not current_account['is_premium'] and random.random() < 0.1, "Random non-premium rotation")
        ]

        for condition, reason in rotation_triggers:
            if condition:
                if await account_manager.rotate_account(reason):
                    current_account = account_manager.get_current_account()
                    client = current_account['client']
                    # Revalidate channel after rotation
                    if not await account_manager.validate_channel(client):
                        print(f'{error} Failed to validate channel after rotation!')
                        stats['fail'] += 1
                        current_account['errors'] += 1
                        account_manager.update_account_stats(current_account, False)
                        continue
                break
        
        try:
            if not user['username']:
                print(f'{sleep}{ye} Skipping empty username{rs}')
                stats['invalid'] += 1
                continue
                
            client = current_account['client']
            
            # Check participants cache first
            participants = await account_manager.get_participants(client)
            if user['username'] in participants:
                print(f'{sleep}{cy} Skip: {user["username"]} exists{rs}')
                stats['skip'] += 1
                continue
            
            # Check user cache first
            if user['username'] in account_manager.user_cache:
                user_entity = account_manager.user_cache[user['username']]['entity']
            else:
                # Resolve user entity
                try:
                    user_entity = await client.get_input_entity(user['username'])
                    account_manager.user_cache[user['username']] = {
                        'entity': user_entity,
                        'last_used': datetime.now()
                    }
                    account_manager.cleanup_user_cache()
                except Exception as e:
                    print(f'{error} Failed to resolve user {user["username"]}: {str(e)}')
                    stats['fail'] += 1
                    current_account['errors'] += 1
                    account_manager.update_account_stats(current_account, False)
                    continue
            
            # Calculate adaptive delay
            delay = account_manager.calculate_delay(current_account)
            print(f'\n{sleep} Delay: {delay:.1f}s | Acc: {current_account["phone"]} (SR: {current_account["success_rate"]:.0%})')
            countdown_timer(int(delay))
            
            print(f'\n{attempt} Adding {user["username"]} ({index}/{len(users)})')
            try:
                await client(InviteToChannelRequest(
                    account_manager.group_entity, 
                    [user_entity]
                ))
                stats['success'] += 1
                account_manager.action_count += 1
                account_manager.successful_adds += 1
                current_account['added_count'] += 1
                account_manager.update_account_stats(current_account, True)
                account_manager.proxy_manager.update_proxy_stats(True)
                print(f'{attempt}{g} Success! (Total: {account_manager.successful_adds}/{MAX_SUCCESSFUL_ADDS}){rs}')
            except Exception as e:
                print(f'{error} Failed to add {user["username"]}: {str(e)}')
                stats['fail'] += 1
                current_account['errors'] += 1
                account_manager.update_account_stats(current_account, False)
                account_manager.proxy_manager.update_proxy_stats(False)
                
                if "database is locked" in str(e):
                    print(f'{error} Database is locked. Attempting to rotate account.')
                    if await account_manager.rotate_account("Database locked"):
                        continue
                
                if "Invalid channel object" in str(e) or "ChannelInvalidError" in str(e):
                    print(f'{error} Invalid channel object for {user["username"]}. Skipping.')
                    continue
                
                if "auth" in str(e).lower() or "session" in str(e).lower():
                    print(f'{error} CRITICAL ERROR: Rotating account')
                    if await account_manager.rotate_account("Authentication error"):
                        continue
        
        except PeerFloodError as e:
            stats['fail'] += 1
            current_account['errors'] += 1
            account_manager.update_account_stats(current_account, False)
            account_manager.proxy_manager.update_proxy_stats(False)
            if await account_manager.handle_flood_error(str(e)):
                continue
            countdown_timer(300)
            
        except UserPrivacyRestrictedError:
            print(f'{error} Privacy restriction for {user["username"]}')
            stats['fail'] += 1
            current_account['errors'] += 1
            account_manager.update_account_stats(current_account, False)
            account_manager.proxy_manager.update_proxy_stats(False)

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
    print(f'{info}{g} Processing speed: {len(users)/max(1, duration.total_seconds()/60):.1f} users/min{rs}')
    
    # Account performance details
    print(f'\n{info}{g} ACCOUNT PERFORMANCE:{rs}')
    for acc in sorted(account_manager.accounts, key=lambda x: x['success_rate'], reverse=True):
        status = "ACTIVE" if acc['is_active'] else "INACTIVE"
        premium = "PREMIUM" if acc['is_premium'] else "REGULAR"
        print(f'{info} {acc["phone"]}: {status} | {premium} | Success: {acc["success_rate"]:.0%} | Added: {acc["added_count"]}')
    
    # Proxy performance details
    if account_manager.proxy_manager.current_proxy:
        current_proxy = account_manager.proxy_manager.current_proxy
        print(f'\n{info}{g} CURRENT PROXY:{rs}')
        print(f'{info} {current_proxy["server"]}:{current_proxy["port"]}')
        print(f'{info} Success rate: {current_proxy.get("success_rate", 1.0):.0%}')
        print(f'{info} Avg response: {current_proxy.get("response_time", 0):.2f}s')
    
    # User cache stats
    print(f'\n{info}{g} CACHE STATS:{rs}')
    print(f'{info} Users cached: {len(account_manager.user_cache)}')
    print(f'{info} Participants cache hits: {len(users) - stats["success"] - stats["fail"] - stats["invalid"]}')
    print(f'{info}{g} {"="*60}{rs}')

    # Save proxy stats for next run
    account_manager.proxy_manager.save_proxies()

    # Cleanup
    for acc in account_manager.accounts:
        if acc.get('client'):
            try:
                await acc['client'].disconnect()
            except:
                pass

if __name__ == '__main__':
    asyncio.run(main())
