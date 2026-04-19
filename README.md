<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=8B5CF6,06B6D4&height=200&section=header&text=Instagram%20Bot&fontSize=70&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Instagram%20Username%20Checker%20Script&descSize=20" />

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Shineii86/InstaUserCheckBot/blob/main/notebooks/InstaUserCheckBot.ipynb)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![GitHub Stars](https://img.shields.io/github/stars/Shineii86/InstaUserCheckBot?style=for-the-badge)](https://github.com/Shineii86/InstaUserCheckBot/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Shineii86/InstaUserCheckBot?style=for-the-badge)](https://github.com/Shineii86/InstaUserCheckBot/fork)

**The ultimate Instagram username availability checker. Mass‑check usernames with multi‑threading, proxy rotation, and Telegram alerts – all from Google Colab.**

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [✨ Features](#-features)
- [How It Works](#-how-it-works)
- [Prerequisites & Telegram Setup](#-prerequisites--telegram-setup)
  - [1. Create a Telegram Bot](#1-create-a-telegram-bot)
  - [2. Get Your Chat ID](#2-get-your-chat-id)
- [Quick Start Guide](#-quick-start-guide)
- [Detailed Usage](#-detailed-usage)
  - [Random Generation Mode](#-random-generation-mode)
  - [Custom Wordlist Mode](#-custom-wordlist-mode)
- [⚙️ Configuration Reference](#️-configuration-reference)
  - [Core Settings](#core-settings)
  - [Performance & Anti-Ban Settings](#performance--anti-ban-settings)
  - [Output Settings](#output-settings)
- [🌐 Proxy Support](#-proxy-support)
- [🆘 Troubleshooting](#-troubleshooting)
- [❓ FAQ](#-faq)
- [📄 License & Disclaimer](#-license--disclaimer)
- [💕 Credits & Acknowledgments](#-credits--acknowledgments)

---

## 🎯 Overview

**InstaUserCheckBot** is a powerful, easy‑to‑use Google Colab notebook that automates the process of checking Instagram username availability at scale.  
It combines a flexible random generator with optional custom wordlists, multi‑threading for speed, proxy support to avoid rate‑limiting, and instant Telegram notifications for every available username found.

Whether you're hunting for rare 3‑letter handles or testing thousands of patterns, this tool does the heavy lifting while you sit back and receive hits directly on your phone.

---

## ✨ Features

| Category | Feature | Description |
|----------|---------|-------------|
| 🔍 **Checking Modes** | Random Generation | Generate usernames on‑the‑fly with full control over length, character set, and pattern rules. |
| | Custom Wordlist | Upload or provide a URL to a wordlist of usernames to check. |
| 🚀 **Performance** | Multi‑threading | Check dozens of usernames concurrently – configurable worker count. |
| | Proxy Rotation | Load HTTP/HTTPS/SOCKS proxies from a URL to avoid IP bans. |
| | Smart Delays | Adjustable delay between requests to stay under radar. |
| 📲 **Telegram Integration** | Instant Alerts | Get a Telegram message for every available username with a counter. |
| | Status Updates | Optional start/finish notifications. |
| 💾 **Output** | Auto‑Save | All hits are automatically appended to a text file. |
| | Download Link | At the end of the session, download the file directly from Colab. |
| 🛡️ **Safety** | Expiration Option | Set an expiration date for the script (useful for sharing). |
| | Pattern Filters | Avoid usernames starting/ending with dots, underscores, or numbers. |

---

## 🔬 How It Works

1. **CSRF Token Fetch** – The bot requests Instagram’s signup page to obtain a valid CSRF token.
2. **Username Source** –  
   - *Random Mode*: Generates usernames according to your length and character rules.  
   - *Wordlist Mode*: Reads usernames from an uploaded file or a public URL.
3. **Availability Check** – Sends a POST request to Instagram’s internal AJAX endpoint.  
   - If `"username_is_taken"` appears → taken.  
   - If `"feedback_required"` appears → rate‑limited (retry with proxy/delay).  
   - Otherwise → **available**.
4. **Notification & Save** – Available usernames trigger a Telegram message and are saved to `available_usernames.txt`.
5. **Loop** – The process continues until you stop it or the maximum attempt count is reached.

---

## 🛠️ Prerequisites & Telegram Setup

You need two things from Telegram:

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**.
2. Send the command `/newbot`.
3. Choose a **name** (e.g., `My Username Checker`) and a **username** (must end in `bot`, e.g., `my_username_bot`).
4. BotFather will give you a **token**:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
   **Copy this token** – you'll need it for the notebook.

### 2. Get Your Chat ID

Your **Chat ID** is the unique identifier for your Telegram account.

**Easiest method – using @userinfobot:**
1. Search for **@userinfobot** on Telegram.
2. Send any message (e.g., `/start`).
3. The bot replies with your `Id`. That number is your **Chat ID**.

**Alternative – using your own bot:**
1. Send a message to your newly created bot (search for its username and say "Hello").
2. Visit this URL in your browser (replace `YOUR_BOT_TOKEN` with your token):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Look for `"chat":{"id":123456789}` – that's your Chat ID.

---

## 🚀 Quick Start Guide

1. **Click the "Open in Colab" badge** at the top of this README.
2. **Run the first cell** (`📦 1. Install Dependencies`) – nothing to install, it's just a check.
3. **In the second cell** (`⚙️ 2. Configuration & Run`):
   - Paste your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
   - Choose your desired settings (username length, character set, etc.).
4. **Run the second cell**.
5. Check your Telegram – available usernames will appear as they are found.
6. When you stop the script, a download link for `available_usernames.txt` will appear.

---

## 📚 Detailed Usage

### 🎲 Random Generation Mode

This is the default mode. The notebook generates usernames randomly based on your parameters.

**Key Configuration:**
```python
USERNAME_LENGTH = 5
CHARACTER_SET = "1234567890qwertyuiopasdfghjklzxcvbnm._"
AVOID_START_DOT = True
AVOID_END_DOT = True
MODE = "continuous"   # Runs forever until stopped
# or MODE = "count" + MAX_ATTEMPTS = 1000
```

### 📁 Custom Wordlist Mode

Use your own pre‑generated list of usernames.

**Configuration:**
```python
USE_CUSTOM_WORDLIST = True
WORDLIST_URL = "https://example.com/my_usernames.txt"
# If you leave WORDLIST_URL blank, you'll be prompted to upload a file.
```

The wordlist should be a plain text file with one username per line.

---

## ⚙️ Configuration Reference

### Core Settings

| Parameter | Description | Example |
|-----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather | `"1234567890:ABC..."` |
| `TELEGRAM_CHAT_ID` | Your personal chat ID | `"987654321"` |
| `USERNAME_LENGTH` | Length of generated usernames | `5` |
| `CHARACTER_SET` | Allowed characters | `"abc123._"` |
| `AVOID_START_DOT` | Prevent usernames starting with `.` | `True` |
| `AVOID_END_DOT` | Prevent usernames ending with `.` | `True` |
| `AVOID_START_UNDERSCORE` | Prevent starting with `_` | `False` |
| `AVOID_END_UNDERSCORE` | Prevent ending with `_` | `False` |
| `AVOID_START_NUMBER` | Prevent starting with a digit | `False` |
| `MODE` | `"continuous"` (run forever) or `"count"` | `"continuous"` |
| `MAX_ATTEMPTS` | Max checks when `MODE = "count"` | `1000` |
| `USE_CUSTOM_WORDLIST` | Enable custom wordlist | `False` |
| `WORDLIST_URL` | URL to wordlist (optional) | `""` |

### Performance & Anti‑Ban Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `USE_MULTITHREADING` | Enable concurrent checking | `True` |
| `MAX_WORKERS` | Number of parallel threads | `10` |
| `DELAY_BETWEEN_REQUESTS` | Seconds to wait after each request | `0.5` |
| `USE_PROXY_LIST` | Enable proxy rotation | `False` |
| `PROXY_LIST_URL` | URL to a proxy list (one per line) | `""` |

### Output Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `SAVE_AVAILABLE_TO_FILE` | Save hits to a text file | `True` |
| `OUTPUT_FILENAME` | Name of the output file | `"available_usernames.txt"` |
| `ENABLE_EXPIRATION` | Set an expiration date for the script | `False` |
| `EXPIRATION_DATE` | Date in `YYYY-MM-DD` format | `"2099-01-01"` |

---

## 🌐 Proxy Support

To avoid Instagram’s rate limits, you can provide a list of proxies. The list must be a **plain text file** accessible via URL, with one proxy per line.  
Supported formats:
- `http://user:pass@host:port`
- `http://host:port`
- `socks5://host:port`

**Example proxy list:**
```
http://user1:pass1@192.168.1.1:8080
socks5://192.168.1.2:1080
http://192.168.1.3:3128
```

Set `USE_PROXY_LIST = True` and paste the URL into `PROXY_LIST_URL`.

> ⚠️ Free public proxies are often unreliable. For serious hunting, consider using private or residential proxies.

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Failed to fetch CSRF Token"** | Instagram may be blocking Colab's IP. Try enabling proxies or using a VPN. |
| **Rate limited immediately** | Increase `DELAY_BETWEEN_REQUESTS` and reduce `MAX_WORKERS`. Use proxies. |
| **Telegram messages not arriving** | Double‑check the bot token and chat ID. Ensure you've started a chat with the bot. |
| **Wordlist upload not working** | Make sure you run the cell and select a file when prompted. File must be `.txt`. |
| **Script stops unexpectedly** | If using `MODE = "count"`, it will stop after `MAX_ATTEMPTS`. For continuous, it runs until you interrupt it (press stop button in Colab). |

---

## ❓ FAQ

### Q: Is this legal?
**A:** Checking username availability via Instagram's public endpoints is not illegal. However, aggressive automated requests may violate Instagram's Terms of Service. Use responsibly and at your own risk.

### Q: Can I run this on my own PC?
**A:** Yes! Download the notebook and run it in Jupyter. You'll need to remove Colab‑specific imports (`google.colab`) or install `jupyter` locally.

### Q: How many usernames can I check per hour?
**A:** With 10 threads and a 0.5s delay, roughly **72,000 checks per hour** – but you will likely hit rate limits without proxies. With good proxies and tuned delays, you can sustain thousands per hour.

### Q: Can I check usernames of a specific pattern (e.g., `@name123`)?
**A:** Absolutely – use **Custom Wordlist Mode**. Generate your pattern‑based list externally and feed it to the bot.

### Q: Does this work for Instagram's new "username" vs "handle" system?
**A:** Yes. The endpoint used (`/accounts/web_create_ajax/attempt/`) is the same one Instagram uses during signup to validate handle availability.

---

## 📄 License & Disclaimer

This project is licensed under the **MIT License**.

> ⚠️ **Disclaimer**: This tool is intended for educational and personal use only. Automated access to Instagram's servers may be against their Terms of Service. The author assumes no liability for any account bans, IP blocks, or other consequences resulting from the use of this software. Use at your own risk.

---

## 💕 Credits & Acknowledgments

- [requests](https://docs.python-requests.org/) – elegant HTTP library.
- [Google Colab](https://colab.research.google.com/) – free cloud runtime.
- [Telegram Bot API](https://core.telegram.org/bots/api) – simple messaging.
- Original script concept by [Maxim_ffx](https://telegram.me/Maxim_ffx).

---

## 💕 Loved My Work?

🚨 [Follow me on GitHub](https://github.com/Shineii86)

⭐ [Give a star to this project](https://github.com/Shineii86/InstaUserCheckBot)

<div align="center">

<a href="https://github.com/Shineii86/InstaUserCheckBot">
<img src="https://github.com/Shineii86/AniPay/blob/main/Source/Banner6.png" alt="Banner">
</a>
  
  *For inquiries or collaborations*
     
[![Telegram Badge](https://img.shields.io/badge/-Telegram-2CA5E0?style=flat&logo=Telegram&logoColor=white)](https://telegram.me/Shineii86)
[![Instagram Badge](https://img.shields.io/badge/-Instagram-C13584?style=flat&logo=Instagram&logoColor=white)](https://instagram.com/ikx7.a)
[![Gmail Badge](https://img.shields.io/badge/-Gmail-D14836?style=flat&logo=Gmail&logoColor=white)](mailto:ikx7a@hotmail.com)

  <sup><b>Copyright © 2026 <a href="https://telegram.me/Shineii86">Shinei Nouzen</a> All Rights Reserved</b></sup>

![Last Commit](https://img.shields.io/github/last-commit/Shineii86/InstaUserCheckBot?style=for-the-badge)

</div>
