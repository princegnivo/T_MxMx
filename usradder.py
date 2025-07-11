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
    print(f'{info}{g} Multi-Account Group Adder V2.2 {rs}')
    print(f'{info}{g} Author: t.me/iCloudMxMx {rs}')
    print(f'{info}{cy} Features: Smart Proxy Rotation | MTProto Support | Premium Detection | Anti-Flood{rs}\n')

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
    
    async def fetch_proxies_from_channel(self, client):
        """Enhanced proxy fetching with robust parsing"""
        try:
            print(f'{info} Fetching fresh proxies from @ProxyMTProto')
            channel = await client.get_entity("https://t.me/ProxyMTProto")
            messages = await client.get_messages(channel, limit=50)
            
            new_proxies = []
            proxy_pattern = re.compile(
                r'(?:Server|Host|IP|Адрес)[:\s]*(.*?)\n'
                r'(?:Port|Порт)[:\s]*([0-9]{1,5}|`[0-9]{1,5}`)\n'
                r'(?:Secret|Ключ|Секрет)[:\s]*(.*?)(?:\n|$)',
                re.IGNORECASE
            )
            
            for msg in messages:
                if msg.text:
                    matches = proxy_pattern.finditer(msg.text)
                    for match in matches:
                        try:
                            port = self.parse_proxy_port(match.group(2))
                            if not port:
                                continue
                                
                            proxy = {
                                'server': match.group(1).strip(),
                                'port': port,
                                'secret': match.group(3).strip()
                            }
                            
                            if all(proxy.values()):  # Ensure no empty values
                                new_proxies.append(proxy)
                        except (ValueError, AttributeError, IndexError) as e:
                            continue
            
            # Remove duplicates
            unique_proxies = []
            seen = set()
            for p in new_proxies:
                key = (p['server'], p['port'])
                if key not in seen:
                    seen.add(key)
                    unique_proxies.append(p)
            
            self.proxies = unique_proxies
            self.last_refresh = datetime.now()
            self.save_proxies()
            print(f'{info} Found {len(self.proxies)} fresh proxies')
            return True
            
        except Exception as e:
            print(f'{error} Failed to fetch proxies: {str(e)}')
            return False
    
    def parse_proxy_port(self, port_str):
        """Safe port number parsing that handles backticks and other formatting"""
        try:
            # Remove all non-numeric characters
            clean_port = re.sub(r'[^0-9]', '', port_str)
            if not clean_port:
                return None
                
            port = int(clean_port)
            return port if 1 <= port <= 65535 else None
        except ValueError:
            return None
    
    def load_proxies(self):
        """Load proxies from JSON file"""
        try:
            with open('proxy_list.json') as f:
                self.proxies = json.load(f)
                self.last_refresh = datetime.now()
                print(f'{info} Loaded {len(self.proxies)} proxies from file')
                return True
        except Exception:
            return False
    
    def save_proxies(self):
        """Save proxies to JSON file"""
        try:
            with open('proxy_list.json', 'w') as f:
                json.dump(self.proxies, f, indent=2)
        except Exception as e:
            print(f'{error} Failed to save proxies: {str(e)}')
    
    async def get_next_proxy(self):
        """Get the next working proxy with intelligent selection"""
        # Rotate if we've used current proxy enough times
        if self.proxy_usage_count >= PROXY_ROTATION_COUNT:
            self.proxy_usage_count = 0
            self.current_proxy = None
        
        # Return current proxy if still valid
        if self.current_proxy and await self.test_proxy(self.current_proxy):
            self.proxy_usage_count += 1
            return self.current_proxy
        
        # Check if we need to refresh proxies
        if (not self.proxies or 
            (datetime.now() - self.last_refresh).total_seconds() > PROXY_REFRESH_INTERVAL * 60):
            if not self.load_proxies():
                return None
        
        # Test random proxies until we find a working one
        tested_proxies = set()
        while len(tested_proxies) < len(self.proxies):
            proxy = random.choice(self.proxies)
            if tuple(proxy.items()) in tested_proxies:
                continue
            tested_proxies.add(tuple(proxy.items()))
            
            if await self.test_proxy(proxy):
                self.current_proxy = proxy
                self.proxy_usage_count = 1
                return proxy
        
        return None
    
    async def test_proxy(self, proxy):
        """Test if proxy is working"""
        try:
            # Test TCP connection first
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(proxy['server'], proxy['port']),
                timeout=PROXY_TEST_TIMEOUT
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

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
            'is_active': True
        })
    
    def get_current_account(self):
        return self.accounts[self.current_index] if self.accounts else None
    
    async def rotate_account(self, reason=""):
        """Rotate to next available account with proper cleanup"""
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
        
        original_index = self.current_index
        for i in range(1, len(self.accounts)):
            next_index = (original_index + i) % len(self.accounts)
            self.current_index = next_index
            self.action_count = 0
            self.flood_errors = 0
            
            if not self.accounts[next_index]['is_active']:
                continue
                
            time.sleep(random.uniform(1, 3))
            
            proxy = await self.proxy_manager.get_next_proxy()
            if await self.setup_client(self.get_current_account(), proxy):
                print(f'{info}{cy} Switched to {self.get_current_account()["phone"]}{rs}')
                return True
        
        print(f'{error} All accounts exhausted or inactive{rs}')
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
                proxy=proxy_config
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
        participants = await client.get_participants(account_manager.target_group)
        participants_count = len(participants)
        print(f'{info}{g} Target: {account_manager.target_group.title} | Members: {participants_count}{rs}')
    except Exception as e:
        print(f'{error} Group error: {str(e)}')
        return

    start_time = datetime.now()
    stats = {'success': 0, 'skip': 0, 'fail': 0, 'invalid': 0}

    for index, user in enumerate(users, 1):
        current_account = account_manager.get_current_account()
        
        # Skip rotation if only one account
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
                    if await account_manager.rotate_account(reason):
                        current_account = account_manager.get_current_account()
                        client = current_account['client']
                        # Revalidate channel after rotation
                        if not await account_manager.validate_channel(client):
                            print(f'{error} Failed to validate channel after rotation!')
                            stats['fail'] += 1
                            continue
                    break
        
        try:
            if not user['username']:
                print(f'{sleep}{ye} Skipping empty username{rs}')
                stats['invalid'] += 1
                continue
                
            client = current_account['client']
            
            # Attempt to get participants with retries
            participants = []
            for attempt_num in range(MAX_RETRIES):
                try:
                    participants = [p.username for p in await client.get_participants(account_manager.target_group) if p.username]
                    break
                except (ChannelInvalidError, ChannelPrivateError) as e:
                    if attempt_num < MAX_RETRIES - 1:
                        print(f'{error} Channel error (attempt {attempt_num + 1}/{MAX_RETRIES}): {str(e)}')
                        time.sleep(5)
                        continue
                    else:
                        print(f'{error} Failed to get participants after {MAX_RETRIES} attempts: {str(e)}')
                        stats['fail'] += 1
                        current_account['errors'] += 1
                        if await account_manager.rotate_account("Channel access failed"):
                            continue
                        else:
                            break
                except Exception as e:
                    print(f'{error} Unexpected error getting participants: {str(e)}')
                    stats['fail'] += 1
                    current_account['errors'] += 1
                    break
            
            if not participants:
                continue
                
            if user['username'] in participants:
                print(f'{sleep}{cy} Skip: {user["username"]} exists{rs}')
                stats['skip'] += 1
                continue
            
            # Random delay with premium adjustment
            delay = random.randint(MIN_DELAY, MAX_DELAY) * (0.7 if current_account['is_premium'] else 1.0)
            print(f'\n{sleep} Delay: {delay:.1f}s | Acc: {current_account["phone"]}')
            countdown_timer(int(delay))
            
            print(f'\n{attempt} Adding {user["username"]} ({index}/{len(users)})')
            try:
                await client(InviteToChannelRequest(
                    account_manager.group_entity, 
                    [await client.get_input_entity(user['username'])]
                ))
                stats['success'] += 1
                account_manager.action_count += 1
                account_manager.successful_adds += 1
                current_account['added_count'] += 1
                print(f'{attempt}{g} Suc
