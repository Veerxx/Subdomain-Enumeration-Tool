#!/bin/bash
# install.sh - Installation script

echo "Installing Subdomain Enumeration Tool..."

# Install Python dependencies
pip3 install -r requirements.txt

# Generate wordlist
python3 generate_wordlist.py

echo "Installation complete!"
echo ""
echo "Usage examples:"
echo "  python3 subenum.py example.com"
echo "  python3 subenum.py example.com -w subdomains.txt -t 100 -o results.json"
echo "  python3 subenum.py example.com -v"
