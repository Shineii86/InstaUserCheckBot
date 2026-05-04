#!/usr/bin/env python3
"""
InstaUserCheckBot — Telegram Bot Entry Point.

Usage:
    python run_bot.py                    # Interactive (prompts for token)
    python run_bot.py --token YOUR_TOKEN # From CLI arg
    TELEGRAM_BOT_TOKEN=... python run_bot.py  # From env var
"""

import argparse
import os
import sys

from bot.handlers import run_bot, VERSION


BANNER = f"""
\033[2;36m╔══════════════════════════════════════════════════╗
║                                                  ║
║   📸  InstaUserCheckBot  v{VERSION:<22}║
║                                                  ║
║   🔍  Instagram Username Checker                 ║
║   ⚡  Fast • Free • No API Keys                  ║
║                                                  ║
╚══════════════════════════════════════════════════╝\033[0m
"""


def _is_notebook() -> bool:
    """Detect if running inside Jupyter/Colab notebook."""
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True
        if shell == "Shell":
            return True
    except (ImportError, NameError):
        pass
    try:
        import google.colab  # noqa: F401
        return True
    except ImportError:
        pass
    return False


def main():
    parser = argparse.ArgumentParser(description="📸 InstaUserCheckBot — Telegram Bot")
    parser.add_argument("--token", "-t", help="Telegram Bot Token (from @BotFather)")
    args = parser.parse_args()

    token = args.token or os.getenv("TELEGRAM_BOT_TOKEN") or input("🔑 Bot Token: ").strip()
    if not token:
        print("\033[1;31m❌ Bot token is required.\033[0m", file=sys.stderr)
        print("\033[2m   Get one from @BotFather on Telegram.\033[0m", file=sys.stderr)
        sys.exit(1)

    print(BANNER)

    if _is_notebook():
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "nest_asyncio"])
                import nest_asyncio
                nest_asyncio.apply()
            except Exception:
                print("⚠️  Install nest_asyncio for notebook support: pip install nest_asyncio")

    run_bot(token)


if __name__ == "__main__":
    main()
