import threading

class StreamHandler:
    def __init__(self, bot):
        self.bot = bot
        self.live_mode = {}  # chat_id -> bool
        self.active_streams = {}  # chat_id -> thread

    def set_live_mode(self, chat_id, enabled):
        self.live_mode[chat_id] = enabled
        if not enabled and chat_id in self.active_streams:
            # Clean up old stream if exists
            self.active_streams[chat_id] = None

    def is_live_mode(self, chat_id):
        return self.live_mode.get(chat_id, False)

    def handle_streaming(self, chat_id, process):
        """Stream output from a process to the chat"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.bot.sendMessage(chat_id, line.strip())
                    # Small delay to avoid flooding
                    import time
                    time.sleep(0.1)
        except Exception as e:
            self.bot.sendMessage(chat_id, f'Stream error: {e}')
        finally:
            if chat_id in self.active_streams:
                del self.active_streams[chat_id]

    def start_stream_thread(self, chat_id, process):
        """Start a background thread for streaming output"""
        if chat_id in self.active_streams and self.active_streams[chat_id]:
            # Kill old thread if exists
            return
        
        thread = threading.Thread(
            target=self.handle_streaming,
            args=(chat_id, process),
            daemon=True
        )
        self.active_streams[chat_id] = thread
        thread.start()