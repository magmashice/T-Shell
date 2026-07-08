from core.crypto import CryptoHandler


def test_encrypt_decrypt_roundtrip():
    c = CryptoHandler('master', b'salt')
    key = c.get_current_key()
    plaintext = 'echo hello'
    encrypted = c.encrypt_payload(plaintext, key)
    assert encrypted != plaintext
    decrypted = c.decrypt_payload(encrypted, key)
    assert decrypted == plaintext
