#!/usr/bin/env python3
"""
Professional Subdomain Enumeration Tool
Author: Veerxx
GitHub: https://github.com/Veerxx/Subdomain-Enumeration-Tool
"""

import argparse
import asyncio
import aiohttp
import dns.resolver
import dns.asyncresolver
import json
import csv
import time
import sys
import signal
from typing import Set, List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re
import random
import colorama
from colorama import Fore, Style
import pyfiglet
import threading

colorama.init()

@dataclass
class SubdomainResult:
    subdomain: str
    ip_addresses: List[str]
    status: str
    response_time: float
    title: str = ""
    server: str = ""
    technologies: List[str] = None
    cname: List[str] = None
    source: str = ""
    timestamp: str = ""

class SubdomainEnumerator:
    def __init__(self, domain: str, threads: int = 50, timeout: int = 5, 
                 verbose: bool = False, output_file: str = None):
        self.domain = domain.lower()
        self.threads = threads
        self.timeout = timeout
        self.verbose = verbose
        self.output_file = output_file
        self.found_subdomains: Set[str] = set()
        self.results: List[SubdomainResult] = []
        self.lock = threading.Lock()
        self.running = True
        self.total_queries = 0
        self.start_time = None
        self.end_time = None
        
        self.resolver = dns.asyncresolver.Resolver()
        self.resolver.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1']
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]

    def print_banner(self):
        try:
            banner = pyfiglet.figlet_format("SubEnum Pro", font="slant")
            print(f"{Fore.CYAN}{banner}{Style.RESET_ALL}")
        except:
            print(f"{Fore.CYAN}=== SubEnum Pro - Subdomain Enumeration Tool ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Target: {self.domain}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'='*60}{Style.RESET_ALL}\n")

    async def dns_query(self, subdomain: str, source: str = "bruteforce") -> Optional[SubdomainResult]:
        fqdn = f"{subdomain}.{self.domain}"
        
        for attempt in range(3):
            try:
                answers = await self.resolver.resolve(fqdn, 'A', raise_on_no_answer=False)
                ip_addresses = [str(r) for r in answers]
                
                if ip_addresses:
                    cname = []
                    try:
                        cname_answers = await self.resolver.resolve(fqdn, 'CNAME')
                        cname = [str(r) for r in cname_answers]
                    except:
                        pass
                    
                    title, server, technologies = await self.get_web_info(fqdn)
                    
                    return SubdomainResult(
                        subdomain=fqdn,
                        ip_addresses=ip_addresses,
                        status="active",
                        response_time=0.1,
                        title=title,
                        server=server,
                        technologies=technologies if technologies else [],
                        cname=cname,
                        source=source,
                        timestamp=datetime.now().isoformat()
                    )
                return None
            except:
                if attempt == 2:
                    return None
                await asyncio.sleep(1)
        return None

    async def get_web_info(self, domain: str) -> tuple:
        title = ""
        server = ""
        technologies = []
        
        for protocol in ['https', 'http']:
            try:
                url = f"{protocol}://{domain}"
                timeout = aiohttp.ClientTimeout(total=5)
                connector = aiohttp.TCPConnector(ssl=False)
                
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.get(url, headers={'User-Agent': random.choice(self.user_agents)}, 
                                         allow_redirects=True, ssl=False) as resp:
                        server = resp.headers.get('Server', '')
                        try:
                            html = await resp.text()
                            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                            if title_match:
                                title = title_match.group(1).strip()[:100]
                        except:
                            pass
                        return title, server, technologies
            except:
                continue
        return title, server, technologies

    async def crtsh_search(self):
        print(f"{Fore.CYAN}[*] Searching crt.sh...{Style.RESET_ALL}")
        url = f"https://crt.sh/?q=%.{self.domain}&output=json"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout, ssl=False) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for entry in data:
                            name = entry.get('name_value', '')
                            if name:
                                for sub in name.split('\n'):
                                    self.extract_subdomains(sub.strip(), "crt.sh")
        except Exception as e:
            if self.verbose:
                print(f"{Fore.YELLOW}[-] crt.sh error{Style.RESET_ALL}")

    async def hackertarget_search(self):
        print(f"{Fore.CYAN}[*] Searching HackerTarget...{Style.RESET_ALL}")
        url = f"https://api.hackertarget.com/hostsearch/?q={self.domain}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout, ssl=False) as resp:
                    if resp.status == 200:
                        data = await resp.text()
                        for line in data.split('\n'):
                            if ',' in line:
                                subdomain = line.split(',')[0].strip()
                                if subdomain:
                                    self.extract_subdomains(subdomain, "hackertarget")
        except:
            pass

    async def alienvault_search(self):
        print(f"{Fore.CYAN}[*] Searching AlienVault...{Style.RESET_ALL}")
        url = f"https://otx.alienvault.com/api/v1/indicators/domain/{self.domain}/passive_dns"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout, ssl=False) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for entry in data.get('passive_dns', []):
                            hostname = entry.get('hostname', '')
                            if hostname:
                                self.extract_subdomains(hostname, "alienvault")
        except:
            pass

    async def rapiddns_search(self):
        print(f"{Fore.CYAN}[*] Searching RapidDNS...{Style.RESET_ALL}")
        url = f"https://rapiddns.io/subdomain/{self.domain}?full=1"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout, ssl=False) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        pattern = r'<td>([a-zA-Z0-9][-a-zA-Z0-9]*\.' + re.escape(self.domain) + r')</td>'
                        matches = re.findall(pattern, html)
                        for match in matches:
                            self.extract_subdomains(match, "rapiddns")
        except:
            pass

    async def bufferover_search(self):
        print(f"{Fore.CYAN}[*] Searching BufferOver...{Style.RESET_ALL}")
        url = f"https://dns.bufferover.run/dns?q=.{self.domain}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout, ssl=False) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get('FDNS_A', []):
                            parts = item.split(',')
                            if len(parts) > 1:
                                self.extract_subdomains(parts[1], "bufferover")
        except:
            pass

    async def sonarsearch_search(self):
        print(f"{Fore.CYAN}[*] Searching SonarSearch...{Style.RESET_ALL}")
        url = f"https://sonar.omnisint.io/subdomains/{self.domain}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout, ssl=False) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list):
                            for subdomain in data:
                                self.extract_subdomains(subdomain, "sonarsearch")
        except:
            pass

    def extract_subdomains(self, text: str, source: str = "unknown"):
        text = text.lower().strip()
        text = re.sub(r'[^\w\.-]', '', text)
        pattern = r'([a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?\.)*' + re.escape(self.domain)
        matches = re.finditer(pattern, text)
        
        for match in matches:
            full_domain = match.group()
            if (full_domain and full_domain != self.domain and full_domain.endswith(self.domain)):
                with self.lock:
                    if full_domain not in self.found_subdomains:
                        self.found_subdomains.add(full_domain)
                        if self.verbose:
                            print(f"{Fore.BLUE}[{source}] Found: {full_domain}{Style.RESET_ALL}")
                        asyncio.create_task(self.verify_subdomain(full_domain, source))

    async def verify_subdomain(self, subdomain: str, source: str):
        try:
            sub_part = subdomain.replace(f".{self.domain}", "")
            result = await self.dns_query(sub_part, source)
            if result:
                with self.lock:
                    if result.subdomain not in [r.subdomain for r in self.results]:
                        self.results.append(result)
                        self.print_result(result)
        except:
            pass

    async def dns_bruteforce(self, wordlist: List[str]):
        print(f"{Fore.CYAN}[*] Starting DNS bruteforce with {len(wordlist)} words...{Style.RESET_ALL}")
        
        variations = []
        for word in wordlist:
            variations.append(word)
            for prefix in ['dev-', 'test-', 'stage-', 'api-']:
                variations.append(f"{prefix}{word}")
            for suffix in ['-dev', '-test', '-stage', '-api']:
                variations.append(f"{word}{suffix}")
        
        variations = list(set(variations))
        semaphore = asyncio.Semaphore(self.threads)
        
        async def check_word(word):
            async with semaphore:
                result = await self.dns_query(word, "bruteforce")
                if result:
                    with self.lock:
                        if result.subdomain not in [r.subdomain for r in self.results]:
                            self.results.append(result)
                            self.print_result(result)
                self.total_queries += 1
        
        batch_size = 50
        for i in range(0, len(variations), batch_size):
            if not self.running:
                break
            batch = variations[i:i+batch_size]
            tasks = [check_word(word) for word in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(0.5)

    def print_result(self, result: SubdomainResult):
        print(f"\n{Fore.GREEN}[+] {result.subdomain} {Style.RESET_ALL}")
        print(f"    {Fore.CYAN}IP: {', '.join(result.ip_addresses)}{Style.RESET_ALL}")
        print(f"    {Fore.MAGENTA}Source: {result.source}{Style.RESET_ALL}")
        if result.title:
            print(f"    {Fore.YELLOW}Title: {result.title}{Style.RESET_ALL}")
        if result.server:
            print(f"    {Fore.BLUE}Server: {result.server}{Style.RESET_ALL}")
        sys.stdout.flush()

    async def run_all_scans(self, wordlist: List[str] = None):
        self.start_time = time.time()
        print(f"{Fore.GREEN}[*] Starting enumeration for {self.domain}{Style.RESET_ALL}\n")
        
        api_tasks = [
            self.crtsh_search(),
            self.hackertarget_search(),
            self.alienvault_search(),
            self.rapiddns_search(),
            self.bufferover_search(),
            self.sonarsearch_search()
        ]
        
        await asyncio.gather(*api_tasks, return_exceptions=True)
        
        if wordlist:
            print(f"\n{Fore.GREEN}[*] Starting DNS bruteforce...{Style.RESET_ALL}")
            await self.dns_bruteforce(wordlist)
        
        self.end_time = time.time()

    def save_results(self):
        if not self.output_file or not self.results:
            return
        
        file_format = self.output_file.split('.')[-1].lower()
        
        try:
            if file_format == 'json':
                with open(self.output_file, 'w') as f:
                    json.dump([asdict(r) for r in self.results], f, indent=2)
            elif file_format == 'csv':
                with open(self.output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Subdomain', 'IP Addresses', 'Source', 'Title', 'Server', 'Timestamp'])
                    for r in self.results:
                        writer.writerow([
                            r.subdomain,
                            ', '.join(r.ip_addresses),
                            r.source,
                            r.title,
                            r.server,
                            r.timestamp
                        ])
            else:
                with open(self.output_file, 'w') as f:
                    for r in sorted(self.results, key=lambda x: x.subdomain):
                        f.write(f"{r.subdomain}\n")
                        f.write(f"  IP: {', '.join(r.ip_addresses)}\n")
                        f.write(f"  Source: {r.source}\n")
                        if r.title:
                            f.write(f"  Title: {r.title}\n")
                        f.write("\n")
            
            print(f"\n{Fore.GREEN}[✓] Results saved to {self.output_file}{Style.RESET_ALL}")
        except:
            pass

    def print_summary(self):
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Enumeration Complete!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Total subdomains found: {len(self.results)}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Total queries: {self.total_queries}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Time taken: {self.end_time - self.start_time:.2f} seconds{Style.RESET_ALL}")
        
        if self.results:
            sources = {}
            for r in self.results:
                sources[r.source] = sources.get(r.source, 0) + 1
            print(f"\n{Fore.YELLOW}Results by source:{Style.RESET_ALL}")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {source}: {count}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def load_wordlist(wordlist_file: str = None) -> List[str]:
    default = [
        'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'ns2',
        'admin', 'blog', 'dev', 'test', 'api', 'secure', 'vpn', 'portal', 'cpanel',
        'whm', 'autodiscover', 'm', 'imap', 'ns', 'pop3', 'www2', 'forum', 'news',
        'ns3', 'mail2', 'new', 'mysql', 'old', 'lists', 'support', 'mobile', 'mx',
        'static', 'docs', 'beta', 'shop', 'sql', 'demo', 'cp', 'calendar', 'wiki',
        'web', 'media', 'email', 'images', 'img', 'download', 'dns', 'stats',
        'dashboard', 'manage', 'start', 'info', 'apps', 'video', 'sip', 'dns2',
        'cdn', 'mssql', 'remote', 'server', 'stage', 'staging', 'chat', 'help',
        'helpdesk', 'ssl', 'mail1', 'link', 'site', 'member', 'members', 'office',
        'host', 'hosting', 'cloud', 'direct', 'cms', 'billing', 'cert', 'crl',
        'live', 'partner', 'partners', 'training', 'tools', 'service', 'services',
        'oldmail', 'forums', 'community', 'board', 'admin2', 'clients', 'client',
        'user', 'users', 'public', 'private', 'status', 'speedtest', 'test2'
    ]
    
    if not wordlist_file:
        return default
    
    try:
        with open(wordlist_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return words if words else default
    except:
        return default

def signal_handler(sig, frame):
    print(f"\n{Fore.YELLOW}[!] Interrupted by user{Style.RESET_ALL}")
    sys.exit(0)

async def main_async():
    parser = argparse.ArgumentParser(description='Subdomain Enumeration Tool')
    parser.add_argument('domain', help='Target domain')
    parser.add_argument('-w', '--wordlist', help='Wordlist file')
    parser.add_argument('-t', '--threads', type=int, default=50, help='Thread count')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout in seconds')
    
    args = parser.parse_args()
    signal.signal(signal.SIGINT, signal_handler)
    
    enumerator = SubdomainEnumerator(
        domain=args.domain,
        threads=args.threads,
        timeout=args.timeout,
        verbose=args.verbose,
        output_file=args.output
    )
    
    enumerator.print_banner()
    wordlist = load_wordlist(args.wordlist)
    print(f"{Fore.GREEN}[*] Loaded {len(wordlist)} words{Style.RESET_ALL}")
    
    await enumerator.run_all_scans(wordlist)
    
    if enumerator.results:
        enumerator.save_results()
        enumerator.print_summary()
    else:
        print(f"\n{Fore.YELLOW}[!] No subdomains found{Style.RESET_ALL}")

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
EOF
