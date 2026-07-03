import os

class FileHandler:
    def __init__(self, dir_manager, bot):
        self.dir_manager = dir_manager
        self.bot = bot

    def get_file(self, chat_id, filename):
        """Download a file from the current directory"""
        cwd = self.dir_manager.get_cwd(chat_id)
        file_path = os.path.join(cwd, filename)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                self.bot.sendDocument(chat_id, open(file_path, 'rb'))
                self.bot.sendMessage(chat_id, f'File "{filename}" dumped.')
                return True
            except Exception as e:
                self.bot.sendMessage(chat_id, f'Error sending file: {e}')
                return False
        else:
            self.bot.sendMessage(chat_id, f'Error: File "{filename}" not found.')
            return False

    def save_document(self, chat_id, file_id, original_filename=None):
        """Save an uploaded document to the current directory"""
        cwd = self.dir_manager.get_cwd(chat_id)
        try:
            file_info = self.bot.getFile(file_id)
            remote_path = file_info['file_path']
            filename = original_filename or remote_path.split('/')[-1]
            save_path = os.path.join(cwd, filename)
            
            self.bot.download_file(file_id, save_path)
            self.bot.sendMessage(chat_id, f'File "{filename}" saved in {cwd}.')
            return save_path
        except Exception as e:
            self.bot.sendMessage(chat_id, f'Error saving file: {e}')
            return None