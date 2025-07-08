import sys
import requests
from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import PhoneNumberBannedError
import pickle
import pyfiglet
from colorama import init, Fore
import os
import random
from time import sleep
from bs4 import BeautifulSoup

# Initialize colorama
init()

# Color definitions
lg = Fore.LIGHTGREEN_EX
w = Fore.WHITE
cy = Fore.CYAN
ye = Fore.YELLOW
r = Fore.RED
n = Fore.RESET
colors = [lg, r, w, cy, ye]

def banner():
    f = pyfiglet.Figlet(font='slant')
    banner = f.renderText('Telegram')
    print(f'{random.choice(colors)}{banner}{n}')
    print(r + '  Version: 2.0 | Author: @iCloudMxMx' + n + '\n')

def clr():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def extract_api_credentials():
    clr()
    banner()
    print(lg + '[+] Automated API Credential Extraction\n' + n)
    
    try:
        phone = input(f"{r}[{lg}+{r}] {lg}Enter your number with country code [Ex: +9812345678]: {r}")
        
        with requests.Session() as req:
            # Send phone number
            login0 = req.post('https://my.telegram.org/auth/send_password', data={'phone': phone})

            if 'Sorry, too many tries. Please try again later.' in login0.text:
                print(f'{r}[!] Your account has been temporarily banned! Try again later.{n}')
                input(f'\n{lg}Press enter to continue...{n}')
                return

            if not login0.json().get('random_hash'):
                print(f'{r}[!] Failed to send code. Check your phone number.{n}')
                input(f'\n{lg}Press enter to continue...{n}')
                return

            random_hash = login0.json()['random_hash']
            
            # Get verification code
            code = input(f'{r}[{lg}+{r}] {lg}Enter the code sent to your Telegram: {r}')
            
            # Login with code
            login_data = {
                'phone': phone,
                'random_hash': random_hash,
                'password': code
            }
            
            login = req.post('https://my.telegram.org/auth/login', data=login_data)
            
            if 'true' not in login.text:
                print(f'{r}[!] Invalid verification code{n}')
                input(f'\n{lg}Press enter to continue...{n}')
                return
            
            # Get apps page
            apps_page = req.get('https://my.telegram.org/apps')
            soup = BeautifulSoup(apps_page.text, 'html.parser')
            
            try:
                # Extract API credentials
                api_id = soup.find('label', string='App api_id:').find_next_sibling('div').select_one('span').get_text()
                api_hash = soup.find('label', string='App api_hash:').find_next_sibling('div').select_one('span').get_text()
                
                # Extract additional info
                try:
                    key = soup.find('label', string='Public keys:').find_next_sibling('div').select_one('code').get_text()
                except:
                    key = "Not found"
                
                try:
                    pc = soup.find('label', string='Production configuration:').find_next_sibling('div').select_one('strong').get_text()
                except:
                    pc = "Not found"
                
                print(f'\n{lg}[+] Successfully extracted credentials:{n}')
                print(f'{lg}├─ API ID: {w}{api_id}{n}')
                print(f'{lg}├─ API Hash: {w}{api_hash}{n}')
                print(f'{lg}├─ Public Key: {w}{key[:20]}...{n}')
                print(f'{lg}└─ Production Config: {w}{pc[:30]}...{n}')
                
                # Save to vars.txt
                save = input(f'\n{lg}Do you want to save these credentials? (y/n): {r}').lower()
                if save == 'y':
                    with open('vars.txt', 'ab') as f:
                        pickle.dump([int(api_id), api_hash, phone], f)
                    print(f'\n{lg}[+] Credentials saved to vars.txt!{n}')
                
            except Exception as e:
                print(f'{r}[!] Failed to extract credentials. You may need to create an app first.{n}')
                print(f'{r}Error: {str(e)}{n}')
                
    except Exception as e:
        print(f'{r}[!] Error: {str(e)}{n}')
    
    input(f'\n{lg}Press enter to continue...{n}')

while True:
    clr()
    banner()
    print(lg + '[1] Add new accounts' + n)
    print(lg + '[2] Extract API credentials automatically' + n)  # Moved to position 2
    print(lg + '[3] Filter all banned accounts' + n)
    print(lg + '[4] List out all the accounts' + n)
    print(lg + '[5] Delete specific accounts' + n)
    print(r + '[6] Exit' + n)
    
    try:
        a = int(input(f'\nEnter your choice: {r}'))
    except ValueError:
        print(r + '[!] Please enter a valid number' + n)
        sleep(2)
        continue

    if a == 1:
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

    elif a == 2:  # Now the API extraction is option 2
        extract_api_credentials()

    elif a == 3:  # Previously option 2, now option 3
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

    elif a == 4:  # Previously option 3, now option 4
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

    elif a == 5:  # Previously option 4, now option 5
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

    elif a == 6:
        print(lg + '\nExiting... Goodbye!' + n)
        sleep(1)
        sys.exit(0)
    else:
        print(r + '[!] Invalid choice! (1-6 only)' + n)
        sleep(2)
