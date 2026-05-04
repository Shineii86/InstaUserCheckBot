# 📋 Changelog

All notable changes to **InstaUserCheckBot** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0] — 2026-05-04

### 🎨 v3.0 — Full UI/UX Overhaul

#### ✨ Added — New Bot Commands
- **`/pattern`** — Generate usernames from pattern templates
  - Syntax: `?`=letter `#`=digit `!`=alnum `_`=underscore
  - Examples: `/pattern user_????`, `/pattern pro_####`
  - Quick templates menu with one-tap generation
- **`/history`** — View recent check log with timestamps and status emojis
- **`/ping`** — Check bot uptime, version, and session stats
- **`/about`** — Bot info, version, author, and GitHub link
- **`/cancel`** — Alias for `/stop`

#### ✨ Added — Generation Engine
- **Word Combo Generator** — Adjective + noun + number combinations
  - 60+ adjectives (fast, cool, cyber, pixel, quantum, etc.)
  - 60+ nouns (coder, ninja, dragon, phoenix, etc.)
  - Smart number suffixes with 60% probability
- **Pattern Template Generator** — Generate from custom patterns
  - Full syntax: `?`=letter `#`=digit `!`=alnum `_`=underscore
- **Mixed Generation Mode** — Round-robin across random + word combo
- **Smart Dedup** — Tracks all generated usernames to prevent duplicates
- **Generation Mode Selector** — New setting in /settings
  - 🎲 Random — Pure random characters
  - 🧠 Word Combos — Adjective+noun+number
  - 🌈 Mixed — Best of both worlds

#### ✨ Added — Retry Logic & Backoff
- **Exponential backoff** on rate limits (base 2.0, max 30s)
  - Automatic retry up to 3 times per request
  - Jitter added to prevent thundering herd
  - UA rotation on each retry attempt
- **Auto-adjust delay** — Automatically increases delay after consecutive rate limits
- **`recommended_delay` property** — Dynamic delay based on rate limit history
- **Rate limit tracking** — Consecutive and total rate limit counters

#### ✨ Added — Enhanced UX Features
- **Time-aware greeting** — `/start` adapts message based on time of day
- **Speed tracking** — Real-time checks/sec displayed during batch and generate
- **Elapsed time** — Total time shown in completion reports
- **Retry on error** — One-tap "🔄 Retry" button when a check fails
- **Copy username** — "📋 Copy Name" button on available username results
- **Export hits button** — Export all available names from any session
- **Session uptime** — Displayed in `/ping` command
- **History tracking** — All checks automatically logged with timestamps
- **Batch size limit** — Max 200 usernames per batch with clear error message
- **Progress bar** — Visual progress indicator in stats

#### ✨ Added — Inline Query Mode
- **Inline query** — Check usernames from any chat with `@botname username`
  - Available/taken results with claim links
  - Instant feedback without opening the bot

#### ✨ Added — Web App (Mini App)
- **Full page-based mini app** — Home, Single, Batch, Generate, Pattern, History, Settings
- **Batch checking** — Check up to 200 usernames with progress bar
- **Generate & Check** — All generation modes with configurable count
- **Pattern templates** — Quick-tap symbol insert and preset templates
- **Session stats** — Live stats bar on home page
- **History & Export** — View history and export to .txt
- **Settings** — Configure length, chars, gen mode, delay
- **Haptic feedback** — Native Telegram haptics on all interactions
- **CloudStorage** — Settings persist via Telegram CloudStorage

#### ✨ Added — Unified Renderers
- **`render_start()`**, **`render_help()`**, **`render_settings()`**, **`render_stats()`**, **`render_history()`**, **`render_export()`** — Eliminate code duplication
- **`safe_edit()` helper** — Silently handles "message is not modified" errors
- **`_render_check_result()` shared renderer** — Single source of truth for check results

#### 🔧 Changed — Callback Data Overhaul
- **Shortened all callback_data** to stay under Telegram's 64-byte limit
  - `settings` → `s`, `stats` → `st`, `history` → `hi`, `help` → `hp`
  - `set_length` → `sl`, `len_5` → `l:5`, `set_chars` → `sc`
  - `set_delay` → `sd`, `delay_1.0` → `d:1.0`, `set_workers` → `sw`
  - `set_gen_mode` → `sg`, `gen_random` → `gm:random`
  - `pattern_menu` → `pm`, `copy_username` → `c:username`
  - `confirm_reset_settings` → `crs`, `reset_settings` → `rs`
  - `stop_check` → `x`

#### 🔧 Changed — Instagram Client
- **Retry with exponential backoff** — Up to 3 retries per request
- **Auto CSRF refresh** on rate limits
- **Rate limit tracking** — Consecutive and total counters
- **Dynamic delay recommendation** based on rate limit history

#### 🔧 Changed — Generator
- **Major expansion** — Word combos, patterns, mixed mode
- **Smart dedup** with seen set
- **Pattern validation** with clear error messages

#### 📝 Documentation
- **README.md** — Updated to v3.0 with all new features
- **CHANGELOG.md** — Created with full release notes

---

## [2.0.0] — 2026-05-04

### 🎉 Initial Feature Release

#### ✨ Added
- **Telegram Bot** — Interactive bot with inline keyboard UI
  - `/check`, `/batch`, `/generate`, `/settings`, `/stats`, `/stop`
  - Quick check by typing a username
  - Inline keyboard menus for settings
- **CLI Tool** — Full-featured command-line interface
  - Interactive, CLI args, JSON config, environment variables
  - Three run modes: continuous, count, hits
- **Google Colab Notebook** — Zero-install browser experience
- **Core Engine** — Instagram username availability checking
  - CSRF session management with 5-min token refresh
  - Multi-threaded checking with configurable workers
  - Proxy rotation (HTTP/HTTPS/SOCKS)
  - User-Agent rotation (6 browser fingerprints)
  - Username generation with filters
  - Wordlist loading from file or URL
  - Real-time hit notifications via Telegram
  - Auto-save hits to file

---

## [Unreleased]

### 🔮 Planned
- SOCKS5 proxy authentication support
- Export results to CSV/JSON formats
- Rate limit auto-retry with exponential backoff (CLI mode)
- Multi-language support (i18n)
- Web dashboard for monitoring

---

<div align="center">

**[⬆ Back to Top](#-changelog)**

</div>
