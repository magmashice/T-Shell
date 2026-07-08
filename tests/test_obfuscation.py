import sys
import subprocess

from core.obfuscation import obfuscate_script


def test_obfuscate_and_execute(tmp_path):
    payload = "print('OBF_OK')"
    obf = obfuscate_script(payload)

    p = tmp_path / 'obf.py'
    p.write_text(obf)

    proc = subprocess.run([sys.executable, str(p)], capture_output=True, text=True, timeout=10)
    assert 'OBF_OK' in proc.stdout
