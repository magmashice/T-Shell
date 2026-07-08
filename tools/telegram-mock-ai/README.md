# telegram-mock-ai — local Telegram Bot API mock (helper)

This helper folder contains convenience files and instructions to run
`skrashevich/telegram-mock-ai` inside this workspace for local
development and integration testing.

Options (from upstream):

- Docker + Ollama (recommended): runs the mock server plus a local LLM
  to generate realistic replies and seed data.
- Docker without an LLM: run only the mock server and use the Admin API
  to inject messages manually.
- From source: requires Go 1.22+, `make run` will build and run the
  server.

Quick setup (using the bundled helper script):

1. Open PowerShell and run:

```powershell
.\tools\telegram-mock-ai\setup.ps1
```

2. The script clones the upstream repo into
   `tools/telegram-mock-ai/telegram-mock-ai`, copies
   `config.example.yaml -> config.yaml` and runs `docker compose up -d`.

3. After startup the Bot API is at `http://localhost:8081` and the
   Admin API at `http://localhost:8082`.

Admin API examples:

Create a user:

```bash
curl -X POST http://localhost:8082/api/users -d '{"first_name":"Diana","username":"diana"}'
```

Inject a user message into chat -1001:

```bash
curl -X POST http://localhost:8082/api/chats/-1001/messages -H 'Content-Type: application/json' -d '{"user_id":1001,"text":"Hi, bot!"}'
```

Notes:

- The upstream project is maintained at https://github.com/skrashevich/telegram-mock-ai
- Refer to upstream README for advanced configuration (LLM providers,
  proactive mode, seed generation).
