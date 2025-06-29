import sys  # Add this import at the top
import requests
from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import PhoneNumberBannedError
import pickle
import pyfiglet
from colorama import init, Fore
import os
import random
from time import sleep
import subprocess

# Initialize colorama
init()

# Color definitions
lg = Fore.LIGHTGREEN_EX
w = Fore.WHITE
cy = Fore.CYAN
ye = Fore.YELLOW
r = Fore.RED
n = Fore.RESET
flashing_blue = Fore.BLUE + '\033[5m'  # Flashing blue color
colors = [lg, r, w, cy, ye]

def banner():
    f = pyfiglet.Figlet(font='slant')
    banner = f.renderText('Telegram')
    print(f'{random.choice(colors)}{banner}{n}')
    print(r + '  Version: 2.0 | Author: PrinceMxMx' + n + '\n')

def clr():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def launch_scraper():
    print(f'{lg}Launching scraper...{n}')
    try:
        subprocess.run([sys.executable, 'scraper.py'])  # Launch the scraper.py script
    except Exception as e:
        print(f'{r}[!] Error launching scraper: {str(e)}{n}')
    input(f'\n{lg}Press enter to return to main menu...{n}')

while True:
    clr()
    banner()
    print(lg + '[1] Add new accounts' + n)
    print(lg + '[2] Filter all banned accounts' + n)
    print(lg + '[3] List out all the accounts' + n)
    print(lg + '[4] Delete specific accounts' + n)
    print(flashing_blue + '[5] Launch scraper' + n)
    
    try:
        a = int(input(f'\nEnter your choice: {r}'))
    except ValueError:
        print(r + '[!] Please enter a valid number' + n)
        sleep(2)
        continue

    if a == 1:
        # [Previous implementation for option 1]
        with open('vars.txt', 'ab') as g:
            newly_added = []
            while True:
                try:
                    a = int(input(f'\n{lg}Enter API ID: {r}'))
                    b = input(f'{lg}Enter API Hash: {r}')
                    c = input(f'{lg}Enter Phone Number: {r}')
                    p = ''.join(c.split())
                    pickle.dump([a, b, p], g)
                    newly_added.append([a, b, p])
                    ab = input(f'\nDo you want to add more accounts?[y/n]: ').lower()
                    if ab != 'y':
                        g.close()
                        clr()
                        print(lg + '[*] Logging in new accounts...\n')
                        for added in newly_added:
                            try:
                                client = TelegramClient(f'sessions/{added[2]}', added[0], added[1])
                                client.start()
                                print(f'{lg}[+] Logged in - {added[2]}')
                                client.disconnect()
                            except Exception as e:
                                print(f'{r}[!] Error with {added[2]}: {str(e)}')
                        input(f'\n{lg}Press enter to continue...')
                        break
                except Exception as e:
                    print(f'{r}[!] Error: {str(e)}')

    elif a == 2:
        # [Previous implementation for option 2]
        accounts = []
        banned_accs = []
        try:
            with open('vars.txt', 'rb') as h:
                while True:
                    try:
                        accounts.append(pickle.load(h))
                    except EOFError:
                        break
            
            if not accounts:
                print(r + '[!] No accounts found!' + n)
                sleep(2)
                continue
                
            for account in accounts:
                try:
                    client = TelegramClient(f'sessions/{account[2]}', account[0], account[1])
                    client.connect()
                    if not client.is_user_authorized():
                        try:
                            client.send_code_request(account[2])
                            code = input(f'{lg}Enter code for {account[2]}: {r}')
                            client.sign_in(account[2], code)
                        except PhoneNumberBannedError:
                            print(r + f'{account[2]} is banned!' + n)
                            banned_accs.append(account)
                    client.disconnect()
                except Exception as e:
                    print(f'{r}Error checking {account[2]}: {str(e)}')
                    continue
            
            if not banned_accs:
                print(lg + 'No banned accounts found!' + n)
            else:
                accounts = [acc for acc in accounts if acc not in banned_accs]
                with open('vars.txt', 'wb') as f:
                    for acc in accounts:
                        pickle.dump(acc, f)
                print(lg + f'Removed {len(banned_accs)} banned accounts' + n)
                
            input(f'\n{lg}Press enter to continue...')
        except Exception as e:
            print(f'{r}[!] Error: {str(e)}')
            sleep(2)

    elif a == 3:
        # [Previous implementation for option 3]
        try:
            with open('vars.txt', 'rb') as f:
                accounts = []
                while True:
                    try:
                        accounts.append(pickle.load(f))
                    except EOFError:
                        break
                
                if not accounts:
                    print(r + '[!] No accounts found!' + n)
                else:
                    print(f'\n{lg}│{"ID":^8}│{"API Hash":^32}│{"Phone":^15}│{n}')
                    print(lg + '├' + '─'*8 + '┼' + '─'*32 + '┼' + '─'*15 + '┤' + n)
                    for acc in accounts:
                        print(f'{lg}│{str(acc[0]):^8}│{acc[1]:^32}│{acc[2]:^15}│{n}')
                    print(lg + '└' + '─'*8 + '┴' + '─'*32 + '┴' + '─'*15 + '┘' + n)
                    
                input(f'\n{lg}Press enter to continue...')
        except Exception as e:
            print(f'{r}[!] Error: {str(e)}')
            sleep(2)

    elif a == 4:
        # [Previous implementation for option 4]
        try:
            with open('vars.txt', 'rb') as f:
                accounts = []
                while True:
                    try:
                        accounts.append(pickle.load(f))
                    except EOFError:
                        break
                
                if not accounts:
                    print(r + '[!] No accounts to delete!' + n)
                    sleep(2)
                    continue
                    
                print(f'\n{lg}Select account to delete:{n}')
                for i, acc in enumerate(accounts):
                    print(f'{lg}[{i}] {acc[2]}{n}')
                    
                try:
                    choice = int(input(f'\n{lg}Enter choice (0-{len(accounts)-1}): {r}'))
                    if 0 <= choice < len(accounts):
                        phone = accounts[choice][2]
                        session_file = f'sessions/{phone}.session'
                        if os.path.exists(session_file):
                            os.remove(session_file)
                        del accounts[choice]
                        
                        with open('vars.txt', 'wb') as f:
                            for acc in accounts:
                                pickle.dump(acc, f)
                        print(f'\n{lg}Account deleted successfully!{n}')
                    else:
                        print(r + 'Invalid selection!' + n)
                except ValueError:
                    print(r + 'Please enter a valid number!' + n)
                    
                input(f'\n{lg}Press enter to continue...')
        except Exception as e:
            print(f'{r}[!] Error: {str(e)}')
            sleep(2)

    elif a == 5:
        launch_scraper()
    else:
        print(r + '[!] Invalid choice! (1-5 only)' + n)
        sleep(2)
