#!/usr/bin/env python3
"""
Telegram RAT - Python Payload Generator
Cross-platform encrypted payloads with auto-key delivery
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.bot_controller import BotController

def main():
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