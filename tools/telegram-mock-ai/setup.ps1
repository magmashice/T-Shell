<#
PowerShell helper to clone and start telegram-mock-ai for local dev.

The script will:
- clone the upstream repo into tools/telegram-mock-ai/telegram-mock-ai (if missing)
- copy config.example.yaml -> config.yaml if not present
- run `docker compose up -d` in the repo folder

Run this from the repository root in an elevated (or normal) PowerShell.
#>

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$target = Join-Path $root 'telegram-mock-ai'

if (-not (Test-Path $target)) {
    Write-Host "Cloning telegram-mock-ai into $target..."
    git clone https://github.com/skrashevich/telegram-mock-ai.git $target
} else {
    Write-Host "Repository already cloned at $target"
}

$cfgExample = Join-Path $target 'config.example.yaml'
$cfg = Join-Path $target 'config.yaml'
if ((Test-Path $cfgExample) -and (-not (Test-Path $cfg))) {
    Write-Host "Copying config.example.yaml -> config.yaml"
    Copy-Item -Path $cfgExample -Destination $cfg
} else {
    Write-Host "config.yaml already exists or example is missing"
}

Write-Host "Starting docker compose (detached)..."
Push-Location $target
try {
    & docker compose up -d
} catch {
    Write-Host "Failed to run 'docker compose up -d'. Please ensure Docker is installed and running." -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

Write-Host "Done. Bot API: http://localhost:8081  Admin API: http://localhost:8082"
Write-Host "If using Ollama, run: docker exec -it ollama ollama pull llama3"
