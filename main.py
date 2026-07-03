#!/usr/bin/env python3
"""
Telegram PowerShell Bot - Entry Point
A modular bot that executes PowerShell commands via Telegram
"""

import sys
import os

# Add the current directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import BotController

def main():
    """Main entry point"""
    try:
        controller = BotController()
        controller.start()
    except KeyboardInterrupt:
        print("\nBot stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()