import os
import time
import random
import sys
import pyfiglet
import subprocess
import json
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Configuration
CONFIG_FILE = "proxy_list.json"

# Color definitions
r = Fore.RED
g = Fore.GREEN
b = Fore.BLUE
y = Fore.YELLOW
m = Fore.MAGENTA
c = Fore.CYAN
w = Fore.WHITE
lg = Fore.LIGHTGREEN_EX
ly = Fore.LIGHTYELLOW_EX
lm = Fore.LIGHTMAGENTA_EX
lc = Fore.LIGHTCYAN_EX
lr = Fore.LIGHTRED_EX
lb = Fore.LIGHTBLUE_EX
rs = Style.RESET_ALL

# Rainbow colors
rainbow = [r, g, b, y, m, c, lg, ly, lm, lc, lr, lb]

# UI elements
info = lg + '(' + w + 'i' + lg + ')' + rs
error = lg + '(' + r + '!' + lg + ')' + rs
success = w + '(' + lg + '+' + w + ')' + rs
INPUT = lg + '(' + c + '~' + lg + ')' + rs

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def run_script(script_name):
    try:
        subprocess.run(['python', script_name], check=True)
    except Exception as e:
        print(f"{error} {lr}Error launching {script_name}: {str(e)}{rs}")
        time.sleep(2)

def animate_text(text, delay=0.05):
    for char in text:
        color = random.choice(rainbow)
        sys.stdout.write(color + char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def loading_animation(duration=2):
    symbols = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    end_time = time.time() + duration
    while time.time() < end_time:
        for symbol in symbols:
            color = random.choice(rainbow)
            sys.stdout.write(f"\r{color}Loading {symbol} {rs}")
            sys.stdout.flush()
            time.sleep(0.1)
    print()

def banner():
    f = pyfiglet.Figlet(font='slant')
    logo = f.renderText('Telegram')
    
    colored_logo = []
    for i, line in enumerate(logo.split('\n')):
        color = rainbow[i % len(rainbow)]
        colored_logo.append(color + line)
    print('\n'.join(colored_logo))
    
    print(f'  {r}Version: {w}2.0 {r}| Author: {w}PrinceMxMx{rs}')
    print(f'  {r}Build: {w}Premium {r}| Status: {lg}Stable{rs}\n')

def welcome_message():
    messages = [
        f"{lg}Welcome to {ly}Telegram Premium Tools{rs}",
        f"{lc}Professional-grade automation suite{rs}",
        f"{lb}Secure • Private • Efficient{rs}"
    ]
    
    for msg in messages:
        print(msg)
        time.sleep(0.7)

def show_settings():
    print(f"\n{lg}⚙️ CURRENT SETTINGS{rs}")
    print(f"{lg}• Theme: {w}Dark Mode")
    print(f"{lg}• Proxy: {w}System Default")
    print(f"{lg}• Logging: {w}Enabled\n")

def main_menu():
    while True:
        clear_screen()
        banner()
        print(lg+'[1] Account Manager')
        print(lg+'[2] Member Scraper')
        print(lg+'[3] Contact Adder')
        print(lg+'[4] Settings')
        print(lg+'[5] Exit')
        
        choice = input(f"\n{INPUT} {lc}Select option [1-5]: {rs}")
        
        if choice == '1':
            print(f"\n{success} Launching Account Manager...{rs}")
            time.sleep(1)
            run_script("manager.py")
        elif choice == '2':
            print(f"\n{success} Launching Member Scraper...{rs}")
            time.sleep(1)
            run_script("scraper.py")
        elif choice == '3':
            print(f"\n{success} Launching Contact Adder...{rs}")
            time.sleep(1)
            run_script("adder.py")
        elif choice == '4':
            show_settings()
            input(f"{INPUT} {lc}Press Enter to continue...{rs}")
        elif choice == '5':
            print(f"\n{info} {ly}Closing Telegram Premium Tools...{rs}")
            time.sleep(1)
            clear_screen()
            sys.exit(0)
        else:
            print(f"\n{error} Invalid selection!{rs}")
            time.sleep(1)

def main():
    loading_animation()
    clear_screen()
    banner()
    welcome_message()
    
    print(f"\n{info} {ly}Initializing components...{rs}")
    print(f"{success} {lg}Core systems ready{rs}")
    print(f"{info} {lc}Python {sys.version.split()[0]} detected{rs}")
    
    input(f"\n{INPUT} {lc}Press Enter to continue...{rs}")
    
    print(f"\n{lg}Loading premium modules{rs}", end='')
    for _ in range(3):
        print(f"{random.choice(rainbow)}✦{rs}", end='', flush=True)
        time.sleep(0.3)
    
    print(f"\n\n{ly}Initialization complete!{rs}\n")
    time.sleep(1)
    
    main_menu()

if __name__ == "__main__":
    main()
