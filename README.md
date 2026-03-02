
# 🔍 Subdomain Enumeration Tool

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A powerful subdomain enumeration tool that combines multiple techniques for comprehensive domain reconnaissance.

## ✨ Features

- 🚀 Multiple data sources (crt.sh, HackerTarget, AlienVault, etc.)
- ⚡ Fast asynchronous operations
- 🔍 Real-time DNS verification
- 📊 Multiple output formats (JSON, CSV, TXT)
- 🎨 Beautiful colored output

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/Veerxx/Subdomain-Enumeration-Tool.git
cd Subdomain-Enumeration-Tool
pip install -r requirements.txt
python3 generate_wordlist.py

# Basic usage
python3 subdomain_enum.py example.com

# Advanced usage
python3 subdomain_enum.py example.com -w wordlists/common.txt -o results.json -v
