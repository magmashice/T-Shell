import json
import io
import contextlib

from core.payload_generator import PayloadGenerator


def test_generate_and_execute_payload(tmp_path):
    """Integration-style test without external network: execute the
    generated payload in-process and mock urllib to simulate the
    telegram-mock-ai responses (sendMessage + getUpdates returning the key).
    """
    gen = PayloadGenerator('m', b's', 'bot-token', 'payload-token')
    script, key_id, key = gen.generate_payload('echo INTEGRATION_TEST', -1001)

    # Execute the generated script in a fresh globals dict so we can
    # monkeypatch urllib.request.urlopen used by the script.
    fake_globals = {}
    # Execute script to define functions and constants
    exec(script, fake_globals)

    # State to simulate that sendMessage was called
    state = {'sent': False}

    class MockResp:
        def __init__(self, text):
            self._b = text.encode('utf-8')

        def read(self):
            return self._b

        def getcode(self):
            return 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(req, timeout=10):
        # Determine URL string
        url = getattr(req, 'full_url', None) or (req.get_full_url() if hasattr(req, 'get_full_url') else str(req))
        # sendMessage call: mark as sent and return OK
        if 'sendMessage' in url:
            state['sent'] = True
            return MockResp(json.dumps({'ok': True, 'result': []}))
        # getUpdates call: return key once sendMessage seen
        if 'getUpdates' in url:
            if state['sent']:
                res = {'ok': True, 'result': [{
                    'update_id': 1,
                    'message': {'chat': {'id': -1001}, 'text': key}
                }]}
                return MockResp(json.dumps(res))
            return MockResp(json.dumps({'ok': True, 'result': []}))

    # Patch the urllib.request.urlopen used by the script
    import urllib
    fake_globals['urllib'].request.urlopen = fake_urlopen

    # Capture stdout printed by the payload's execute/print
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        # Run main from the generated script
        fake_globals['main']()

    out = buf.getvalue()
    assert 'INTEGRATION_TEST' in out
