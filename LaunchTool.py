#!/usr/bin/env python3
import os
import sys
import subprocess
import pyfiglet
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Color definitions
r = Fore.RED
g = Fore.GREEN
w = Fore.WHITE
ye = Fore.YELLOW
cy = Fore.CYAN
colors = [r, g, w, ye, cy]

def color_text(text, color):
    return f"{color}{text}{Style.RESET_ALL}"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_logo():
    """Display the Telegram logo"""
    try:
        logo = pyfiglet.Figlet(font='slant').renderText('Telegram')
        print(color_text(logo, g))  # Green logo as requested
    except:
        print(color_text("=== TelegramPremiumTools ===", g))

def run_script(script_name):
    """Launch script and return to menu"""
    try:
        print(color_text(f"\nLaunching {script_name}...", g))
        subprocess.run(['python', script_name], check=True)
    except subprocess.CalledProcessError:
        print(color_text(f"\n{script_name} failed to execute properly", r))
    except Exception as e:
        print(color_text(f"\nError: {e}", r))
    input(color_text("\nPress Enter to return to menu...", cy))
    clear_screen()

def main_menu():
    """Main menu interface"""
    while True:
        clear_screen()
        show_logo()
        print(color_text("  Version: 2.0 | Author: PrinceMxMx\n", w))
        
        print(color_text("[1] Account Manager", ye))
        print(color_text("[2] Member Scraper", ye))
        print(color_text("[3] Contact Adder", ye))
        print(color_text("[4] Exit", r))
        
        choice = input(color_text("\nSelect option [1-4]: ", cy)).strip()
        
        if choice == '1':
            run_script("manager.py")
        elif choice == '2':
            run_script("scraper.py")
        elif choice == '3':
            print(color_text("\nLaunching Contact Adder...", g))
            subprocess.run(['python', 'adder.py'], check=True)
            sys.exit(0)
        elif choice == '4':
            print(color_text("\nExiting Telegram Tools...", r))
            sys.exit(0)
        else:
            print(color_text("\nInvalid selection!", r))
            input(color_text("Press Enter to continue...", cy))
            clear_screen()

if __name__ == "__main__":
    try:
        # Create required directories
        os.makedirs("members", exist_ok=True)
        clear_screen()
        main_menu()
    except KeyboardInterrupt:
        print(color_text("\nScript interrupted by user", r))
        sys.exit(1)
    except Exception as e:
        print(color_text(f"\nFatal error: {e}", r))
        sys.exit(1)
