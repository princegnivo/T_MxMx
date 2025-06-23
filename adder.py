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
    print(f'{r}   Version: {w}1.1 {r}| Author: {w}PrinceMxMx{rs}')

def clr():
    os.system('clear')

global scraped_grp
with open('target_grp.txt', 'r') as f:
    scraped_grp = f.readline()
f.close()

clr()
banner()
users = []
input_file = 'members/members.csv'
with open(input_file, 'r', encoding='UTF-8') as f:
    reader = csv.reader(f, delimiter=',', lineterminator='\n')
    next(reader, None)
    for row in reader:
        user = {}
        user['username'] = row[0]
        user['user_id'] = row[1]
        user['access_hash'] = row[2]
        user['group'] = row[3]
        user['group_id'] = row[4]
        users.append(user)

accounts = []
f = open('vars.txt', 'rb')
while True:
    try:
        accounts.append(pickle.load(f))
    except EOFError:
        break
f.close()

print('\n' + info + lg + ' Creating sessions for all accounts...' + rs)
for a in accounts:
    iD = int(a[0])
    Hash = str(a[1])
    phn = str(a[2])
    clnt = TelegramClient(f'sessions/{phn}', iD, Hash)
    clnt.connect()
    banned = []
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
            banned.append(a)
    for z in banned:
        accounts.remove(z)
        print('\n'+info+lg+'Banned account removed'+rs)
    time.sleep(0.5)
    clnt.disconnect()

print(info+' Sessions created!')
time.sleep(2)
print(f'{plus}{lg} Enter the exact username of the public group{w}[Without @]')
g = input(f'{INPUT}{lg} Username[Eg: Techmedies_Hub]: {r}')
group = 't.me/' + str(g)

print(f'{info}{lg} Joining from all accounts...{rs}')
for account in accounts:
    api_id = int(account[0])
    api_hash = str(account[1])
    phone = str(account[2])
    client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
    client.connect()
    try:
        username = client.get_entity(group)
        client(JoinChannelRequest(username))
        print(f'{success}{lg} Joined from {phone}')
    except:
        print(f'{error}{r} Error in joining from {phone}')
        accounts.remove(account)
    client.disconnect()

time.sleep(2)
clr()
number = len(accounts)
print(f'{info}{lg} Total accounts: {w}{number}')
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

# Create alt_accounts.csv with all selected accounts except the first one
if len(selected_accounts) > 1:
    with open('alt_accounts.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['phone', 'api_id', 'api_hash'])
        for acc in selected_accounts[1:]:  # Skip first account (main account)
            writer.writerow([acc[2], acc[0], acc[1]])
    print(f'{success} Created alt_accounts.csv with {len(selected_accounts)-1} backup accounts')
else:
    # Clear alt_accounts.csv if not needed
    open('alt_accounts.csv', 'w').close()

to_use = selected_accounts
print(f'\n{info}{lg} Distributing CSV files...{rs}')
time.sleep(2)

for i in to_use:
    done = []
    file = 'members/members' + str(to_use.index(i)) + '.csv'
    with open(file, 'w', encoding='UTF-8') as f:
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        writer.writerow(['username', 'user id', 'access hash', 'group', 'group id'])
        for user in users[:60]:
            writer.writerow([user['username'], user['user_id'], user['access_hash'], user['group'], user['group_id']])
            done.append(user)
    f.close()
    del_count = 0
    while del_count != len(done):
        del users[0]
        del_count += 1
    if len(users) == 0:
        break

if not len(users) == 0:
    with open('members/members.csv', 'w', encoding='UTF-8') as f:
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        writer.writerow(['username', 'user id', 'access hash', 'group', 'group id'])
        for user in users:
            writer.writerow([user['username'], user['user_id'], user['access_hash'], user['group'], user['group_id']])
    f.close()
    m = str(len(users))
    print(f'{info}{lg} Remaining {m} users stored in {w}members.csv')

for acc in to_use:
    if acc in accounts:
        accounts.remove(acc)

with open('vars.txt', 'wb') as f:
    for acc in accounts:
        pickle.dump(acc, f)
    for k in to_use:
        pickle.dump(k, f)
    f.close()

print(f'{info}{lg} CSV file distribution complete{rs}')
time.sleep(2)
clr()

print(f'\n{info}{r} This will be fully automated.')
print(f'{info}{r} Don\'t touch the device until all processes complete')
input(f'\n{plus}{lg} Press enter to continue...{rs}')
print(f'\n{info}{lg} Launching from {len(to_use)} accounts...{rs}\n')

for i in range(5, 0, -1):
    print(random.choice(colors) + str(i) + rs)
    time.sleep(1)

processes = []
main_account = to_use[0]
api_id = str(main_account[0])
api_hash = str(main_account[1])
phone = str(main_account[2])
file = 'members/members0.csv'

if len(to_use) == 1:
    cmd = ['python', 'usradder.py', api_id, api_hash, phone, file, group, str(scraped_grp)]
else:
    cmd = ['python', 'usradder.py', api_id, api_hash, phone, file, group, str(scraped_grp), 'alt_accounts.csv']

process = subprocess.Popen(cmd)
processes.append(process)
print(f'{plus}{lg} Launched main process from {phone}')

# Wait for all processes to complete
for process in processes:
    process.wait()

print(f'\n{success}{lg} All processes completed!{rs}')
