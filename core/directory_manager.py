import os
import subprocess

class DirectoryManager:
    def __init__(self):
        self.user_directories = {}  # chat_id -> cwd

    def get_cwd(self, chat_id):
        """Get current working directory for a user"""
        return self.user_directories.get(chat_id, os.getcwd())

    def set_cwd(self, chat_id, path):
        """Set current working directory for a user"""
        self.user_directories[chat_id] = path

    def change_directory(self, chat_id, new_path):
        """Change directory using PowerShell and return new path"""
        try:
            ps_cmd = f'Set-Location "{new_path}"; Get-Location'
            full_cmd = f'powershell.exe -Command "{ps_cmd}"'
            result = subprocess.check_output(full_cmd, shell=True, text=True).strip()
            lines = result.splitlines()
            new_dir = lines[-1].strip() if lines else new_path
            self.user_directories[chat_id] = new_dir
            return new_dir
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to change directory: {e.stderr}")
        except Exception as e:
            raise Exception(f"Failed to change directory: {e}")