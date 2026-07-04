"""
Cryptography Handler for Python Payloads
"""

import base64
import hashlib
import os
import time
import random
import uuid

class CryptoHandler:
    def __init__(self, master_secret, salt):
        self.master_secret = master_secret
        self.salt = salt
        self.current_key = self._generate_key()
        self.key_store = {}

    def _generate_key(self):
        random_salt = os.urandom(16)
        salt_hex = self.salt.hex() if isinstance(self.salt, bytes) else str(self.salt)
        key_material = f"{self.master_secret}_{salt_hex}_{time.time()}_{random_salt.hex()}_{random.randint(1000, 9999)}"
        key_bytes = hashlib.sha256(key_material.encode('utf-8')).digest()
        return base64.b64encode(key_bytes).decode('utf-8')

    def encrypt_payload(self, data, key=None):
        if key is None:
            key = self.current_key

        key_bytes = base64.b64decode(key)
        data_bytes = data.encode('utf-8')
        stretched = (key_bytes * (len(data_bytes) // len(key_bytes) + 1))[:len(data_bytes)]
        encrypted = bytes(a ^ b for a, b in zip(data_bytes, stretched))
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt_payload(self, encrypted_data, key):
        try:
            key_bytes = base64.b64decode(key)
            data_bytes = base64.b64decode(encrypted_data)
            stretched = (key_bytes * (len(data_bytes) // len(key_bytes) + 1))[:len(data_bytes)]
            decrypted = bytes(a ^ b for a, b in zip(data_bytes, stretched))
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