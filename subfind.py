import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from colorama import init, Fore, Style
import threading

init(autoreset=True)

# Constants
API_URL = "https://sub-scan-api.reverseipdomain.com/?domain={domain}"
FILTERED_SUBDOMAINS = [
    'www.', 'webmail.', 'cpanel.', 'cpcalendars.', 'cpcontacts.',
    'webdisk.', 'mail.', 'whm.', 'autodiscover.'
]
MAX_THREADS = 500

# Lock for thread-safe file writing
file_lock = threading.Lock()

def clear_screen():
    """Clear the console screen."""
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def get_subdomains(domain: str, max_retries: int = 3) -> List[str]:
    """
    Retrieve subdomains for a given domain.
    """
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(API_URL.format(domain=domain))
            response.raise_for_status()
            data = response.json()

            if 'result' in data and 'domains' in data['result']:
                return data['result']['domains']
            else:
                print(Fore.YELLOW + f"[!] No subdomains found for {domain}")
                return []
        except requests.exceptions.RequestException as e:
            retries += 1
            print(Fore.RED + f"[!] Error fetching {domain}: {e}. Retrying ({retries}/{max_retries})...")
    return []

def filter_subdomains(subdomains: List[str]) -> List[str]:
    """
    Filter out common subdomains.
    """
    return [subdomain for subdomain in subdomains if not any(subdomain.startswith(f) for f in FILTERED_SUBDOMAINS)]

def process_file(input_file: str, auto_filter: bool, output_file: str, thread_count: int):
    """
    Process domains from the input file.
    """
    clear_screen()
    with open(input_file, 'r') as file:
        domains = [line.strip() for line in file if line.strip()]

    print(Fore.CYAN + f"Scanning {len(domains)} domains from {input_file}...")

    thread_count = min(thread_count, MAX_THREADS)

    with open(output_file, 'w') as outfile:
        def write_subdomains(domain: str):
            subdomains = get_subdomains(domain)
            if subdomains:
                if auto_filter:
                    subdomains = filter_subdomains(subdomains)
                with file_lock:
                    for subdomain in sorted(set(subdomains)):
                        outfile.write(f"{subdomain}\n")
                print(Fore.GREEN + f"{domain} >>> {len(subdomains)} subdomain(s) found")
            else:
                print(Fore.YELLOW + f"{domain} >>> No subdomains found")

        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = {executor.submit(write_subdomains, domain): domain for domain in domains}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(Fore.RED + f"[!] Error processing domain: {e}")

    print(Fore.YELLOW + "Subdomains saved to " + Fore.CYAN + f"{output_file}")

if __name__ == "__main__":
    clear_screen()
    print("""
█▀ █░█ █▄▄ █▀▄ █▀█ █▀▄▀█ ▄▀█ █ █▄░█   █▀▀ █ █▄░█ █▀▄ █▀▀ █▀█
▄█ █▄█ █▄█ █▄▀ █▄█ █░▀░█ █▀█ █ █░▀█   █▀░ █ █░▀█ █▄▀ ██▄ █▀▄        
- Subdomain Finder By @DUCKXSEC
- https://github.com/duckxsec/subdomain-finder
""")
    input_file = input(Fore.CYAN + "$ Enter Your File: ").strip()
    auto_filter = input(Fore.CYAN + "$ Auto filter subdomain [y/n]: ").strip().lower() == 'y'
    output_file = input(Fore.CYAN + "$ Save to: ").strip()
    thread_count = int(input(Fore.CYAN + "Thread: ").strip())

    process_file(input_file, auto_filter, output_file, thread_count)

