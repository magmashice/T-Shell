import telepot
from telepot.loop import MessageLoop
import time
from config import TOKEN
from core import (
    DirectoryManager,
    PowerShellExecutor,
    SudoHandler,
    FileHandler,
    StreamHandler,
    CommandHandlers
)

class BotController:
    def __init__(self, token=TOKEN):
        self.bot = telepot.Bot(token)
        
        # Initialize all components
        self.dir_manager = DirectoryManager()
        self.executor = PowerShellExecutor(self.dir_manager)
        self.sudo_handler = SudoHandler(self.executor)
        self.stream_handler = StreamHandler(self.bot)
        self.file_handler = FileHandler(self.dir_manager, self.bot)
        self.command_handlers = CommandHandlers(
            self.bot,
            self.dir_manager,
            self.executor,
            self.sudo_handler,
            self.file_handler,
            self.stream_handler
        )

    def handle_message(self, msg):
        """Main message dispatcher"""
        try:
            content_type, chat_type, chat_id = telepot.glance(msg)
            
            if content_type == 'text':
                text = msg['text']
                
                # Route to appropriate handler based on command
                if text.startswith('/start'):
                    self.command_handlers.handle_start(msg)
                elif text.startswith('/help'):
                    self.command_handlers.handle_help(msg)
                elif text.startswith('/live'):
                    self.command_handlers.handle_live(msg)
                elif text.startswith('/normal'):
                    self.command_handlers.handle_normal(msg)
                elif text.startswith('/get'):
                    self.command_handlers.handle_get(msg)
                else:
                    # Check if this is a sudo password response
                    if self.sudo_handler.is_pending(chat_id):
                        self.command_handlers.handle_sudo_password(msg)
                    else:
                        self.command_handlers.handle_general_command(msg)
            
            elif content_type == 'document':
                # Handle file uploads
                chat_id = msg['chat']['id']
                file_id = msg['document']['file_id']
                file_name = msg['document'].get('file_name', None)
                self.file_handler.save_document(chat_id, file_id, file_name)
            
            elif content_type == 'photo':
                # Handle photo uploads (save as image)
                chat_id = msg['chat']['id']
                # Get the largest photo
                photo = msg['photo'][-1]
                file_id = photo['file_id']
                file_name = f"photo_{time.time()}.jpg"
                self.file_handler.save_document(chat_id, file_id, file_name)
                
        except Exception as e:
            # Send error to user
            try:
                chat_id = msg['chat']['id']
                self.bot.sendMessage(chat_id, f'Message handling error: {e}')
            except:
                pass

    def start(self):
        """Start the bot"""
        MessageLoop(self.bot, self.handle_message).run_as_thread()
        print("=" * 50)
        print("Telegram PowerShell Bot Running...")
        print(f"Bot Token: {TOKEN[:10]}...")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            sys.exit(0)