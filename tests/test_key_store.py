from core.crypto import CryptoHandler


def test_store_and_get_key():
    c = CryptoHandler('m', b's')
    kid = c.generate_key_id()
    key = c.get_current_key()
    c.store_key(kid, key)
    assert c.get_key(kid) == key
