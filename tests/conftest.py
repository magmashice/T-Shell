import os
import sys
import time
import subprocess
import urllib.request
import urllib.error

import pytest
import shutil

# Ensure project root is on sys.path so `import core.*` works when running pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def is_admin_api_healthy():
    try:
        with urllib.request.urlopen('http://localhost:8082/api/health', timeout=2) as resp:
            return resp.getcode() == 200
    except Exception:
        return False


def start_mock_server():
    # Prefer the included PowerShell helper on Windows, else attempt docker compose
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', 'telegram-mock-ai')
    setup_ps1 = os.path.join(tools_dir, 'setup.ps1')
    repo_dir = os.path.join(tools_dir, 'telegram-mock-ai')

    # Try docker-compose start if repo present and docker is available (preferred)
    if os.path.exists(repo_dir) and shutil.which('docker'):
        subprocess.check_call(['docker', 'compose', 'up', '-d'], cwd=repo_dir)
        return

    # On Windows, fallback to PowerShell helper if present
    if os.name == 'nt' and os.path.exists(setup_ps1):
        subprocess.check_call(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', setup_ps1])
        return

    # No way to start the mock server from this environment
    raise RuntimeError('Cannot start telegram-mock-ai: docker not found and setup script missing')


@pytest.fixture(scope='session')
def mock_server():
    """Ensure telegram-mock-ai Admin API is running at localhost:8082.

    If not reachable, attempt to start docker compose (or the PowerShell
    helper on Windows) and wait until healthy or timeout.
    """
    if is_admin_api_healthy():
        yield
        return

    start_mock_server()

    # wait up to 60s for server to come up
    deadline = time.time() + 60
    while time.time() < deadline:
        if is_admin_api_healthy():
            yield
            return
        time.sleep(1)

    pytest.skip('telegram-mock-ai did not start in time')
