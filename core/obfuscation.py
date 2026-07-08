"""Simple obfuscation utilities.

This module provides a minimal obfuscator used by tests. It base64
encodes a Python script and wraps it with a small decoder that executes
the original code. This is intentionally simple and meant to support
integration tests; it is NOT intended as a production obfuscator.
"""

import base64


def obfuscate_script(script: str) -> str:
    """Return a Python script (string) that decodes and executes `script`.

    The returned script is self-contained and can be written to a file and
    executed with the system Python interpreter.
    """
    encoded = base64.b64encode(script.encode('utf-8')).decode('ascii')
    wrapper = (
        "# -*- coding: utf-8 -*-\n"
        "import base64\n"
        f"_s = {encoded!r}\n"
        "decoded = base64.b64decode(_s).decode('utf-8')\n"
        "exec(decoded, {'__name__': '__main__'})\n"
    )
    return wrapper
