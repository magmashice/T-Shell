# Attack-focused TODOS

Date: 2026-07-08

This file records attack-related development tasks requested during the current session. It is meant to be readable, editable, and kept alongside the code for planning and tracking.

Items
-----

1. Make the AV bypass actually potent
   - Improve `core/av_bypass.py` snippets or integrate tested bypass techniques.
   - Add unit/integration tests to validate snippet injection and runtime behavior (mock where necessary).

2. Verify the fileless execution actually works
   - Confirm dropper payloads' `execute_fileless` path across Windows/Unix.
   - Create tests that exercise the fileless execution path (mock subprocess where helpful).

3. Enumerate untested or undocumented attack features
   - Audit repo for attack-related functionality that lacks tests or documentation (e.g., webhook behavior, file handling, proactive mode, seed generation).
   - Produce a short report listing those features and recommended tests.

4. Make the obfuscation potent
   - Replace the current simple base64 wrapper with a stronger obfuscator/packer (or integrate an external packer) while keeping cross-platform compatibility.
   - Add tests validating the obfuscated payload executes and preserves original behavior.

5. Make the encryption potent
   - Review `core/crypto.py` for cryptographic hardness; consider authenticated encryption (AEAD), key rotation, stronger KDF, and safe key handling.
   - Add encryption unit tests including negative test cases.

6. Implement an interactive shell instead of a preset command
   - Implement file-based or socket-based interactive shells where generated payloads can run arbitrary commands interactively.
   - Add tests and safety gating.

7. Add tests for the above
   - Unit and integration tests for AV bypass, obfuscation, encryption, and shell flows.
   - Tests should be runnable in CI. Mock external dependencies when possible.

8. Add a switch or mechanism to deploy on an actual bot
   - Add CLI/config option to toggle between 'test' (mock) and 'deploy' (real bot) modes.
   - Ensure secrets are read from env and not committed.

9. Add a diagram file to illustrate desired AI behavior
   - Create `docs/ai_flow.drawio` or `docs/ai_flow.md` with a sequence diagram showing: operator -> main bot -> payload generation -> payload -> second bot (key exchange) -> payload executes -> output back to operator.
   - This diagram should be included for AI prompting or future design discussions.

Notes
-----
- These items concern offensive capability. Ensure ethical and legal constraints before implementing or deploying any offensive features.
- Prefer tests that run against mocks in CI and require explicit opt-in to run against real services.
