#!/usr/bin/env python3
"""
Wordlist Generator for Subdomain Enumeration
Author: Veerxx
"""

wordlist = [
    'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1',
    'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'm', 'imap',
    'test', 'ns', 'blog', 'pop3', 'dev', 'www2', 'admin', 'forum', 'news',
    'vpn', 'ns3', 'mail2', 'new', 'mysql', 'old', 'lists', 'support',
    'mobile', 'mx', 'static', 'docs', 'beta', 'shop', 'sql', 'secure',
    'demo', 'cp', 'calendar', 'wiki', 'web', 'media', 'email', 'images',
    'img', 'download', 'dns', 'stats', 'dashboard', 'portal', 'manage',
    'start', 'info', 'apps', 'video', 'sip', 'dns2', 'api', 'cdn', 'mssql',
    'remote', 'server', 'stage', 'staging', 'chat', 'help', 'helpdesk',
    'ssl', 'mail1', 'link', 'site', 'member', 'members', 'office', 'host',
    'hosting', 'cloud', 'direct', 'cms', 'ecommerce', 'billing', 'cert',
    'crl', 'pgp', 'registrar', 'ns4', 'email2', 'live', 'partner',
    'partners', 'training', 'tools', 'service', 'services', 'portal2',
    'oldmail', 'forums', 'community', 'board', 'admin2', 'clients',
    'client', 'user', 'users', 'public', 'private', 'status', 'speedtest',
    'test2', 'jenkins', 'gitlab', 'github', 'bitbucket', 'jira', 'confluence'
]

with open('wordlists/common.txt', 'w') as f:
    for word in sorted(set(wordlist)):
        f.write(f"{word}\n")

print(f"[+] Generated wordlist with {len(set(wordlist))} words")
print("[+] Saved to wordlists/common.txt")
