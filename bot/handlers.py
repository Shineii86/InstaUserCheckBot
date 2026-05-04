"""
Telegram Bot — interactive Instagram username checker.

Commands:
    /start          — Welcome message
    /help           — Show help
    /check <name>   — Check a single username
    /batch <names>  — Check multiple usernames (comma-separated)
    /generate       — Generate & check random usernames
    /settings       — View/change settings
    /stats          — Show session statistics
    /stop           — Stop current batch/generation
"""

import asyncio
import random
import string
import threading
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

from checker.instagram import InstagramClient, AVAILABLE, TAKEN, RATE_LIMITED, ERROR
from checker.proxy import ProxyManager
from checker.generator import UsernameGenerator


# ── ANSI Colors for console ──
GRN = "\033[2;32m"
RED = "\033[1;31m"
RST = "\033[0m"


# ── Emoji Map (Telegram Premium) ──
EMOJI = {
    "check": "🔍",
    "hit": "✅",
    "taken": "❌",
    "rate": "⚠️",
    "error": "💥",
    "stats": "📊",
    "settings": "⚙️",
    "stop": "🛑",
    "start": "🚀",
    "user": "👤",
    "id": "🆔",
    "pack": "📦",
    "clock": "🕐",
    "fire": "🔥",
    "star": "⭐",
    "back": "🔙",
    "yes": "✅",
    "no": "❌",
}


class UserSession:
    """Per-user session state."""

    def __init__(self):
        self.checked = 0
        self.hits = 0
        self.taken = 0
        self.rate_limited = 0
        self.errors = 0
        self.available: list = []
        self.running = False
        self.should_stop = False

        # Settings
        self.username_length = 5
        self.char_set = "1234567890qwertyuiopasdfghjklzxcvbnm._"
        self.delay = 0.5
        self.max_workers = 5
        self.mode = "single"  # single, batch, generate

    def reset_stats(self):
        self.checked = 0
        self.hits = 0
        self.taken = 0
        self.rate_limited = 0
        self.errors = 0
        self.available = []

    def record(self, status: str, username: str):
        self.checked += 1
        if status == AVAILABLE:
            self.hits += 1
            self.available.append(username)
        elif status == TAKEN:
            self.taken += 1
        elif status == RATE_LIMITED:
            self.rate_limited += 1
        elif status == ERROR:
            self.errors += 1


# ── Global State ──
sessions: dict[int, UserSession] = {}
client: Optional[InstagramClient] = None


def get_session(user_id: int) -> UserSession:
    if user_id not in sessions:
        sessions[user_id] = UserSession()
    return sessions[user_id]


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /start."""
    user = update.effective_user
    text = (
        f"{EMOJI['fire']} <b>InstaUserCheckBot v2.0</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{EMOJI['user']} <b>User:</b> <code>{user.first_name}</code>\n"
        f"{EMOJI['id']} <b>UID:</b> <code>{user.id}</code>\n\n"
        f"{EMOJI['check']} <b>Check Instagram usernames instantly!</b>\n\n"
        f"<b>Commands:</b>\n"
        f"  /check username — Check one username\n"
        f"  /batch user1,user2,user3 — Check multiple\n"
        f"  /generate — Generate & check random names\n"
        f"  /settings — Configure checker\n"
        f"  /stats — Session statistics\n"
        f"  /stop — Stop current operation"
    )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{EMOJI['check']} Quick Check", switch_inline_query_current_chat=""),
            InlineKeyboardButton(f"{EMOJI['settings']} Settings", callback_data="settings"),
        ],
        [
            InlineKeyboardButton(f"{EMOJI['stats']} Stats", callback_data="stats"),
            InlineKeyboardButton("📖 Help", callback_data="help"),
        ],
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /help."""
    text = (
        f"📖 <b>InstaUserCheckBot Help</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>🔹 /check username</b>\n"
        f"Check if a single Instagram username is available.\n"
        f"<i>Example:</i> <code>/check coolname123</code>\n\n"
        f"<b>🔹 /batch user1,user2,user3</b>\n"
        f"Check multiple usernames at once (comma-separated).\n"
        f"<i>Example:</i> <code>/batch abc,xyz,test123</code>\n\n"
        f"<b>🔹 /generate</b>\n"
        f"Generate random usernames and check availability.\n"
        f"Uses your configured length and character set.\n\n"
        f"<b>🔹 /settings</b>\n"
        f"View and change: username length, char set, delay.\n\n"
        f"<b>🔹 /stats</b>\n"
        f"Show checked count, hits, taken, errors.\n\n"
        f"<b>🔹 /stop</b>\n"
        f"Stop any running batch or generation.\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Made by @Shineii86</i>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /check <username>."""
    if not ctx.args:
        await update.message.reply_text(
            f"{EMOJI['error']} Usage: <code>/check username</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    username = ctx.args[0].strip().lower()
    if not username:
        await update.message.reply_text(f"{EMOJI['error']} Provide a username.")
        return

    session = get_session(update.effective_user.id)
    msg = await update.message.reply_text(
        f"{EMOJI['clock']} Checking <code>@{username}</code>...",
        parse_mode=ParseMode.HTML,
    )

    status, _ = await asyncio.to_thread(client.check, username, session.delay)
    session.record(status, username)

    if status == AVAILABLE:
        text = (
            f"{EMOJI['hit']} <b>AVAILABLE!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{EMOJI['user']} <b>Username:</b> <code>@{username}</code>\n"
            f"{EMOJI['hit']} <b>Status:</b> Available ✨\n"
            f"{EMOJI['stats']} <b>Total checked:</b> {session.checked}\n"
            f"{EMOJI['hit']} <b>Total hits:</b> {session.hits}"
        )
    elif status == TAKEN:
        text = (
            f"{EMOJI['taken']} <b>Taken</b>\n"
            f"{EMOJI['user']} <code>@{username}</code> is already registered."
        )
    elif status == RATE_LIMITED:
        text = (
            f"{EMOJI['rate']} <b>Rate Limited</b>\n"
            f"Instagram is blocking requests. Try again later or use a proxy."
        )
    else:
        text = f"{EMOJI['error']} <b>Error</b> checking <code>@{username}</code>."

    await msg.edit_text(text, parse_mode=ParseMode.HTML)


async def cmd_batch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /batch user1,user2,user3."""
    if not ctx.args:
        await update.message.reply_text(
            f"{EMOJI['error']} Usage: <code>/batch user1,user2,user3</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    raw = " ".join(ctx.args)
    usernames = [u.strip().lower() for u in raw.split(",") if u.strip()]
    if not usernames:
        await update.message.reply_text(f"{EMOJI['error']} No usernames provided.")
        return

    session = get_session(update.effective_user.id)
    session.running = True
    session.should_stop = False

    msg = await update.message.reply_text(
        f"{EMOJI['start']} <b>Batch Check Started</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{EMOJI['pack']} <b>Usernames:</b> {len(usernames)}\n"
        f"{EMOJI['clock']} <b>Delay:</b> {session.delay}s\n\n"
        f"<i>Checking...</i>",
        parse_mode=ParseMode.HTML,
    )

    results = {AVAILABLE: [], TAKEN: [], RATE_LIMITED: [], ERROR: []}

    for i, username in enumerate(usernames):
        if session.should_stop:
            break

        status, _ = await asyncio.to_thread(client.check, username, session.delay)
        session.record(status, username)
        results[status].append(username)

        # Update progress every 5 checks or on last
        if (i + 1) % 5 == 0 or i == len(usernames) - 1:
            try:
                await msg.edit_text(
                    f"{EMOJI['start']} <b>Batch Check Running</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"{EMOJI['pack']} Progress: {i + 1}/{len(usernames)}\n"
                    f"{EMOJI['hit']} Hits: {len(results[AVAILABLE])}\n"
                    f"{EMOJI['taken']} Taken: {len(results[TAKEN])}\n"
                    f"{EMOJI['rate']} Rate Limit: {len(results[RATE_LIMITED])}\n\n"
                    f"<i>Checking...</i>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    session.running = False

    # Final report
    hit_list = "\n".join(f"  <code>@{u}</code>" for u in results[AVAILABLE]) or "  <i>None</i>"
    text = (
        f"{EMOJI['stats']} <b>Batch Check Complete</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{EMOJI['pack']} <b>Total:</b> {len(usernames)}\n"
        f"{EMOJI['hit']} <b>Available:</b> {len(results[AVAILABLE])}\n"
        f"{EMOJI['taken']} <b>Taken:</b> {len(results[TAKEN])}\n"
        f"{EMOJI['rate']} <b>Rate Limited:</b> {len(results[RATE_LIMITED])}\n"
        f"{EMOJI['error']} <b>Errors:</b> {len(results[ERROR])}\n\n"
        f"{EMOJI['hit']} <b>Available Usernames:</b>\n{hit_list}"
    )

    if session.should_stop:
        text = f"{EMOJI['stop']} <b>Stopped!</b>\n\n" + text

    await msg.edit_text(text, parse_mode=ParseMode.HTML)


async def cmd_generate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /generate — generate and check random usernames."""
    session = get_session(update.effective_user.id)
    count = 20  # default batch size for generation

    if ctx.args:
        try:
            count = int(ctx.args[0])
            count = min(count, 100)  # cap at 100
        except ValueError:
            pass

    session.running = True
    session.should_stop = False

    gen = UsernameGenerator(
        length=session.username_length,
        chars=session.char_set,
    )

    msg = await update.message.reply_text(
        f"{EMOJI['fire']} <b>Generating & Checking</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{EMOJI['pack']} <b>Count:</b> {count}\n"
        f"{EMOJI['settings']} <b>Length:</b> {session.username_length}\n"
        f"{EMOJI['clock']} <b>Delay:</b> {session.delay}s\n\n"
        f"<i>Starting...</i>",
        parse_mode=ParseMode.HTML,
    )

    results = {AVAILABLE: [], TAKEN: [], RATE_LIMITED: [], ERROR: []}
    gen_iter = gen.random_stream()

    for i in range(count):
        if session.should_stop:
            break

        username = next(gen_iter)
        status, _ = await asyncio.to_thread(client.check, username, session.delay)
        session.record(status, username)
        results[status].append(username)

        if (i + 1) % 5 == 0 or i == count - 1:
            try:
                await msg.edit_text(
                    f"{EMOJI['fire']} <b>Generating & Checking</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"{EMOJI['pack']} Progress: {i + 1}/{count}\n"
                    f"{EMOJI['hit']} Hits: {len(results[AVAILABLE])}\n"
                    f"{EMOJI['taken']} Taken: {len(results[TAKEN])}\n"
                    f"{EMOJI['rate']} Rate Limit: {len(results[RATE_LIMITED])}\n\n"
                    f"<i>Checking...</i>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    session.running = False

    hit_list = "\n".join(f"  <code>@{u}</code>" for u in results[AVAILABLE]) or "  <i>None</i>"
    text = (
        f"{EMOJI['stats']} <b>Generation Complete</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{EMOJI['pack']} <b>Checked:</b> {count}\n"
        f"{EMOJI['hit']} <b>Available:</b> {len(results[AVAILABLE])}\n"
        f"{EMOJI['taken']} <b>Taken:</b> {len(results[TAKEN])}\n"
        f"{EMOJI['rate']} <b>Rate Limited:</b> {len(results[RATE_LIMITED])}\n\n"
        f"{EMOJI['hit']} <b>Available Usernames:</b>\n{hit_list}"
    )

    if session.should_stop:
        text = f"{EMOJI['stop']} <b>Stopped!</b>\n\n" + text

    await msg.edit_text(text, parse_mode=ParseMode.HTML)


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /stats."""
    session = get_session(update.effective_user.id)
    text = (
        f"{EMOJI['stats']} <b>Session Statistics</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{EMOJI['check']} <b>Checked:</b> {session.checked}\n"
        f"{EMOJI['hit']} <b>Available:</b> {session.hits}\n"
        f"{EMOJI['taken']} <b>Taken:</b> {session.taken}\n"
        f"{EMOJI['rate']} <b>Rate Limited:</b> {session.rate_limited}\n"
        f"{EMOJI['error']} <b>Errors:</b> {session.errors}\n"
    )
    if session.available:
        hit_list = "\n".join(f"  <code>@{u}</code>" for u in session.available[-10:])
        text += f"\n{EMOJI['hit']} <b>Recent Hits:</b>\n{hit_list}"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{EMOJI['stop']} Reset Stats", callback_data="reset_stats")],
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /stop."""
    session = get_session(update.effective_user.id)
    if session.running:
        session.should_stop = True
        await update.message.reply_text(
            f"{EMOJI['stop']} <b>Stopping...</b> Will finish current check shortly.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            f"{EMOJI['no']} Nothing is running.",
            parse_mode=ParseMode.HTML,
        )


async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /settings."""
    session = get_session(update.effective_user.id)
    await show_settings(update.message, session)


async def show_settings(message, session: UserSession):
    """Show settings menu with inline buttons."""
    text = (
        f"{EMOJI['settings']} <b>Settings</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📏 <b>Username Length:</b> {session.username_length}\n"
        f"🔤 <b>Character Set:</b> <code>{session.char_set}</code>\n"
        f"{EMOJI['clock']} <b>Delay:</b> {session.delay}s\n"
        f"🧵 <b>Workers:</b> {session.max_workers}\n"
    )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📏 Length", callback_data="set_length"),
            InlineKeyboardButton("🔤 Chars", callback_data="set_chars"),
        ],
        [
            InlineKeyboardButton(f"{EMOJI['clock']} Delay", callback_data="set_delay"),
            InlineKeyboardButton("🧵 Workers", callback_data="set_workers"),
        ],
        [
            InlineKeyboardButton(f"{EMOJI['back']} Reset All", callback_data="reset_settings"),
        ],
    ])
    await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


# ============================================================================
# CALLBACK QUERY HANDLERS
# ============================================================================

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    session = get_session(user_id)
    data = query.data

    if data == "settings":
        text = (
            f"{EMOJI['settings']} <b>Settings</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📏 <b>Username Length:</b> {session.username_length}\n"
            f"🔤 <b>Character Set:</b> <code>{session.char_set}</code>\n"
            f"{EMOJI['clock']} <b>Delay:</b> {session.delay}s\n"
            f"🧵 <b>Workers:</b> {session.max_workers}\n"
        )
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📏 Length", callback_data="set_length"),
                InlineKeyboardButton("🔤 Chars", callback_data="set_chars"),
            ],
            [
                InlineKeyboardButton(f"{EMOJI['clock']} Delay", callback_data="set_delay"),
                InlineKeyboardButton("🧵 Workers", callback_data="set_workers"),
            ],
        ])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "set_length":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(str(i), callback_data=f"len_{i}") for i in range(3, 8)],
            [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="settings")],
        ])
        await query.edit_message_text(
            f"📏 <b>Choose Username Length:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )

    elif data.startswith("len_"):
        session.username_length = int(data.split("_")[1])
        await query.edit_message_text(
            f"{EMOJI['yes']} Length set to <b>{session.username_length}</b>",
            parse_mode=ParseMode.HTML,
        )

    elif data == "set_chars":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("a-z 0-9 ._", callback_data="chars_default")],
            [InlineKeyboardButton("a-z only", callback_data="chars_alpha")],
            [InlineKeyboardButton("a-z 0-9", callback_data="chars_alnum")],
            [InlineKeyboardButton("0-9 only", callback_data="chars_digits")],
            [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="settings")],
        ])
        await query.edit_message_text(
            f"🔤 <b>Choose Character Set:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )

    elif data.startswith("chars_"):
        sets = {
            "chars_default": "1234567890qwertyuiopasdfghjklzxcvbnm._",
            "chars_alpha": "qwertyuiopasdfghjklzxcvbnm",
            "chars_alnum": "1234567890qwertyuiopasdfghjklzxcvbnm",
            "chars_digits": "1234567890",
        }
        session.char_set = sets.get(data, sets["chars_default"])
        await query.edit_message_text(
            f"{EMOJI['yes']} Character set updated:\n<code>{session.char_set}</code>",
            parse_mode=ParseMode.HTML,
        )

    elif data == "set_delay":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{d}s", callback_data=f"delay_{d}") for d in [0.3, 0.5, 1.0, 2.0]],
            [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="settings")],
        ])
        await query.edit_message_text(
            f"{EMOJI['clock']} <b>Choose Delay:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )

    elif data.startswith("delay_"):
        session.delay = float(data.split("_")[1])
        await query.edit_message_text(
            f"{EMOJI['yes']} Delay set to <b>{session.delay}s</b>",
            parse_mode=ParseMode.HTML,
        )

    elif data == "set_workers":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(str(w), callback_data=f"workers_{w}") for w in [1, 3, 5, 10]],
            [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="settings")],
        ])
        await query.edit_message_text(
            "🧵 <b>Choose Workers:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )

    elif data.startswith("workers_"):
        session.max_workers = int(data.split("_")[1])
        await query.edit_message_text(
            f"{EMOJI['yes']} Workers set to <b>{session.max_workers}</b>",
            parse_mode=ParseMode.HTML,
        )

    elif data == "reset_settings":
        session.username_length = 5
        session.char_set = "1234567890qwertyuiopasdfghjklzxcvbnm._"
        session.delay = 0.5
        session.max_workers = 5
        await query.edit_message_text(
            f"{EMOJI['yes']} <b>Settings reset to defaults.</b>",
            parse_mode=ParseMode.HTML,
        )

    elif data == "stats":
        text = (
            f"{EMOJI['stats']} <b>Session Statistics</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{EMOJI['check']} <b>Checked:</b> {session.checked}\n"
            f"{EMOJI['hit']} <b>Available:</b> {session.hits}\n"
            f"{EMOJI['taken']} <b>Taken:</b> {session.taken}\n"
            f"{EMOJI['rate']} <b>Rate Limited:</b> {session.rate_limited}\n"
            f"{EMOJI['error']} <b>Errors:</b> {session.errors}\n"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['stop']} Reset Stats", callback_data="reset_stats")],
            [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="back_start")],
        ])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "reset_stats":
        session.reset_stats()
        await query.edit_message_text(
            f"{EMOJI['yes']} <b>Stats reset.</b>",
            parse_mode=ParseMode.HTML,
        )

    elif data == "help":
        text = (
            f"📖 <b>Quick Help</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<code>/check username</code> — Check one\n"
            f"<code>/batch a,b,c</code> — Check multiple\n"
            f"<code>/generate</code> — Random generation\n"
            f"<code>/settings</code> — Configure\n"
            f"<code>/stats</code> — View stats\n"
            f"<code>/stop</code> — Stop running task"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="back_start")],
        ])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "back_start":
        text = (
            f"{EMOJI['fire']} <b>InstaUserCheckBot v2.0</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{EMOJI['check']} <b>Ready to check usernames!</b>\n\n"
            f"Use /check, /batch, or /generate to start."
        )
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{EMOJI['check']} Quick Check", switch_inline_query_current_chat=""),
                InlineKeyboardButton(f"{EMOJI['settings']} Settings", callback_data="settings"),
            ],
            [
                InlineKeyboardButton(f"{EMOJI['stats']} Stats", callback_data="stats"),
                InlineKeyboardButton("📖 Help", callback_data="help"),
            ],
        ])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


# ============================================================================
# MESSAGE HANDLER (for inline-style checks)
# ============================================================================

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages as username checks."""
    text = update.message.text.strip()
    if not text or " " in text or len(text) > 30:
        return  # ignore multi-word or long messages

    # Treat as a username check
    session = get_session(update.effective_user.id)
    username = text.lower()

    msg = await update.message.reply_text(
        f"{EMOJI['clock']} Checking <code>@{username}</code>...",
        parse_mode=ParseMode.HTML,
    )

    status, _ = await asyncio.to_thread(client.check, username, session.delay)
    session.record(status, username)

    if status == AVAILABLE:
        result = (
            f"{EMOJI['hit']} <b>AVAILABLE!</b>\n"
            f"{EMOJI['user']} <code>@{username}</code>\n"
            f"{EMOJI['hit']} Hits: {session.hits}"
        )
    elif status == TAKEN:
        result = f"{EMOJI['taken']} <code>@{username}</code> is taken."
    elif status == RATE_LIMITED:
        result = f"{EMOJI['rate']} Rate limited. Try later."
    else:
        result = f"{EMOJI['error']} Error checking <code>@{username}</code>."

    await msg.edit_text(result, parse_mode=ParseMode.HTML)


# ============================================================================
# BOT STARTUP
# ============================================================================

def run_bot(token: str):
    """Start the Telegram bot."""
    global client

    # Initialize Instagram client
    proxy_mgr = ProxyManager()
    client = InstagramClient(
        user_agents=[
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ],
        proxy_manager=proxy_mgr,
    )

    # Build application
    app = Application.builder().token(token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("batch", cmd_batch))
    app.add_handler(CommandHandler("generate", cmd_generate))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("settings", cmd_settings))

    # Callback handler
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Text handler (for quick username checks)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print(f"{GRN}🤖 InstaUserCheckBot started!{RST}")
    app.run_polling(drop_pending_updates=True)
