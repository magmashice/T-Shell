class SudoHandler:
    def __init__(self, executor):
        self.executor = executor
        self.pending_commands = {}  # chat_id -> command

    def queue_command(self, chat_id, command):
        """Queue a command that needs elevation"""
        self.pending_commands[chat_id] = command

    def is_pending(self, chat_id):
        """Check if there's a pending command for this user"""
        return chat_id in self.pending_commands

    def execute_pending(self, chat_id, password=None):
        """Execute the pending command with elevation"""
        command = self.pending_commands.pop(chat_id, None)
        if not command:
            return None, "No pending command found"
        
        # Strip 'sudo ' prefix
        actual_command = command[5:]
        try:
            returncode, stdout, stderr = self.executor.execute_and_wait(
                chat_id, 
                actual_command, 
                elevated=True
            )
            if returncode == 0:
                return returncode, stdout or "Elevated command executed successfully."
            else:
                return returncode, stderr or f"Error code: {returncode}"
        except Exception as e:
            return None, str(e)

    def clear_pending(self, chat_id):
        """Clear pending command without executing"""
        if chat_id in self.pending_commands:
            del self.pending_commands[chat_id]