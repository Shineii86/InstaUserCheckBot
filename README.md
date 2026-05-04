<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=8B5CF6,06B6D4&height=200&section=header&text=Instagram%20Bot&fontSize=70&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Instagram%20Username%20Checker%20v3.0&descSize=20" />

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Shineii86/InstaUserCheckBot/blob/main/notebooks/InstaUserCheckBot.ipynb)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-3.0-blue.svg)](https://github.com/Shineii86/InstaUserCheckBot/releases)

[![GitHub Stars](https://img.shields.io/github/stars/Shineii86/InstaUserCheckBot?style=for-the-badge)](https://github.com/Shineii86/InstaUserCheckBot/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Shineii86/InstaUserCheckBot?style=for-the-badge)](https://github.com/Shineii86/InstaUserCheckBot/fork)

**Check Instagram username availability at scale. CLI tool, Telegram bot, or Google Colab — your choice.**

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
  - [Telegram Bot](#telegram-bot)
  - [CLI Tool](#cli-tool)
  - [Google Colab](#google-colab)
- [🤖 Bot Commands](#-bot-commands)
- [📚 CLI Reference](#-cli-reference)
- [⚙️ Configuration](#️-configuration)
- [📁 Project Structure](#-project-structure)
- [🌐 Proxy Support](#-proxy-support)
- [FAQ](#-faq)
- [License](#-license)

---

## 🎯 Overview

**InstaUserCheckBot** checks Instagram username availability at scale. Three ways to use it:

| Mode | Best For | Run It |
|------|----------|--------|
| 🤖 **Telegram Bot** | Personal use, phone alerts, interactive | `python run_bot.py` |
| 💻 **CLI Tool** | Automation, scripts, batch jobs | `python main.py` |
| 📓 **Google Colab** | Quick start, no install | Open notebook |

---

## ✨ Features

| Category | Feature | Description |
|----------|---------|-------------|
| 🔍 **Modes** | Single Check | Check one username via `/check` or CLI |
| | Batch Check | Check multiple via `/batch` or `--wordlist` (max 200) |
| | Random Generation | Generate & check via `/generate` or CLI |
| | Pattern Templates | Generate from patterns via `/pattern` |
| | Word Combos | Adjective + noun + number names |
| 🧬 **Generation** | Random | Pure random character usernames |
| | Word Combos | `fastcoder42`, `coolhacker`, `wildwolf7` |
| | Mixed | Round-robin across strategies for variety |
| | Pattern Templates | `user_????`, `test_##`, `my_!_!_name` |
| | Smart Dedup | Never checks the same username twice |
| 🚀 **Performance** | Multi-threading | Configurable worker count (1–10) |
| | Proxy Rotation | HTTP/HTTPS/SOCKS from file or URL |
| | CSRF Session Reuse | Single session with 5-min token refresh |
| | UA Rotation | Rotates across 6 browser fingerprints |
| | Retry Logic | Exponential backoff on rate limits (3 retries) |
| | Auto Delay | Automatically increases delay when rate limited |
| 📲 **Telegram** | Interactive Bot | Full inline keyboard UI |
| | Inline Query | Check from any chat with `@botname username` |
| | Rich Hit Alerts | Notifications with Open/Stop buttons |
| | Progress Updates | Speed tracking during batch & generate |
| | Settings Panel | Change length, chars, delay, gen mode in-chat |
| | Quick Check | Just type a username — no command needed! |
| | Check History | View recent checks with `/history` |
| | Bot Status | Check uptime & responsiveness with `/ping` |
| | About Page | Bot info & credits via `/about` |
| | Retry on Error | One-tap retry for failed checks |
| | Copy to Clipboard | Quick-copy available usernames |
| | Time-Aware Greeting | Welcome message adapts to time of day |
| 🌐 **Web App** | Full Mini App | 7-page app with batch, generate, pattern, settings |
| | Haptic Feedback | Native Telegram haptics on all interactions |
| | CloudStorage | Settings persist across sessions |
| 📓 **Colab** | One-Click Bot | Launch Telegram bot directly from notebook |
| | Textarea Input | Multi-line username input with Run button |
| | Config Sliders | Sliders, dropdowns, and toggles for all settings |
| 💾 **Output** | Auto-Save | Hits saved to file in real-time |
| | Export Hits | Export all available names from any session |
| 🛡️ **Safety** | Thread-Safe Stats | Locked counters, proper stop conditions |
| | Rate Limit Detection | Counted separately, not silently skipped |
| | Batch Limits | Max 200 per batch to prevent abuse |

---

## 🚀 Quick Start

### Telegram Bot

```bash
# Clone & install
git clone https://github.com/Shineii86/InstaUserCheckBot.git
cd InstaUserCheckBot
pip install -r requirements.txt

# Run the bot
python run_bot.py --token YOUR_BOT_TOKEN
```

Or from environment:
```bash
export TELEGRAM_BOT_TOKEN="1234567890:ABC..."
python run_bot.py
```

Then open your bot in Telegram and send `/start`.

### CLI Tool

```bash
# Interactive (prompts for token/chat-id)
python main.py

# With arguments
python main.py --token TOKEN --chat-id CHAT_ID --mode hits --stop-after 5

# With config file
python main.py --config config.json

# With wordlist
python main.py --token TOKEN --chat-id CHAT_ID --wordlist usernames.txt
```

### Google Colab

Click the **Open in Colab** badge at the top. Run both cells. Done.

---

## 🤖 Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome screen with quick-action buttons | `/start` |
| `/help` | Show all commands, rules & pattern syntax | `/help` |
| `/check username` | Check a single username | `/check coolname123` |
| `/batch user1,user2,user3` | Check multiple (comma/space/newline) | `/batch abc,xyz,test` |
| `/generate` | Generate & check 20 random usernames | `/generate` |
| `/generate 50` | Generate & check N random usernames | `/generate 50` |
| `/generate 50 word_combo` | Generate with word combos | `/generate 50 word_combo` |
| `/pattern template` | Generate from pattern template | `/pattern user_????` |
| `/pattern tmpl 50` | Pattern with custom count | `/pattern test_## 50` |
| `/settings` | View/change length, chars, delay, gen mode | `/settings` |
| `/stats` | Show session statistics with hit rate | `/stats` |
| `/history` | View recent check log with timestamps | `/history` |
| `/ping` | Check bot uptime & responsiveness | `/ping` |
| `/about` | Bot info, version, and credits | `/about` |
| `/stop` | Stop current batch/generation | `/stop` |
| `@botname username` | Inline query — check from any chat | `@mybot coolname123` |

**💡 Quick check:** Just type a username as a message (no command needed) — the bot checks it instantly.

**🔍 Inline query:** Use `@botname username` in any chat to check availability without opening the bot.

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
| `MODE` | `continuous` | `continuous`, `count`, or `hits` |
| `MAX_WORKERS` | `10` | Thread count |
| `DELAY` | `0.5` | Seconds between requests |
| `USE_PROXIES` | `false` | Enable proxy rotation |
| `PROXY_FILE` / `PROXY_URL` | — | Proxy source |

---

## 📁 Project Structure

```
InstaUserCheckBot/
├── main.py                 # CLI entry point
├── run_bot.py              # Telegram bot entry point
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── LICENSE
├── checker/                # Core checking engine
│   ├── __init__.py
│   ├── config.py           # Configuration dataclass
│   ├── instagram.py        # Instagram API (CSRF, session, UA rotation, retries)
│   ├── telegram.py         # Telegram notification helper (for CLI mode)
│   ├── generator.py        # Username generation (random, word combo, pattern, mixed)
│   ├── proxy.py            # Proxy manager
│   └── core.py             # CLI orchestrator (threading, stats)
├── bot/                    # Telegram bot interface
│   ├── __init__.py
│   └── handlers.py         # All /commands, callbacks, inline queries, settings UI
├── webapp/                 # Telegram Web App (Mini App)
│   └── index.html          # Full page-based mini app
└── notebooks/
    └── InstaUserCheckBot.ipynb  # Colab notebook
```

---

## 🌐 Proxy Support

One proxy per line:
```
http://user:pass@host:port
http://host:port
socks5://host:port
```

CLI: `--proxy-file proxies.txt` or `--proxy-url https://...`
Bot: Configure via environment variables before starting.

> ⚠️ Free proxies are unreliable. Use private/residential proxies for serious hunting.

---

## ❓ FAQ

### How do I create a Telegram bot?
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`, choose a name and username
3. Copy the token — that's your `TELEGRAM_BOT_TOKEN`

### How do I get my Chat ID?
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It replies with your ID — that's your `TELEGRAM_CHAT_ID`

### How many usernames per hour?
~72,000 theoretical (10 threads, 0.5s delay). Rate limits reduce this without proxies. The bot now has automatic retry with exponential backoff.

### Can I run both CLI and bot?
Yes! They're independent. CLI sends alerts to your Telegram chat. Bot runs as a Telegram bot.

### What are pattern templates?
Patterns let you generate usernames from a template. Use special characters as placeholders:
- `?` = random letter, `#` = random digit, `!` = letter or digit
- Example: `/pattern user_????` generates `user_abcd`, `user_wxyz`, etc.
- Example: `/pattern pro_####` generates `pro_1234`, `pro_5678`, etc.

### What's the difference between generation modes?
- **Random** — Pure random characters. Fast but names are hard to remember.
- **Word Combos** — Adjective + noun + number. Produces pronounceable names like `coolhacker` or `wildwolf7`.
- **Mixed** — Combines both strategies for variety.
- Use `/settings` → Gen Mode to switch, or `--gen-mode word_combo` in CLI.

### What's new in v3.0?
- **Pattern templates:** `/pattern user_????` — generate from custom patterns
- **Word combos:** `/generate 50 word_combo` — memorable names like `coolcoder42`
- **Inline query:** Check from any chat with `@botname username`
- **Web App:** Full mini app with batch, generate, pattern, settings
- **Retry logic:** Exponential backoff on rate limits
- **Rich notifications:** Hit alerts with Open/Copy/Retry buttons
- **History & ping:** `/history` and `/ping` commands
- See [CHANGELOG.md](CHANGELOG.md) for full details

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
