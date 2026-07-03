import threading
from config import INFO_MSG, HELP_TEXT

class CommandHandlers:
    def __init__(self, bot, dir_manager, executor, sudo_handler, file_handler, stream_handler):
        self.bot = bot
        self.dir_manager = dir_manager
        self.executor = executor
        self.sudo_handler = sudo_handler
        self.file_handler = file_handler
        self.stream_handler = stream_handler

    def handle_start(self, msg):
        chat_id = msg['chat']['id']
        self.bot.sendMessage(chat_id, INFO_MSG)

    def handle_help(self, msg):
        chat_id = msg['chat']['id']
        self.bot.sendMessage(chat_id, HELP_TEXT)

    def handle_live(self, msg):
        chat_id = msg['chat']['id']
        self.stream_handler.set_live_mode(chat_id, True)
        self.bot.sendMessage(chat_id, 'Live terminal mode activated (PowerShell streaming).')

    def handle_normal(self, msg):
        chat_id = msg['chat']['id']
        self.stream_handler.set_live_mode(chat_id, False)
        self.bot.sendMessage(chat_id, 'Live terminal mode deactivated.')

    def handle_get(self, msg):
        chat_id = msg['chat']['id']
        text = msg['text']
        parts = text.split()
        if len(parts) < 2:
            self.bot.sendMessage(chat_id, 'Usage: /get <filename>')
            return
        filename = parts[1]
        self.file_handler.get_file(chat_id, filename)

    def handle_sudo_password(self, msg):
        """Handle sudo password response"""
        chat_id = msg['chat']['id']
        password = msg['text']  # Not actually used, kept for compatibility
        returncode, output = self.sudo_handler.execute_pending(chat_id, password)
        if returncode is None:
            self.bot.sendMessage(chat_id, f'Error: {output}')
        elif returncode == 0:
            self.bot.sendMessage(chat_id, output or 'Elevated command executed successfully.')
        else:
            self.bot.sendMessage(chat_id, f'Error: {output}')

    def handle_general_command(self, msg):
        """Handle any command that's not a slash command"""
        chat_id = msg['chat']['id']
        command = msg['text']
        
        # Check if it's a sudo command
        if command.startswith('sudo '):
            self.sudo_handler.queue_command(chat_id, command)
            self.bot.sendMessage(chat_id, 'Please enter administrator password:')
            return

        # Check if it's a cd command
        if command.startswith('cd '):
            try:
                new_dir = command[3:].strip()
                new_path = self.dir_manager.change_directory(chat_id, new_dir)
                self.bot.sendMessage(chat_id, f'Current directory :> {new_path}')
                return
            except Exception as e:
                self.bot.sendMessage(chat_id, f'Error: {e}')
                return

        # Execute regular command
        live_mode = self.stream_handler.is_live_mode(chat_id)
        try:
            if live_mode:
                process = self.executor.execute(chat_id, command, live_mode=True)
                # Start streaming in background
                self.stream_handler.start_stream_thread(chat_id, process)
            else:
                returncode, stdout, stderr = self.executor.execute_and_wait(chat_id, command)
                if returncode == 0:
                    self.bot.sendMessage(chat_id, stdout or 'Command executed successfully.')
                else:
                    self.bot.sendMessage(chat_id, f'Error: {stderr or "Unknown error"}')
        except Exception as e:
            self.bot.sendMessage(chat_id, f'Error: {e}')