from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, PhoneNumberBannedError
from telethon.tl.functions.channels import InviteToChannelRequest
import sys
from telethon.tl.functions.channels import JoinChannelRequest
import csv
import time
import random
import pyfiglet
from colorama import init, Fore
import os
import pickle
import traceback
import subprocess

init()

# Color definitions and banner function remain the same
r = Fore.RED
lg = Fore.GREEN
rs = Fore.RESET
w = Fore.WHITE
cy = Fore.CYAN
ye = Fore.YELLOW
colors = [r, lg, w, ye, cy]
info = lg + '(' + w + 'i' + lg + ')' + rs
error = lg + '(' + r + '!' + lg + ')' + rs
success = w + '(' + lg + '*' + w + ')' + rs
INPUT = lg + '(' + cy + '~' + lg + ')' + rs
plus = lg + '(' + w + '+' + lg + ')' + rs

def banner():
    f = pyfiglet.Figlet(font='slant')
    logo = f.renderText('Telegram')
    print(random.choice(colors) + logo + rs)
    print(f'{r}   Version: {w}2.0 {r}| Author: {w}PrinceMxMx{rs}')

def clr():
    os.system('clear')

# Load target group
global scraped_grp
with open('target_grp.txt', 'r') as f:
    scraped_grp = f.readline().strip()
f.close()

clr()
banner()

# Load members
users = []
input_file = 'members/members.csv'
with open(input_file, 'r', encoding='UTF-8') as f:
    reader = csv.reader(f, delimiter=',', lineterminator='\n')
    next(reader, None)
    for row in reader:
        user = {
            'username': row[0],
            'user_id': row[1],
            'access_hash': row[2],
            'group': row[3],
            'group_id': row[4]
        }
        users.append(user)

# Load accounts
accounts = []
with open('vars.txt', 'rb') as f:
    while True:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            break

# Session creation
print('\n' + info + lg + ' Creating sessions for all accounts...' + rs)
for a in accounts[:]:  # Use slice copy to safely remove during iteration
    iD, Hash, phn = int(a[0]), str(a[1]), str(a[2])
    clnt = TelegramClient(f'sessions/{phn}', iD, Hash)
    clnt.connect()
    
    if not clnt.is_user_authorized():
        try:
            clnt.send_code_request(phn)
            code = input(f'{INPUT}{lg} Enter code for {w}{phn}{cy}[s to skip]:{r}')
            if 's' in code:
                accounts.remove(a)
            else:
                clnt.sign_in(phn, code)
        except PhoneNumberBannedError:
            print(f'{error}{w}{phn} {r}is banned!{rs}')
            accounts.remove(a)
    
    clnt.disconnect()
    time.sleep(0.5)

print(info + ' Sessions created!')
time.sleep(2)

# Group joining
print(f'{plus}{lg} Enter the exact username of the public group{w}[Without @]')
g = input(f'{INPUT}{lg} Username[Eg: iunlock1]: {r}')
group = str(g)  # Removed 't.me/' prefix as per your requested format

print(f'{info}{lg} Joining from all accounts...{rs}')
for account in accounts[:]:  # Safe iteration with copy
    api_id, api_hash, phone = int(account[0]), str(account[1]), str(account[2])
    client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
    client.connect()
    try:
        client(JoinChannelRequest(group))
        print(f'{success}{lg} Joined from {phone}')
    except Exception as e:
        print(f'{error}{r} Error joining from {phone}: {str(e)}')
        accounts.remove(account)
    client.disconnect()

# Account selection
time.sleep(2)
clr()
print(f'{info}{lg} Total accounts: {w}{len(accounts)}')
print(f'{info}{lg} Available accounts:')
for i, acc in enumerate(accounts, 1):
    print(f'{w}[{i}] {cy}Phone: {w}{acc[2]} {cy}API ID: {w}{acc[0]}')

print(f'\n{info}{lg} If you have more than 10 accounts then it is recommended to use 10 at a time')
a = int(input(f'{plus}{lg} Enter number of accounts to use: {r}'))

selected_accounts = []
if a == 1:
    acc_num = int(input(f'{plus}{lg} Enter account number to use: {r}')) - 1
    if 0 <= acc_num < len(accounts):
        selected_accounts.append(accounts[acc_num])
    else:
        print(f'{error} Invalid account number!')
        sys.exit(1)
else:
    print(f'{plus}{lg} Enter account numbers separated by space (e.g., 1 3 5): {r}')
    acc_nums = list(map(int, input().split()))
    for num in acc_nums:
        if 1 <= num <= len(accounts):
            selected_accounts.append(accounts[num-1])
        else:
            print(f'{error} Invalid account number {num}, skipping')

# CSV distribution
print(f'\n{info}{lg} Distributing CSV files...{rs}')
time.sleep(2)

for i, acc in enumerate(selected_accounts):
    output_file = f'members/members{i}.csv'
    with open(output_file, 'w', encoding='UTF-8') as f:
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        writer.writerow(['username', 'user id', 'access hash', 'group', 'group id'])
        for user in users[:60]:  # Take 60 users per account
            writer.writerow([user['username'], user['user_id'], user['access_hash'], user['group'], user['group_id']])
            users.remove(user)  # Remove assigned users
        print(f'{success} Created {output_file} with 60 users')

# Save remaining users
if users:
    with open('members/members.csv', 'w', encoding='UTF-8') as f:
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        writer.writerow(['username', 'user id', 'access hash', 'group', 'group id'])
        writer.writerows([[u['username'], u['user_id'], u['access_hash'], u['group'], u['group_id']] for u in users])
    print(f'{info}{lg} Remaining {len(users)} users stored in members.csv')

# Update vars.txt
with open('vars.txt', 'wb') as f:
    remaining_accounts = [acc for acc in accounts if acc not in selected_accounts]
    for acc in remaining_accounts + selected_accounts:  # Put unused accounts first
        pickle.dump(acc, f)

print(f'{info}{lg} CSV file distribution complete{rs}')
time.sleep(2)
clr()

# Launch usradder.py
print(f'\n{info}{w} 🤖 This will be fully automated.')
print(f'{info}{cy} ☕ Sit back, cup of coffee in hand, and let the magic happen effortlessly.')
input(f'\n{plus}{lg} Press enter to continue...{rs}')
print(f'\n{info}{lg} Launching from {len(selected_accounts)} accounts...{rs}\n')

for i in range(5, 0, -1):
    print(random.choice(colors) + str(i) + rs)
    time.sleep(1)

# Build command according to requested format:
# python usradder.py api_id1 api_hash1 phone1 api_id2 api_hash2 phone2 csv_file group_link
cmd = ['python', 'usradder.py']
for acc in selected_accounts:
    cmd.extend([str(acc[0]), str(acc[1]), str(acc[2])])  # api_id, api_hash, phone

# Add CSV file and group link
cmd.extend(['members/members0.csv', group])

print(f'{plus}{lg} Executing: {" ".join(cmd)}')
process = subprocess.Popen(cmd)
process.wait()

print(f'\n{success}{lg} Process completed!{rs}')
