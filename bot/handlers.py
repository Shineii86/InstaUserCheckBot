"""
InstaUserCheckBot — interactive Instagram username checker.
v3.0 — Full UI/UX overhaul with short callback_data, unified renderers,
        inline queries, Web App, pattern templates, word combos, and robust error handling.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultArticle, InputTextMessageContent,
    WebAppInfo, MenuButtonWebApp,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest

from checker.instagram import InstagramClient, AVAILABLE, TAKEN, RATE_LIMITED, ERROR
from checker.proxy import ProxyManager
from checker.generator import UsernameGenerator


# ── Constants ──
VERSION = "3.0"
DIVIDER = "─" * 26
THICK_DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━"
THIN_DIVIDER = "· · · · · · · · · · · · · ·"
BOT_USERNAME = "InstaUserCheckBot"
BOT_AUTHOR = "@Shineii86"
WEBAPP_URL = "https://shineii86.github.io/InstaUserCheckBot/webapp/index.html"
MAX_HISTORY = 20
START_TIME = time.time()


# ── Emoji Map ──
E = {
    "check": "🔍", "hit": "✅", "taken": "❌", "invalid": "🚫",
    "rate": "⚠️", "error": "💥", "stats": "📊", "settings": "⚙️",
    "stop": "🛑", "start": "🚀", "user": "👤", "id": "🆔",
    "pack": "📦", "clock": "🕐", "fire": "🔥", "star": "⭐",
    "back": "🔙", "yes": "✅", "no": "❌", "instagram": "📸",
    "link": "🔗", "magic": "✨", "target": "🎯", "wave": "👋",
    "bulb": "💡", "gear": "⚙️", "chart": "📈", "trophy": "🏆",
    "dart": "🎯", "sparkle": "✨", "pin": "📌",
    "shield": "🛡️", "zap": "⚡", "memo": "📝", "globe": "🌐",
    "ping": "🏓", "about": "ℹ️", "history": "📜", "copy": "📋",
    "heart": "❤️", "rocket": "🚀", "diamond": "💎",
    "time": "⏰", "refresh": "🔄", "export": "📤", "folder": "📁",
    "lightning": "⚡", "rainbow": "🌈", "party": "🎉",
    "eyes": "👀", "brain": "🧠", "magnifier": "🔎", "crystal": "🔮",
}


# ── Helpers ──
def progress_bar(current: int, total: int, length: int = 10) -> str:
    if total == 0:
        return "░" * length
    filled = int(length * current / total)
    return "█" * filled + "░" * (length - filled)


def format_uptime(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


def format_time_ago(dt: datetime) -> str:
    now = datetime.now(timezone.utc)
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    else:
        return f"{int(seconds // 86400)}d ago"


def safe_edit(func):
    """Decorator to silently handle 'message is not modified' errors."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
    return wrapper


# ── User Session ──
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
        self.char_set_label = "default"
        self.delay = 0.5
        self.max_workers = 5
        self.generation_mode = "random"
        self.pattern = ""

        # History
        self.history: list = []  # [{username, status, time}]

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

        # Add to history
        self.history.insert(0, {"username": username, "status": status, "time": datetime.now(timezone.utc)})
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[:MAX_HISTORY]

    def reset_stats(self):
        self.checked = 0
        self.hits = 0
        self.taken = 0
        self.rate_limited = 0
        self.errors = 0
        self.available = []

    @property
    def hit_rate(self) -> float:
        return (100 * self.hits / self.checked) if self.checked > 0 else 0.0


# ── Global State ──
sessions: dict[int, UserSession] = {}
client: Optional[InstagramClient] = None
generator: Optional[UsernameGenerator] = None


def get_session(user_id: int) -> UserSession:
    if user_id not in sessions:
        sessions[user_id] = UserSession()
    return sessions[user_id]


# ── Status Helpers ──
STATUS_EMOJI = {
    AVAILABLE: "✅", TAKEN: "❌", RATE_LIMITED: "⚠️", ERROR: "💥",
}

STATUS_LABEL = {
    AVAILABLE: "Available", TAKEN: "Taken", RATE_LIMITED: "Rate Limited", ERROR: "Error",
}


# ============================================================================
# UNIFIED RENDERERS
# ============================================================================

def render_start(user) -> tuple[str, InlineKeyboardMarkup]:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    elif 17 <= hour < 21:
        greeting = "Good evening"
    else:
        greeting = "Hey"
    text = (
        f"{E['wave']} <b>{greeting}, {user.first_name}!</b>\n\n"
        f"{E['instagram']} <b>{BOT_USERNAME}</b> <i>v{VERSION}</i>\n"
        f"{THICK_DIVIDER}\n\n"
        f"{E['magnifier']} <b>Instagram Username Checker</b>\n"
        f"{E['lightning']} Fast  {E['shield']} Reliable  {E['sparkle']} Free\n\n"
        f"<b>{E['pin']} Quick Actions:</b>\n\n"
        f"  {E['check']}  <b>/check</b> <code>username</code> — Check one name\n"
        f"  {E['pack']}  <b>/batch</b> <code>a,b,c</code> — Check multiple\n"
        f"  {E['magic']}  <b>/generate</b> <code>[N]</code> — Random names\n"
        f"  {E['crystal']}  <b>/pattern</b> <code>tmpl</code> — Pattern templates\n"
        f"  {E['settings']}  <b>/settings</b> — Tune your preferences\n"
        f"  {E['stats']}  <b>/stats</b> — View session stats\n"
        f"  {E['history']}  <b>/history</b> — Recent check log\n"
        f"  {E['ping']}  <b>/ping</b> — Bot status & uptime\n"
        f"  {E['bulb']}  <b>/help</b> — Full guide & rules\n\n"
        f"{THIN_DIVIDER}\n"
        f"{E['sparkle']} <i>Just type a username to quick-check it!</i>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['check']} Quick Check", switch_inline_query_current_chat=""),
         InlineKeyboardButton(f"{E['magic']} Generate", callback_data="qg")],
        [InlineKeyboardButton(f"🌐 Open Checker", web_app=WebAppInfo(url=WEBAPP_URL)),
         InlineKeyboardButton(f"{E['settings']} Settings", callback_data="s")],
        [InlineKeyboardButton(f"{E['stats']} Stats", callback_data="st"),
         InlineKeyboardButton(f"{E['history']} History", callback_data="hi")],
        [InlineKeyboardButton(f"{E['bulb']} Help", callback_data="hp")],
    ])
    return text, kb


def render_help() -> tuple[str, InlineKeyboardMarkup]:
    text = (
        f"{E['bulb']} <b>How to Use {BOT_USERNAME}</b>\n{THICK_DIVIDER}\n\n"
        f"<b>{E['check']} /check</b> <code>username</code> — Check one\n"
        f"<b>{E['pack']} /batch</b> <code>a,b,c</code> — Check multiple\n"
        f"<b>{E['magic']} /generate</b> <code>[N]</code> — Random names\n"
        f"<b>{E['crystal']} /pattern</b> <code>tmpl</code> — Pattern templates\n"
        f"<b>{E['settings']} /settings</b> — Configure\n"
        f"<b>{E['stats']} /stats</b> — View stats\n"
        f"<b>{E['history']} /history</b> — Recent checks\n"
        f"<b>{E['ping']} /ping</b> — Bot status\n"
        f"<b>{E['about']} /about</b> — Bot info\n"
        f"<b>{E['stop']} /stop</b> — Stop operation\n\n"
        f"{E['pin']} <b>Instagram Username Rules:</b>\n"
        f"  Up to 30 chars • a-z, 0-9, ., _ • no spaces\n\n"
        f"{E['crystal']} <b>Pattern Syntax:</b>\n"
        f"  <code>?</code>=letter <code>#</code>=digit <code>!</code>=alnum"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"{E['back']} Back", callback_data="b")]])
    return text, kb


def render_settings(session: UserSession) -> tuple[str, InlineKeyboardMarkup]:
    text = (
        f"{E['settings']} <b>Settings</b>\n{THICK_DIVIDER}\n\n"
        f"  📏 <b>Length:</b> {session.username_length}\n"
        f"  🔤 <b>Chars:</b> <code>{session.char_set_label}</code>\n"
        f"  {E['clock']} <b>Delay:</b> {session.delay}s\n"
        f"  🧵 <b>Workers:</b> {session.max_workers}\n"
        f"  {E['gear']} <b>Gen Mode:</b> {session.generation_mode}\n"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📏 {session.username_length} chars", callback_data="sl"),
         InlineKeyboardButton(f"🔤 {session.char_set_label}", callback_data="sc")],
        [InlineKeyboardButton(f"{E['clock']} {session.delay}s delay", callback_data="sd"),
         InlineKeyboardButton(f"🧵 {session.max_workers} workers", callback_data="sw")],
        [InlineKeyboardButton(f"{E['gear']} {session.generation_mode}", callback_data="sg"),
         InlineKeyboardButton(f"{E['crystal']} pattern", callback_data="pm")],
        [InlineKeyboardButton(f"{E['refresh']} Reset All", callback_data="crs"),
         InlineKeyboardButton(f"{E['back']} Back", callback_data="b")],
    ])
    return text, kb


def render_stats(session: UserSession) -> tuple[str, InlineKeyboardMarkup]:
    hit_bar = progress_bar(session.hits, max(session.checked, 1), 12)
    text = (
        f"{E['stats']} <b>Session Statistics</b>\n{THICK_DIVIDER}\n\n"
        f"  {E['magnifier']} Checked: <b>{session.checked}</b>\n"
        f"  {E['hit']} Available: <b>{session.hits}</b>\n"
        f"  {E['taken']} Taken: <b>{session.taken}</b>\n"
        f"  {E['rate']} Rate Limit: <b>{session.rate_limited}</b>\n"
        f"  {E['error']} Errors: <b>{session.errors}</b>\n\n"
        f"  {E['target']} <b>Hit Rate:</b>\n    <code>{hit_bar}</code> {session.hit_rate:.1f}%\n"
    )
    if session.available:
        recent = session.available[-5:]
        hit_list = "\n".join(f"    {E['hit']} <code>@{u}</code>" for u in recent)
        text += f"\n  {E['star']} <b>Recent Hits:</b>\n{hit_list}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['export']} Export", callback_data="ex"),
         InlineKeyboardButton(f"{E['history']} History", callback_data="hi")],
        [InlineKeyboardButton(f"{E['refresh']} Reset", callback_data="crst"),
         InlineKeyboardButton(f"{E['back']} Back", callback_data="b")],
    ])
    return text, kb


def render_history(session: UserSession) -> tuple[str, InlineKeyboardMarkup]:
    if not session.history:
        text = f"{E['history']} <b>Check History</b>\n{THICK_DIVIDER}\n\n<i>No checks yet.</i>"
    else:
        lines = []
        for h in session.history[:15]:
            emoji = STATUS_EMOJI.get(h["status"], "❓")
            label = STATUS_LABEL.get(h["status"], "Unknown")
            ago = format_time_ago(h["time"])
            lines.append(f"  {emoji} <code>@{h['username']}</code> — {label} · {ago}")
        text = (
            f"{E['history']} <b>Check History</b>\n{THICK_DIVIDER}\n\n"
            + "\n".join(lines)
        )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['export']} Export", callback_data="ex"),
         InlineKeyboardButton(f"{E['back']} Back", callback_data="b")],
    ])
    return text, kb


def render_export(session: UserSession) -> tuple[str, InlineKeyboardMarkup]:
    if not session.available:
        text = f"{E['export']} <b>Export Hits</b>\n{THICK_DIVIDER}\n\n<i>No available names to export.</i>"
    else:
        hit_list = "\n".join(f"  {E['hit']} <code>@{u}</code>" for u in session.available)
        text = (
            f"{E['export']} <b>Export Hits</b>\n{THICK_DIVIDER}\n\n"
            f"{hit_list}\n\n"
            f"  {E['memo']} <b>Total:</b> {len(session.available)} available names"
        )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"{E['back']} Back", callback_data="b")]])
    return text, kb


def _render_check_result(username: str, status: str, session: UserSession) -> tuple[str, InlineKeyboardMarkup]:
    """Shared renderer for check results (used by /check, quick check, retry)."""
    emoji = STATUS_EMOJI.get(status, "❓")
    label = STATUS_LABEL.get(status, "Unknown")

    if status == AVAILABLE:
        text = (
            f"{E['party']} <b>AVAILABLE!</b> {E['sparkle']}\n{THICK_DIVIDER}\n"
            f"  {E['user']} <code>@{username}</code>\n"
            f"  {E['link']} <a href=\"https://instagram.com/{username}\">instagram.com/{username}</a>\n\n"
            f"  {E['bulb']} <i>Claim it now!</i>"
        )
    elif status == TAKEN:
        text = (
            f"{E['taken']} <b>Taken</b>\n{DIVIDER}\n"
            f"<code>@{username}</code> is already registered.\n\n"
            f"{E['bulb']} <i>Try /generate to find available names!</i>"
        )
    elif status == RATE_LIMITED:
        text = (
            f"{E['rate']} <b>Rate Limited</b>\n{DIVIDER}\n"
            f"Instagram is blocking requests.\n"
            f"Try again later or use a proxy."
        )
    else:
        text = (
            f"{E['error']} <b>Error</b>\n{DIVIDER}\n"
            f"Could not check <code>@{username}</code>.\n"
            f"Tap retry to try again."
        )

    buttons = []
    if status == AVAILABLE:
        buttons.append(InlineKeyboardButton(f"📱 Open", url=f"https://instagram.com/{username}"))
        buttons.append(InlineKeyboardButton(f"📋 Copy", callback_data=f"c:{username}"))
    elif status == TAKEN:
        buttons.append(InlineKeyboardButton(f"📱 View", url=f"https://instagram.com/{username}"))
    elif status in (RATE_LIMITED, ERROR):
        buttons.append(InlineKeyboardButton(f"🔄 Retry", callback_data=f"r:{username}"))

    kb_rows = [buttons] if buttons else []
    kb_rows.append([
        InlineKeyboardButton(f"{E['check']} Check Another", switch_inline_query_current_chat=""),
        InlineKeyboardButton(f"{E['magic']} Generate", callback_data="qg"),
    ])
    kb = InlineKeyboardMarkup(kb_rows)
    return text, kb


# ============================================================================
# GENERATION ENGINE
# ============================================================================

async def _run_generation(update_or_query, session: UserSession, count: int = 20,
                          mode: str = "random", pattern: str = "", is_callback: bool = False):
    """Unified generation engine for /generate, /pattern, and callback-triggered generation."""
    session.running = True
    session.should_stop = False

    gen = UsernameGenerator(
        length=session.username_length,
        chars=session.char_set,
    )

    # Pick stream
    if pattern:
        error = UsernameGenerator.validate_pattern(pattern)
        if error:
            msg = update_or_query.message if is_callback else update_or_query.message
            await msg.reply_text(f"{E['error']} {error}", parse_mode=ParseMode.HTML)
            session.running = False
            return
        name_iter = gen.pattern_stream(pattern)
        mode_label = f"🔮 Pattern: <code>{pattern}</code>"
    elif mode == "word_combo":
        name_iter = gen.word_combo_stream()
        mode_label = "🧠 Word Combos"
    elif mode == "mixed":
        name_iter = gen.mixed_stream()
        mode_label = "🌈 Mixed"
    else:
        name_iter = gen.random_stream()
        mode_label = "🎲 Random"

    # Send initial message
    if is_callback:
        msg = await update_or_query.message.reply_text(
            f"{E['start']} <b>Generating & Checking</b>\n{THICK_DIVIDER}\n\n"
            f"  {E['gear']} Mode: {mode_label}\n"
            f"  {E['pack']} Count: <b>{count}</b>\n"
            f"  {E['clock']} Delay: <b>{session.delay}s</b>\n\n"
            f"<i>Starting...</i>",
            parse_mode=ParseMode.HTML,
        )
    else:
        msg = await update_or_query.message.reply_text(
            f"{E['start']} <b>Generating & Checking</b>\n{THICK_DIVIDER}\n\n"
            f"  {E['gear']} Mode: {mode_label}\n"
            f"  {E['pack']} Count: <b>{count}</b>\n\n"
            f"<i>Starting...</i>",
            parse_mode=ParseMode.HTML,
        )

    hits_list = []
    taken_count = 0
    rate_count = 0
    error_count = 0
    start_time = time.time()

    for i in range(count):
        if session.should_stop:
            break

        username = next(name_iter)
        status, _ = await asyncio.to_thread(client.check, username, session.delay)
        session.record(status, username)

        if status == AVAILABLE:
            hits_list.append(username)
        elif status == TAKEN:
            taken_count += 1
        elif status == RATE_LIMITED:
            rate_count += 1
        elif status == ERROR:
            error_count += 1

        # Auto-adjust delay on rate limits
        if client and client.consecutive_rate_limits >= 3:
            session.delay = min(session.delay + 0.5, 5.0)

        # Update progress every 5 checks
        if (i + 1) % 5 == 0 or i == count - 1:
            elapsed = time.time() - start_time
            speed = (i + 1) / elapsed if elapsed > 0 else 0
            try:
                await msg.edit_text(
                    f"{E['start']} <b>Generating & Checking</b>\n{THICK_DIVIDER}\n\n"
                    f"  {E['gear']} Mode: {mode_label}\n"
                    f"  {E['pack']} Progress: <b>{i + 1}/{count}</b>\n"
                    f"  {E['hit']} Hits: <b>{len(hits_list)}</b>\n"
                    f"  {E['taken']} Taken: <b>{taken_count}</b>\n\n"
                    f"  {E['zap']} Speed: <b>{speed:.1f}/sec</b>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    session.running = False
    elapsed = time.time() - start_time

    # Final report
    hit_display = "\n".join(f"  {E['hit']} <code>@{u}</code>" for u in hits_list) or "  <i>None found</i>"
    text = (
        f"{E['trophy']} <b>{'Pattern' if pattern else 'Generation'} Complete</b>\n{THICK_DIVIDER}\n\n"
        f"  {E['gear']} Mode: {mode_label}\n"
        f"  {E['magnifier']} Checked: <b>{count}</b>\n"
        f"  {E['hit']} Available: <b>{len(hits_list)}</b>\n"
        f"  {E['taken']} Taken: <b>{taken_count}</b>\n"
        f"  {E['rate']} Rate Limit: <b>{rate_count}</b>\n"
        f"  {E['error']} Errors: <b>{error_count}</b>\n\n"
        f"  {E['clock']} Time: <b>{elapsed:.1f}s</b> · {E['zap']} Speed: <b>{count / elapsed:.1f}/sec</b>\n\n"
        f"{E['star']} <b>Available Names:</b>\n{hit_display}"
    )

    if session.should_stop:
        text = f"{E['stop']} <b>Stopped!</b>\n\n" + text

    buttons = []
    if hits_list:
        buttons.append(InlineKeyboardButton(f"{E['export']} Export Hits", callback_data="ex"))
    buttons.append(InlineKeyboardButton(f"{E['magic']} Generate More", callback_data="qg"))
    kb = InlineKeyboardMarkup([
        buttons,
        [InlineKeyboardButton(f"{E['stats']} Stats", callback_data="st"),
         InlineKeyboardButton(f"{E['back']} Home", callback_data="b")],
    ])

    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text, kb = render_start(update.effective_user)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text, kb = render_help()
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            f"{E['error']} Usage: <code>/check username</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    username = ctx.args[0].strip().lower().lstrip("@")
    session = get_session(update.effective_user.id)

    msg = await update.message.reply_text(
        f"{E['clock']} Checking <code>@{username}</code>...\n"
        f"<i>Scanning instagram.com/{username}</i>",
        parse_mode=ParseMode.HTML,
    )

    status, _ = await asyncio.to_thread(client.check, username, session.delay)
    session.record(status, username)
    text, kb = _render_check_result(username, status, session)
    await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_batch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            f"{E['error']} Usage: <code>/batch user1,user2,user3</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    raw = " ".join(ctx.args)
    usernames = [u.strip().lower().lstrip("@") for u in raw.replace("\n", ",").replace(" ", ",").split(",") if u.strip()]

    if not usernames:
        await update.message.reply_text(f"{E['error']} No usernames provided.")
        return

    if len(usernames) > 200:
        await update.message.reply_text(f"{E['error']} Max 200 per batch (got {len(usernames)}).")
        return

    session = get_session(update.effective_user.id)
    session.running = True
    session.should_stop = False

    msg = await update.message.reply_text(
        f"{E['start']} <b>Batch Check Started</b>\n{THICK_DIVIDER}\n\n"
        f"  {E['pack']} Usernames: <b>{len(usernames)}</b>\n"
        f"  {E['clock']} Delay: <b>{session.delay}s</b>\n\n"
        f"<i>Checking...</i>",
        parse_mode=ParseMode.HTML,
    )

    hits_list = []
    taken_count = 0
    rate_count = 0
    error_count = 0
    start_time = time.time()

    for i, username in enumerate(usernames):
        if session.should_stop:
            break

        status, _ = await asyncio.to_thread(client.check, username, session.delay)
        session.record(status, username)

        if status == AVAILABLE:
            hits_list.append(username)
        elif status == TAKEN:
            taken_count += 1
        elif status == RATE_LIMITED:
            rate_count += 1
        elif status == ERROR:
            error_count += 1

        # Update progress every 5 checks
        if (i + 1) % 5 == 0 or i == len(usernames) - 1:
            elapsed = time.time() - start_time
            speed = (i + 1) / elapsed if elapsed > 0 else 0
            try:
                await msg.edit_text(
                    f"{E['start']} <b>Batch Check Running</b>\n{THICK_DIVIDER}\n\n"
                    f"  {E['pack']} Progress: <b>{i + 1}/{len(usernames)}</b>\n"
                    f"  {E['hit']} Hits: <b>{len(hits_list)}</b>\n"
                    f"  {E['taken']} Taken: <b>{taken_count}</b>\n"
                    f"  {E['rate']} Rate Limit: <b>{rate_count}</b>\n\n"
                    f"  {E['zap']} Speed: <b>{speed:.1f}/sec</b>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    session.running = False
    elapsed = time.time() - start_time

    hit_display = "\n".join(f"  {E['hit']} <code>@{u}</code>" for u in hits_list) or "  <i>None found</i>"
    text = (
        f"{E['trophy']} <b>Batch Check Complete</b>\n{THICK_DIVIDER}\n\n"
        f"  {E['pack']} Total: <b>{len(usernames)}</b>\n"
        f"  {E['hit']} Available: <b>{len(hits_list)}</b>\n"
        f"  {E['taken']} Taken: <b>{taken_count}</b>\n"
        f"  {E['rate']} Rate Limit: <b>{rate_count}</b>\n"
        f"  {E['error']} Errors: <b>{error_count}</b>\n\n"
        f"  {E['clock']} Time: <b>{elapsed:.1f}s</b> · {E['zap']} Speed: <b>{len(usernames) / elapsed:.1f}/sec</b>\n\n"
        f"{E['star']} <b>Available Names:</b>\n{hit_display}"
    )

    if session.should_stop:
        text = f"{E['stop']} <b>Stopped!</b>\n\n" + text

    buttons = []
    if hits_list:
        buttons.append(InlineKeyboardButton(f"{E['export']} Export", callback_data="ex"))
    buttons.append(InlineKeyboardButton(f"{E['check']} Check Again", switch_inline_query_current_chat=""))
    kb = InlineKeyboardMarkup([
        buttons,
        [InlineKeyboardButton(f"{E['magic']} Generate", callback_data="qg"),
         InlineKeyboardButton(f"{E['back']} Home", callback_data="b")],
    ])

    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass


async def cmd_generate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    count = 20
    if ctx.args:
        try:
            count = min(int(ctx.args[0]), 100)
        except ValueError:
            pass
    await _run_generation(update, session, count=count, mode=session.generation_mode)


async def cmd_pattern(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            f"{E['crystal']} <b>Pattern Templates</b>\n{THICK_DIVIDER}\n\n"
            f"Generate usernames from a pattern.\n\n"
            f"<b>Syntax:</b>\n"
            f"  <code>?</code> = random letter (a-z)\n"
            f"  <code>#</code> = random digit (0-9)\n"
            f"  <code>!</code> = letter or digit\n"
            f"  <code>_</code> = literal underscore\n"
            f"  Other = literal character\n\n"
            f"<b>Examples:</b>\n"
            f"  <code>/pattern user_????</code>\n"
            f"  <code>/pattern test_##</code>\n"
            f"  <code>/pattern my_!_!_name</code>\n"
            f"  <code>/pattern pro_####</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    pattern = ctx.args[0].strip()
    session = get_session(update.effective_user.id)
    count = 20
    if len(ctx.args) > 1:
        try:
            count = min(int(ctx.args[1]), 100)
        except ValueError:
            pass
    await _run_generation(update, session, count=count, pattern=pattern)


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    text, kb = render_stats(session)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    text, kb = render_history(session)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_ping(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uptime = format_uptime(time.time() - START_TIME)
    session = get_session(update.effective_user.id)
    text = (
        f"{E['ping']} <b>Pong!</b>\n{THICK_DIVIDER}\n\n"
        f"  {E['clock']} <b>Uptime:</b> {uptime}\n"
        f"  {E['gear']} <b>Version:</b> v{VERSION}\n"
        f"  {E['magnifier']} <b>Your Checks:</b> {session.checked}\n"
        f"  {E['hit']} <b>Your Hits:</b> {session.hits}\n\n"
        f"  {E['sparkle']} <i>All systems operational!</i>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"{E['back']} Back", callback_data="b")]])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{E['instagram']} <b>{BOT_USERNAME}</b>\n{THICK_DIVIDER}\n\n"
        f"  {E['gear']} <b>Version:</b> v{VERSION}\n"
        f"  {E['user']} <b>Author:</b> {BOT_AUTHOR}\n"
        f"  {E['link']} <b>Source:</b> <a href=\"https://github.com/Shineii86/InstaUserCheckBot\">GitHub</a>\n\n"
        f"  {E['magnifier']} <b>Features:</b>\n"
        f"  · Single, batch, & generation modes\n"
        f"  · Pattern templates\n"
        f"  · Word combo generation\n"
        f"  · Proxy rotation\n"
        f"  · Multi-threaded checking\n\n"
        f"  {E['heart']} <i>Star the repo if you found it useful!</i>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ GitHub", url="https://github.com/Shineii86/InstaUserCheckBot"),
         InlineKeyboardButton(f"{E['back']} Back", callback_data="b")],
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    text, kb = render_settings(session)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    if session.running:
        session.should_stop = True
        await update.message.reply_text(
            f"{E['stop']} <b>Stopping...</b> Will finish current check shortly.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            f"{E['no']} Nothing is running.",
            parse_mode=ParseMode.HTML,
        )


# ============================================================================
# CALLBACK HANDLER
# ============================================================================

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session(query.from_user.id)
    data = query.data

    # ── Navigation ──
    if data == "b":
        text, kb = render_start(query.from_user)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "hp":
        text, kb = render_help()
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "s":
        text, kb = render_settings(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "st":
        text, kb = render_stats(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "hi":
        text, kb = render_history(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "ex":
        text, kb = render_export(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    # ── Quick Generate ──
    elif data == "qg":
        await query.answer("✨ Generating...")
        await _run_generation(query, session, count=20, mode=session.generation_mode, is_callback=True)

    # ── Settings ──
    elif data == "sl":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(str(i), callback_data=f"l:{i}") for i in [4, 5, 6, 7, 8]],
            [InlineKeyboardButton(str(i), callback_data=f"l:{i}") for i in [10, 12, 15]],
            [InlineKeyboardButton(f"{E['back']} Back", callback_data="s")],
        ])
        await safe_edit(query.edit_message_text)("📏 <b>Username Length:</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data.startswith("l:"):
        session.username_length = int(data[2:])
        await query.answer(f"📏 Length: {session.username_length}")
        text, kb = render_settings(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "sc":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("a-z 0-9 ._", callback_data="ch:d"),
             InlineKeyboardButton("a-z only", callback_data="ch:a")],
            [InlineKeyboardButton("a-z 0-9", callback_data="ch:an"),
             InlineKeyboardButton("0-9 only", callback_data="ch:num")],
            [InlineKeyboardButton(f"{E['back']} Back", callback_data="s")],
        ])
        await safe_edit(query.edit_message_text)("🔤 <b>Character Set:</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data.startswith("ch:"):
        sets = {
            "d": ("1234567890qwertyuiopasdfghjklzxcvbnm._", "default"),
            "a": ("qwertyuiopasdfghjklzxcvbnm", "alpha"),
            "an": ("1234567890qwertyuiopasdfghjklzxcvbnm", "alnum"),
            "num": ("1234567890", "digits"),
        }
        chars, label = sets.get(data[3:], sets["d"])
        session.char_set = chars
        session.char_set_label = label
        await query.answer(f"🔤 Chars: {label}")
        text, kb = render_settings(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "sd":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{d}s", callback_data=f"d:{d}") for d in [0.3, 0.5, 1.0, 2.0]],
            [InlineKeyboardButton(f"{E['back']} Back", callback_data="s")],
        ])
        await safe_edit(query.edit_message_text)(f"{E['clock']} <b>Delay:</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data.startswith("d:"):
        session.delay = float(data[2:])
        await query.answer(f"{E['clock']} Delay: {session.delay}s")
        text, kb = render_settings(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "sw":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(str(w), callback_data=f"w:{w}") for w in [1, 3, 5, 10]],
            [InlineKeyboardButton(f"{E['back']} Back", callback_data="s")],
        ])
        await safe_edit(query.edit_message_text)("🧵 <b>Workers:</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data.startswith("w:"):
        session.max_workers = int(data[2:])
        await query.answer(f"🧵 Workers: {session.max_workers}")
        text, kb = render_settings(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "sg":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Random", callback_data="gm:random"),
             InlineKeyboardButton("🧠 Combos", callback_data="gm:word_combo")],
            [InlineKeyboardButton("🌈 Mixed", callback_data="gm:mixed")],
            [InlineKeyboardButton(f"{E['back']} Back", callback_data="s")],
        ])
        await safe_edit(query.edit_message_text)(f"{E['gear']} <b>Generation Mode:</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data.startswith("gm:"):
        session.generation_mode = data[3:]
        await query.answer(f"{E['gear']} Mode: {session.generation_mode}")
        text, kb = render_settings(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "pm":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("user_????", callback_data="pt:u4"),
             InlineKeyboardButton("name_##_ab", callback_data="pt:n2a")],
            [InlineKeyboardButton("my_!_!_!_tag", callback_data="pt:m3t"),
             InlineKeyboardButton("pro_####", callback_data="pt:p4")],
            [InlineKeyboardButton(f"{E['back']} Back", callback_data="s")],
        ])
        await safe_edit(query.edit_message_text)(
            f"{E['crystal']} <b>Pattern Templates:</b>\n\nTap one to generate:",
            parse_mode=ParseMode.HTML, reply_markup=kb,
        )

    elif data.startswith("pt:"):
        tpl_map = {"u4": "user_????", "n2a": "name_##_ab", "m3t": "my_!_!_!_tag", "p4": "pro_####"}
        pattern = tpl_map.get(data[3:], "user_????")
        await query.answer(f"🔮 Pattern: {pattern}")
        await _run_generation(query, session, count=20, pattern=pattern, is_callback=True)

    # ── Reset ──
    elif data == "crs":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{E['yes']} Reset", callback_data="rs"),
             InlineKeyboardButton(f"{E['no']} Cancel", callback_data="s")],
        ])
        await safe_edit(query.edit_message_text)(
            f"{E['refresh']} <b>Reset all settings to defaults?</b>",
            parse_mode=ParseMode.HTML, reply_markup=kb,
        )

    elif data == "rs":
        session.username_length = 5
        session.char_set = "1234567890qwertyuiopasdfghjklzxcvbnm._"
        session.char_set_label = "default"
        session.delay = 0.5
        session.max_workers = 5
        session.generation_mode = "random"
        session.pattern = ""
        await query.answer("✅ Settings reset")
        text, kb = render_settings(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "crst":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{E['yes']} Reset", callback_data="rst"),
             InlineKeyboardButton(f"{E['no']} Cancel", callback_data="st")],
        ])
        await safe_edit(query.edit_message_text)(
            f"{E['refresh']} <b>Reset all statistics?</b>",
            parse_mode=ParseMode.HTML, reply_markup=kb,
        )

    elif data == "rst":
        session.reset_stats()
        await query.answer("✅ Stats reset")
        text, kb = render_stats(session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    # ── Copy Username ──
    elif data.startswith("c:"):
        username = data[2:]
        await query.answer(f"📋 @{username}", show_alert=True)

    # ── Retry ──
    elif data.startswith("r:"):
        username = data[2:]
        await query.answer("🔄 Retrying...")
        status, _ = await asyncio.to_thread(client.check, username, session.delay)
        session.record(status, username)
        text, kb = _render_check_result(username, status, session)
        await safe_edit(query.edit_message_text)(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    # ── Stop ──
    elif data == "x":
        session.should_stop = True
        await query.answer("🛑 Stopping...")

    # ── Inline query chosen ──
    elif data.startswith("chosen_"):
        pass  # handled by chosen_inline_result


# ============================================================================
# INLINE QUERY HANDLER
# ============================================================================

async def handle_inline_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower().lstrip("@")
    if not query or len(query) < 2:
        return

    results = []

    # Available result
    results.append(
        InlineQueryResultArticle(
            id=f"av_{query}",
            title=f"✅ @{query} might be available",
            description=f"Tap to send • instagram.com/{query}",
            input_message_content=InputTextMessageContent(
                f"{E['party']} <b>AVAILABLE!</b> {E['sparkle']}\n{THICK_DIVIDER}\n"
                f"  {E['user']} <code>@{query}</code>\n"
                f"  {E['link']} <a href=\"https://instagram.com/{query}\">instagram.com/{query}</a>\n\n"
                f"  {E['bulb']} <i>Claim it now!</i>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            ),
            thumbnail_url="https://img.icons8.com/color/48/checkmark.png",
        )
    )

    # Taken result
    results.append(
        InlineQueryResultArticle(
            id=f"tk_{query}",
            title=f"❌ @{query} is taken",
            description="Already registered on Instagram",
            input_message_content=InputTextMessageContent(
                f"{E['taken']} <b>Taken</b>\n{DIVIDER}\n<code>@{query}</code> is already registered.\n\n"
                f"{E['bulb']} <i>Try /generate to find available names!</i>",
                parse_mode=ParseMode.HTML,
            ),
            thumbnail_url="https://img.icons8.com/color/48/cancel.png",
        )
    )

    await update.inline_query.answer(results, cache_time=0, is_personal=True)


async def handle_chosen_inline(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle when user selects an inline result."""
    result_id = update.chosen_inline_result.result_id
    query = update.chosen_inline_result.query.strip().lower()
    session = get_session(update.chosen_inline_result.from_user.id)

    if result_id.startswith("av_"):
        status, _ = await asyncio.to_thread(client.check, query, session.delay)
        session.record(status, query)


# ============================================================================
# WEB APP DATA HANDLER
# ============================================================================

async def handle_webapp_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle data sent from the Telegram Web App."""
    try:
        import json
        data = json.loads(update.message.web_app_data.data)
    except (ValueError, TypeError):
        await update.message.reply_text(f"{E['error']} Invalid data from web app.", parse_mode=ParseMode.HTML)
        return

    action = data.get("action")
    session = get_session(update.effective_user.id)

    if action == "check":
        username = data.get("username", "").strip().lower()
        status = data.get("status", "error")
        session.record(status, username)
        text, kb = _render_check_result(username, status, session)
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif action in ("batch_result", "generate_result", "pattern_result"):
        total = data.get("total", 0)
        hits = data.get("hits", 0)
        taken = data.get("taken", 0)
        errors = data.get("errors", 0)
        elapsed = data.get("elapsed", "0")
        available_list = data.get("available", [])
        mode = data.get("mode", "")
        pattern = data.get("pattern", "")

        for _ in range(hits):
            session.record(AVAILABLE, "")
        for _ in range(taken):
            session.record(TAKEN, "")
        for _ in range(errors):
            session.record(ERROR, "")

        title = "Pattern" if pattern else ("Generation" if mode else "Batch")
        text = (
            f"{E['trophy']} <b>{title} Complete</b>\n{THICK_DIVIDER}\n\n"
            f"  {E['magnifier']} Checked: <b>{total}</b>\n"
            f"  {E['hit']} Available: <b>{hits}</b>\n"
            f"  {E['taken']} Taken: <b>{taken}</b>\n"
            f"  {E['error']} Errors: <b>{errors}</b>\n\n"
            f"  {E['clock']} Time: <b>{elapsed}s</b>\n"
        )
        if available_list:
            hit_list = "\n".join(f"    {E['hit']} <code>@{u}</code>" for u in available_list[:10])
            text += f"\n  {E['star']} <b>Available Names:</b>\n{hit_list}"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{E['check']} Check More", switch_inline_query_current_chat=""),
             InlineKeyboardButton(f"{E['magic']} Generate", callback_data="qg")],
            [InlineKeyboardButton(f"{E['stats']} Stats", callback_data="st"),
             InlineKeyboardButton(f"{E['back']} Home", callback_data="b")],
        ])
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    else:
        await update.message.reply_text(f"{E['bulb']} Web app data received.", parse_mode=ParseMode.HTML)


# ============================================================================
# MESSAGE HANDLER — quick check by typing a username
# ============================================================================

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lstrip("@").lower()
    if len(text) < 1 or len(text) > 30:
        return
    if " " in text:
        return

    session = get_session(update.effective_user.id)
    username = text

    msg = await update.message.reply_text(
        f"{E['clock']} Checking <code>@{username}</code>...",
        parse_mode=ParseMode.HTML,
    )

    status, _ = await asyncio.to_thread(client.check, username, session.delay)
    session.record(status, username)
    text, kb = _render_check_result(username, status, session)
    await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


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
    app.add_handler(CommandHandler("pattern", cmd_pattern))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("cancel", cmd_stop))

    # Callbacks, inline queries & messages
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(InlineQueryHandler(handle_inline_query))
    app.add_handler(ChosenInlineResultHandler(handle_chosen_inline))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set menu button to open web app (if URL configured)
    async def post_init(app):
        if WEBAPP_URL and WEBAPP_URL != "https://your-domain.com":
            try:
                await app.bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(text="🔍 Checker", web_app=WebAppInfo(url=WEBAPP_URL))
                )
            except Exception:
                pass
    app.post_init = post_init

    print(f"🤖 {BOT_USERNAME} v{VERSION} is running...")
    print("Press Ctrl+C to stop.")

    # Detect Jupyter/Colab
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        is_notebook = shell in ("ZMQInteractiveShell", "Shell")
    except (ImportError, NameError, AttributeError):
        is_notebook = False

    if not is_notebook:
        app.run_polling(drop_pending_updates=True)
    else:
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "nest_asyncio"])
            import nest_asyncio
            nest_asyncio.apply()
        app.run_polling(drop_pending_updates=True)
