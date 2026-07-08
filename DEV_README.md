# Developer README

Purpose
-------
Short guide for developers: project layout, how to run the code, and how
to run tests (unit + integration with local mock server).

Project layout (important files)
- `main.py` — launcher for the `BotController` service.
- `bot/` — Telegram bot controller (primary operator-facing logic).
- `core/` — helper subsystems:
  - `crypto.py` — `CryptoHandler` encrypt/decrypt and key storage.
  - `payload_generator.py` — builds self-contained Python payloads and droppers.
  - `client_manager.py` — client registry and command queue.
  - `av_bypass.py` — small AV-bypass snippets injected into droppers.
  - `obfuscation.py` — simple obfuscation helper used in tests.
- `tests/` — pytest test suite (unit and mocked integration tests).
- `tools/telegram-mock-ai/` — helper to run `skrashevich/telegram-mock-ai` for local testing.

Quickstart (developer)
----------------------
Prerequisites: Python 3.10+, pip, (optional) Docker for full integration.

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Run unit + mocked integration tests:

```powershell
pytest -q
```

Notes: The delivery/integration test is implemented to run in-process and
mock the Telegram API by default so Docker is NOT required to run the
test suite.

Running the real mock server (optional)
--------------------------------------
If you want the upstream `telegram-mock-ai` running locally (real
HTTP endpoints at `http://localhost:8081` and `http://localhost:8082`):

Windows helper (provided):

```powershell
.\tools\telegram-mock-ai\setup.ps1
```

Or run docker compose in `tools/telegram-mock-ai/telegram-mock-ai`:

```powershell
cd tools/telegram-mock-ai/telegram-mock-ai
docker compose up -d
```

Important env vars
- `TELEGRAM_API_BASE` — override API base (used by generated payloads in tests).

Development tips
- Add new unit tests under `tests/` and prefer small, focused tests.
- Integration tests that require external services should be gated
  (skipped by default) or replaced with mocks to keep CI fast.
- When changing templates in `payload_generator.py`, run the
  `tests/test_delivery_integration.py` to validate generated code compiles
  and executes under the mocked environment.

Building docs
-----------
This repo uses plain docstrings. To add HTML docs, run Sphinx or MkDocs.
If you'd like, I can scaffold Sphinx config and a docs/ folder.

Contact
-------
For questions about internals, edit `DEV_README.md` or ask in the
project issue tracker.
