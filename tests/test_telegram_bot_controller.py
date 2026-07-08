import json
import tempfile
import os

from core.payload_generator import PayloadGenerator
from bot.bot_controller import BotController


class DummyBot:
    def __init__(self, token=None):
        self.token = token
        self.sent_messages = []
        self.sent_documents = []

    def sendMessage(self, chat_id, text, **kwargs):
        self.sent_messages.append((chat_id, text))

    def sendDocument(self, chat_id, fileobj, caption=None, **kwargs):
        # read file for inspection
        content = fileobj.read()
        self.sent_documents.append((chat_id, content, caption))


def test_generate_payload_message_and_document(monkeypatch):
    # Patch telepot.Bot with dummy so no network calls occur
    import telepot

    monkeypatch.setattr(telepot, 'Bot', DummyBot)

    bc = BotController()

    # Call generate payload command
    chat_id = -1001
    bc.handle_command(chat_id, '/generate_payload echo hello')

    # Should have sent several messages and one document
    assert any('Generating' in m[1] or 'generated' in m[1] or 'Key ID' in m[1] for m in bc.bot.sent_messages)
    assert len(bc.bot.sent_documents) >= 1
