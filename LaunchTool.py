#!/usr/bin/env python3
import os
import time
import random
import sys
import subprocess
import threading
import pyfiglet
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# ===== COLOR DEFINITIONS =====
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

# Rainbow colors for animations
rainbow = [r, g, b, y, m, c, lg, ly, lm, lc, lr, lb]

# ===== UI ELEMENTS =====
info = lg + '(' + w + 'i' + lg + ')' + rs
error = lg + '(' + r + '!' + lg + ')' + rs
success = w + '(' + lg + '+' + w + ')' + rs
INPUT = lg + '(' + c + '~' + lg + ')' + rs

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def run_script(script_name):
    """Launch script directly and exit"""
    try:
        print(f"\n{success} Launching {script_name}...{rs}")
        subprocess.run(['python', script_name], check=True)
        sys.exit(0)  # Exit after completion
    except subprocess.CalledProcessError as e:
        print(f"{error} {script_name} failed with exit code {e.returncode}{rs}")
        sys.exit(1)
    except Exception as e:
        print(f"{error} Failed to launch {script_name}: {e}{rs}")
        sys.exit(1)

def animate_text(text, delay=0.05):
    """Animated text display with rainbow colors"""
    for char in text:
        color = random.choice(rainbow)
        sys.stdout.write(color + char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def loading_animation(duration=2):
    """Loading spinner animation"""
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
    """Display ASCII art banner"""
    try:
        f = pyfiglet.Figlet(font='slant')
        logo = f.renderText('Telegram')
        
        colored_logo = []
        for i, line in enumerate(logo.split('\n')):
            color = rainbow[i % len(rainbow)]
            colored_logo.append(color + line)
        print('\n'.join(colored_logo))
    except:
        print(f"{lg}=== Telegram Tools ==={rs}")
    
    print(f"  {r}Version: {w}2.0 {r}| Author: {w}@iCloudMxMx{rs}")
    print(f"  {r}Build: {w}Premium {r}| Status: {lg}Stable{rs}\n")

def welcome_message():
    """Display welcome sequence"""
    messages = [
        f"{lg}Welcome to Telegram Premium Tools{rs}",
        f"{lc}Professional automation suite{rs}",
        f"{lb}Secure • Private • Efficient{rs}"
    ]
    
    for msg in messages:
        print(msg)
        time.sleep(0.7)

def main_menu():
    """Main menu interface"""
    while True:
        clear_screen()
        banner()
        
        print(f"{lg}[1] Account Manager")
        print(f"{lg}[2] Member Scraper")
        print(f"{lg}[3] Contact Adder")
        print(f"{lg}[4] Settings")
        print(f"{lg}[5] Exit{rs}")
        
        choice = input(f"\n{INPUT} Select option [1-5]: {rs}").strip()
        
        if choice == '1':
            run_script("manager.py")
        elif choice == '2':
            run_script("scraper.py")
        elif choice == '3':
            run_script("adder.py")
        elif choice == '4':
            print(f"\n{info} Settings panel would appear here")
            input(f"{INPUT} Press Enter to continue...{rs}")
        elif choice == '5':
            print(f"\n{info} {ly}Thank you for using Telegram Premium Tools!{rs}")
            time.sleep(1)
            sys.exit(0)
        else:
            print(f"\n{error} Invalid selection!{rs}")
            time.sleep(1)

def main():
    """Main application entry point"""
    loading_animation()
    clear_screen()
    banner()
    welcome_message()
    
    print(f"\n{info} {ly}Initializing components...{rs}")
    print(f"{success} {lg}Core systems ready{rs}")
    print(f"{info} Python {sys.version.split()[0]} detected{rs}")
    
    input(f"\n{INPUT} Press Enter to continue...{rs}")
    
    print(f"\n{lg}Loading modules{rs}", end='')
    for _ in range(3):
        print(f"{random.choice(rainbow)}✦{rs}", end='', flush=True)
        time.sleep(0.3)
    
    print(f"\n\n{ly}Initialization complete!{rs}\n")
    time.sleep(1)
    
    main_menu()

if __name__ == "__main__":
    try:
        # Create required directories
        os.makedirs("members", exist_ok=True)
        
        main()
    except KeyboardInterrupt:
        print(f"\n{error} Script interrupted by user{rs}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{error} Fatal error: {e}{rs}")
        sys.exit(1)
