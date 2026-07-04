"""
Cryptography Handler for Python Payloads
"""

import base64
import hashlib
import os
import time
import random
import uuid
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class CryptoHandler:
    def __init__(self, master_secret, salt):
        self.master_secret = master_secret
        self.salt = salt
        self.current_key = self._generate_key()
        self.key_store = {}

    def _generate_key(self):
        random_salt = os.urandom(16)
        key_material = f"{self.master_secret}_{time.time()}_{random_salt.hex()}_{random.randint(1000, 9999)}"
        key_bytes = hashlib.sha256(key_material.encode('utf-8')).digest()
        return base64.b64encode(key_bytes).decode('utf-8')

    def _derive_aes_key(self, key):
        return hashlib.sha256((self.master_secret + key).encode('utf-8')).digest()

    def encrypt_payload(self, data, key=None):
        if key is None:
            key = self.current_key

        aes_key = self._derive_aes_key(key)
        iv = os.urandom(16)
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)

        padded = pad(data.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded)

        combined = iv + encrypted
        return base64.b64encode(combined).decode('utf-8')

    def decrypt_payload(self, encrypted_data, key):
        try:
            aes_key = self._derive_aes_key(key)
            combined = base64.b64decode(encrypted_data)
            iv = combined[:16]
            ciphertext = combined[16:]

            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")

    def generate_key_id(self):
        return str(uuid.uuid4())[:8]

    def store_key(self, key_id, key):
        self.key_store[key_id] = key
        return key_id

    def get_key(self, key_id):
        return self.key_store.get(key_id)

    def get_current_key(self):
        return self.current_key