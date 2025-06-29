from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import PhoneNumberBannedError
import csv
import sys
import pickle
import random
import pyfiglet
import os
import datetime
from colorama import init, Fore, Style
from telethon.tl.types import UserStatusRecently, ChannelParticipantsAdmins, UserStatusLastMonth, UserStatusLastWeek, UserStatusOffline, UserStatusOnline
from time import sleep
from telethon.tl.functions.channels import GetFullChannelRequest
import subprocess

# Initialize colorama
init()

# Color definitions
lg = Fore.LIGHTGREEN_EX
rs = Fore.RESET
r = Fore.RED
w = Fore.WHITE
cy = Fore.CYAN
g = Fore.GREEN
b = Fore.BLUE

# Current date setup
today = datetime.datetime.now()
yesterday = today - datetime.timedelta(days=1)

# UI elements
info = lg + '(' + w + 'i' + lg + ')' + rs
error = lg + '(' + r + '!' + lg + ')' + rs
success = w + '(' + lg + '+' + w + ')' + rs
INPUT = lg + '(' + cy + '~' + lg + ')' + rs
colors = [lg, w, r, cy, g, b]

def banner():
    f = pyfiglet.Figlet(font='slant')
    logo = f.renderText('Telegram')
    print(random.choice(colors) + logo + rs)

def clear_screen():
    os.system('clear')

clear_screen()
banner()
print(f'  {r}Version: {w}2.0 {r}| Author: {w}PrinceMxMx{rs}\n')

# Check and create necessary directories
os.makedirs('sessions', exist_ok=True)
os.makedirs('members', exist_ok=True)

# Load accounts from vars.txt
try:
    with open('vars.txt', 'rb') as f:
        accs = []
        while True:
            try:
                accs.append(pickle.load(f))
            except EOFError:
                break
except FileNotFoundError:
    print(f"{error} 'vars.txt' not found! Please create it first with your account details.")
    sys.exit()

if not accs:
    print(f"{error} No accounts found in vars.txt!")
    sys.exit()

# Account selection
print(f'{INPUT}{cy} Choose an account to scrape members\n')
for i, acc in enumerate(accs):
    print(f'{lg}({w}{i}{lg}) {acc[2]}')

try:
    ind = int(input(f'\n{INPUT}{cy} Enter choice: '))
    if ind < 0 or ind >= len(accs):
        raise ValueError
    api_id, api_hash, phone = accs[ind]
except (ValueError, IndexError):
    print(f'{error} Invalid selection!')
    sys.exit()

# Group input
group_name = input(f"Enter the name of the group without the @: {r}")

# Initialize Telegram client
client = TelegramClient(f'sessions/{phone}', api_id, api_hash)

try:
    client.connect()
    if not client.is_user_authorized():
        try:
            client.send_code_request(phone)
            code = input(f'{INPUT}{lg} Enter the login code for {w}{phone}{r}: ')
            client.sign_in(phone, code)
        except PhoneNumberBannedError:
            print(f'{error}{w}{phone}{r} is banned!{rs}')
            sys.exit()
except Exception as e:
    print(f'{error} Connection error: {str(e)}')
    sys.exit()

# Get group entity
try:
    group = client.get_entity(group_name)
except Exception as e:
    print(f'{error} Could not find group: {str(e)}')
    sys.exit()

target_grp = "t.me/" + group_name

# Scraping options menu
print(f"\n{lg}How would you like to obtain the users?\n")
print(f"{r}[{cy}0{r}]{lg} All users")
print(f"{r}[{cy}1{r}]{lg} Active Users (online today and yesterday)")
print(f"{r}[{cy}2{r}]{lg} Users active in the last week")
print(f"{r}[{cy}3{r}]{lg} Users active in the last month")
print(f"{r}[{cy}4{r}]{lg} Non-active users (not active in the last month)")

try:
    choice = int(input("\nYour choice: "))
    if choice not in [0, 1, 2, 3, 4]:
        raise ValueError
except ValueError:
    print(f'{error} Invalid choice!')
    sys.exit()

# Get group info
try:
    channel_full_info = client(GetFullChannelRequest(group))
    participants_count = channel_full_info.full_chat.participants_count
except Exception as e:
    print(f'{error} Error getting group info: {str(e)}')
    sys.exit()

def write_user(writer, group, member):
    username = member.username if member.username else ''
    if isinstance(member.status, UserStatusOffline):
        writer.writerow([username, member.id, member.access_hash, group.title, group.id, member.status.was_online])
    else:
        writer.writerow([username, member.id, member.access_hash, group.title, group.id, type(member.status).__name__])

# Admin collection
admin_choice = input(f"{lg}Would you like to have admins on a separate CSV file? {rs}[y/n] {lg}").lower()
if admin_choice == "y":
    try:
        with open("members/admins.csv", "w", encoding='UTF-8') as f:
            writer = csv.writer(f, delimiter=",", lineterminator="\n")
            writer.writerow(['username', 'user id', 'access hash', 'group', 'group id', 'status'])
            admins = client.iter_participants(group, filter=ChannelParticipantsAdmins)
            for admin in admins:
                if not admin.bot:
                    write_user(writer, group, admin)
        print(f"{success} Admins saved to members/admins.csv")
    except Exception as e:
        print(f"{error} Error saving admins: {str(e)}")

# Main member collection
print(f"\n{lg}Starting member collection...{rs}")
try:
    with open("members/members.csv", "w", encoding='UTF-8') as f:
        writer = csv.writer(f, delimiter=",", lineterminator="\n")
        writer.writerow(['username', 'user id', 'access hash', 'group', 'group id', 'status'])
        
        members = client.iter_participants(group, aggressive=True)
        
        if choice == 0:  # All users
            for i, member in enumerate(members):
                print(f"Processing {i+1}/{participants_count}", end="\r")
                if i % 100 == 0:
                    sleep(3)
                if not member.bot:
                    write_user(writer, group, member)
                    
        elif choice == 1:  # Active (today/yesterday)
            for i, member in enumerate(members):
                print(f"Processing {i+1}/{participants_count}", end="\r")
                if i % 100 == 0:
                    sleep(3)
                if not member.bot:
                    if isinstance(member.status, (UserStatusRecently, UserStatusOnline)):
                        write_user(writer, group, member)
                    elif isinstance(member.status, UserStatusOffline):
                        d = member.status.was_online                    
                        if (d.date() == today.date()) or (d.date() == yesterday.date()):
                            write_user(writer, group, member)
                            
        elif choice == 2:  # Last week
            for i, member in enumerate(members):
                print(f"Processing {i+1}/{participants_count}", end="\r")
                if i % 100 == 0:
                    sleep(3)
                if not member.bot:
                    if isinstance(member.status, (UserStatusRecently, UserStatusOnline, UserStatusLastWeek)):
                        write_user(writer, group, member)
                    elif isinstance(member.status, UserStatusOffline):
                        d = member.status.was_online
                        if (today.date() - d.date()).days <= 7:
                            write_user(writer, group, member)
                            
        elif choice == 3:  # Last month
            for i, member in enumerate(members):
                print(f"Processing {i+1}/{participants_count}", end="\r")
                if i % 100 == 0:
                    sleep(3)
                if not member.bot:
                    if isinstance(member.status, (UserStatusRecently, UserStatusOnline, UserStatusLastWeek, UserStatusLastMonth)):
                        write_user(writer, group, member)
                    elif isinstance(member.status, UserStatusOffline):
                        d = member.status.was_online
                        if (today.date() - d.date()).days <= 30:
                            write_user(writer, group, member)
                            
        elif choice == 4:  # Non-active
            all_users = []
            active_users = []
            for i, member in enumerate(members):
                print(f"Processing {i+1}/{participants_count}", end="\r")
                all_users.append(member)
                if i % 100 == 0:
                    sleep(3)
                if not member.bot:
                    if isinstance(member.status, (UserStatusRecently, UserStatusOnline, UserStatusLastWeek, UserStatusLastMonth)):
                        active_users.append(member)
                    elif isinstance(member.status, UserStatusOffline):
                        d = member.status.was_online
                        if (today.date() - d.date()).days <= 30:
                            active_users.append(member)
            for member in all_users:
                if member not in active_users and not member.bot:
                    write_user(writer, group, member)
                    
except Exception as e:
    print(f"\n{r}Error during collection: {str(e)}{rs}")
    print(f"{r}Partial data may have been saved.{rs}")

# Save target group info
with open('target_grp.txt', 'w') as f:
    f.write(target_grp)

# Final output
clear_screen()
banner()
print(f"\n{success} Data collection complete!")
print(f"{info} Members saved to: members/members.csv")
if admin_choice == "y":
    print(f"{info} Admins saved to: members/admins.csv")
print(f"\n{lg}To transfer files from Termux:{rs}")
print(f"{cy}1.{lg} termux-setup-storage (to access shared storage)")
print(f"{cy}2.{lg} cp members/*.csv /sdcard/ (copy to internal storage)")
print(f"{cy}3.{lg} Or use SCP to transfer over network")

# Launch adder.py instead of exiting
subprocess.run(["python", "adder.py"])
                        
