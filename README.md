<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=8B5CF6,06B6D4&height=200&section=header&text=Instagram%20Bot&fontSize=70&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Instagram%20Username%20Checker%20v2.0&descSize=20" />

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Shineii86/InstaUserCheckBot/blob/main/notebooks/InstaUserCheckBot.ipynb)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![GitHub Stars](https://img.shields.io/github/stars/Shineii86/InstaUserCheckBot?style=for-the-badge)](https://github.com/Shineii86/InstaUserCheckBot/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Shineii86/InstaUserCheckBot?style=for-the-badge)](https://github.com/Shineii86/InstaUserCheckBot/fork)

**The ultimate Instagram username availability checker. Mass‑check usernames with multi‑threading, proxy rotation, and Telegram alerts — run from Colab or your own machine.**

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [🆕 What's New in v2.0](#-whats-new-in-v20)
- [✨ Features](#-features)
- [Quick Start](#-quick-start)
  - [Google Colab](#google-colab)
  - [Local (CLI)](#local-cli)
- [CLI Reference](#-cli-reference)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Proxy Support](#-proxy-support)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [License](#-license)

---

## 🎯 Overview

**InstaUserCheckBot** checks Instagram username availability at scale. It combines random generation with custom wordlists, multi‑threading for speed, proxy support to avoid rate limits, and instant Telegram notifications for every available username found.

---

## 🆕 What's New in v2.0

| Area | v1.0 (Old) | v2.0 (New) |
|------|-----------|-----------|
| **Session** | New session + CSRF per request (2x requests) | Single session, CSRF auto-refreshes every 5 min |
| **User-Agent** | Static Firefox UA | Rotating pool of 6 modern browsers |
| **Email** | Hardcoded `example@gmail.com` | Random generated per request |
| **Thread Safety** | Plain `bool` flag, unprotected list | `threading.Event` + locked `Stats` class |
| **Rate Limits** | Skipped silently | Detected, counted, reported separately |
| **Memory** | Futures list grows unbounded | Proper `as_completed()` draining |
| **Local Use** | Colab-only imports crash locally | Works everywhere, Colab is optional |
| **CLI** | None | Full `argparse` with `--config`, `--env`, flags |
| **Structure** | Single notebook file | Modular `checker/` Python package |
| **Retry** | No retry on errors | Proper error categorization |

---

## ✨ Features

| Category | Feature | Description |
|----------|---------|-------------|
| 🔍 **Modes** | Random Generation | Generate usernames with full control over length, chars, patterns. |
| | Custom Wordlist | Upload file or provide URL to a wordlist. |
| 🚀 **Performance** | Multi‑threading | Configurable worker count for concurrent checks. |
| | Proxy Rotation | HTTP/HTTPS/SOCKS proxies from file or URL. |
| | CSRF Session Reuse | Single session with 5-minute token refresh. |
| | UA Rotation | Rotates across 6 browser fingerprints. |
| 📲 **Telegram** | Instant Alerts | Hit notification with counter and stats. |
| | Status Updates | Start/finish notifications. |
| 💾 **Output** | Auto-Save | Hits appended to file in real-time. |
| | Colab Download | Auto-download link in Colab. |
| 🎯 **Stop** | Hit Limit | Stop after N available usernames. |
| | Attempt Limit | Stop after N total checks. |
| | Continuous | Run until manually stopped. |
| 🛡️ **Safety** | Pattern Filters | Avoid dots/underscores/numbers at start/end. |
| | Thread-Safe Stats | Locked counters for accurate reporting. |

---

## 🚀 Quick Start

### Google Colab

1. Click the **Open in Colab** badge above.
2. Run Cell 1 (installs dependencies).
3. Fill in your Telegram token & chat ID in Cell 2.
4. Run Cell 2 — hits appear in Telegram as they're found.

### Local (CLI)

```bash
# Clone
git clone https://github.com/Shineii86/InstaUserCheckBot.git
cd InstaUserCheckBot

# Install
pip install -r requirements.txt

# Run (interactive — prompts for token/chat-id)
python main.py

# Run with args
python main.py --token YOUR_TOKEN --chat-id YOUR_CHAT_ID --mode hits --stop-after 5

# Run with config file
python main.py --config config.json

# Run from env vars
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python main.py --env
```

---

## 📚 CLI Reference

```
usage: python main.py [options]

Telegram:
  --token, -t         Telegram Bot Token
  --chat-id, -c       Telegram Chat ID

Username Generation:
  --length, -l        Username length (default: 5)
  --chars             Character set
  --no-start-dot      Don't avoid starting with dot
  --no-end-dot        Don't avoid ending with dot

Wordlist:
  --wordlist, -w      Path to wordlist file
  --wordlist-url      URL to wordlist

Run Mode:
  --mode, -m          continuous | count | hits (default: continuous)
  --max-attempts      Max checks for 'count' mode (default: 100)
  --stop-after        Stop after N hits for 'hits' mode (default: 10)

Performance:
  --workers, -W       Thread count (default: 10)
  --delay, -d         Delay between requests in seconds (default: 0.5)
  --proxy-file        Path to proxy list file
  --proxy-url         URL to proxy list

Output:
  --output, -o        Output file (default: available_usernames.txt)
  --no-save           Don't save hits to file

Config:
  --config            Path to JSON config file
  --env               Load from environment variables only
```

---

## ⚙️ Configuration

### JSON Config File

```json
{
  "telegram_token": "1234567890:ABC...",
  "telegram_chat_id": "987654321",
  "username_length": 5,
  "character_set": "1234567890qwertyuiopasdfghjklzxcvbnm._",
  "mode": "hits",
  "stop_after_hits": 10,
  "max_workers": 10,
  "delay": 0.5,
  "use_proxies": true,
  "proxy_url": "https://example.com/proxies.txt"
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | — | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | — | Your Telegram user ID |
| `USERNAME_LENGTH` | `5` | Length of generated usernames |
| `CHARACTER_SET` | `a-z0-9._` | Characters for generation |
| `MODE` | `continuous` | `continuous`, `count`, or `hits` |
| `MAX_ATTEMPTS` | `100` | Max checks in `count` mode |
| `STOP_AFTER_HITS` | `10` | Stop after N hits in `hits` mode |
| `MAX_WORKERS` | `10` | Thread count |
| `DELAY` | `0.5` | Seconds between requests |
| `USE_PROXIES` | `false` | Enable proxy rotation |
| `PROXY_FILE` | — | Path to proxy list |
| `PROXY_URL` | — | URL to proxy list |
| `USE_WORDLIST` | `false` | Use custom wordlist |
| `WORDLIST_PATH` | — | Path to wordlist file |
| `WORDLIST_URL` | — | URL to wordlist |
| `SAVE_HITS` | `true` | Save available usernames to file |
| `OUTPUT_FILE` | `available_usernames.txt` | Output filename |

---

## 📁 Project Structure

```
InstaUserCheckBot/
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── README.md
├── LICENSE
├── checker/                # Core package
│   ├── __init__.py
│   ├── config.py           # Configuration (dataclass + loaders)
│   ├── instagram.py        # Instagram API client (CSRF, session, UA rotation)
│   ├── telegram.py         # Telegram notification helper
│   ├── generator.py        # Username generation + wordlist loading
│   ├── proxy.py            # Proxy manager (file/URL loading, rotation)
│   └── core.py             # Main orchestrator (threading, stats, stop)
└── notebooks/
    └── InstaUserCheckBot.ipynb  # Colab notebook (uses checker package)
```

---

## 🌐 Proxy Support

Proxies should be one per line in plain text:

```
http://user:pass@host:port
http://host:port
socks5://host:port
```

Load from file:
```bash
python main.py --proxy-file proxies.txt
```

Load from URL:
```bash
python main.py --proxy-url https://example.com/proxies.txt
```

> ⚠️ Free proxies are unreliable. Use private/residential proxies for serious hunting.

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Failed to fetch CSRF" | Instagram blocking the IP. Enable proxies. |
| Rate limited immediately | Increase `--delay`, reduce `--workers`, use proxies. |
| Telegram not arriving | Check token and chat ID. Start a chat with the bot first. |
| Wordlist not loading | Check file path/URL. File must be `.txt` with one username per line. |
| Script stops unexpectedly | Check `--mode`. `count` and `hits` modes stop automatically. |

---

## ❓ FAQ

### Is this legal?
Checking username availability via Instagram's public endpoints is not illegal. However, aggressive automation may violate Instagram's ToS. Use responsibly.

### How many usernames per hour?
With 10 threads and 0.5s delay: ~72,000/hour theoretical. In practice, rate limits kick in without proxies. With good proxies: thousands per hour.

### Can I run on my own PC?
Yes! `pip install requests` and run `python main.py`. No Colab needed.

### How do I stop?
Press `Ctrl+C`. The script handles it gracefully and prints a summary.

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

> ⚠️ **Disclaimer**: Educational and personal use only. Automated access to Instagram may violate their ToS. Use at your own risk.

---

<div align="center">

**Copyright [Shinei Nouzen](https://github.com/Shineii86) All Rights Reserved.**

[![Telegram](https://img.shields.io/badge/-Telegram-2CA5E0?style=flat&logo=Telegram&logoColor=white)](https://telegram.me/Shineii86)
[![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat&logo=GitHub&logoColor=white)](https://github.com/Shineii86)

</div>
