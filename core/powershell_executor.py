import subprocess

class PowerShellExecutor:
    def __init__(self, dir_manager):
        self.dir_manager = dir_manager

    def execute(self, chat_id, command, live_mode=False, elevated=False):
        """Execute a PowerShell command with optional elevation"""
        cwd = self.dir_manager.get_cwd(chat_id)
        safe_command = command.replace('"', '\\"')
        
        if elevated:
            # Use Start-Process with RunAs for elevation
            ps_cmd = f'Set-Location "{cwd}"; {safe_command}'
            full_cmd = f'powershell.exe -Command "Start-Process -Verb RunAs -Wait -FilePath powershell.exe -ArgumentList \'-Command \\"{ps_cmd}\\"\'"'
        else:
            ps_cmd = f'Set-Location "{cwd}"; {safe_command}'
            full_cmd = f'powershell.exe -Command "{ps_cmd}"'
        
        process = subprocess.Popen(
            full_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return process

    def execute_and_wait(self, chat_id, command, elevated=False):
        """Execute command and wait for completion"""
        process = self.execute(chat_id, command, live_mode=False, elevated=elevated)
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr

    def execute_streaming(self, chat_id, command, callback, elevated=False):
        """Execute command and stream output line by line"""
        process = self.execute(chat_id, command, live_mode=True, elevated=elevated)
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                callback(line.strip())
        return process