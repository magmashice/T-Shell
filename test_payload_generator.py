import compileall
import tempfile
from pathlib import Path

from core.payload_generator import PayloadGenerator


def test_generated_payload_is_valid_python():
    generator = PayloadGenerator("master-secret", b"salt", "bot-token", "payload-token")
    script, _, _ = generator.generate_payload("echo hello", 123)

    assert "sys.stderr.write" in script
    compile(script, "<generated_payload>", "exec")
