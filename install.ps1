# Installer "un clic" del Consulente Legale per Windows 11.
#
# Prepara tutto il necessario dietro le quinte, senza privilegi di amministratore:
#   1. installa git e uv se mancano (winget / installer ufficiale)
#   2. configura git per i percorsi lunghi (i nomi-file del corpus superano i 260 char)
#   3. scarica il corpus, sincronizza l'ambiente e costruisce l'indice (scripts/setup.py)
#   4. registra il server MCP "legge-it" in Claude Desktop, preservando gli altri server
#
# All'utente resta un solo gesto finale: riavviare Claude Desktop.
# Si lancia con un doppio clic su install.cmd, oppure:
#   powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Say([string]$msg)  { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Ok([string]$msg)   { Write-Host "  OK: $msg" -ForegroundColor Green }
function Info([string]$msg) { Write-Host "  $msg" }

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user    = [Environment]::GetEnvironmentVariable("Path", "User")
    $local   = Join-Path $env:USERPROFILE ".local\bin"
    $env:Path = "$machine;$user;$local"
}

function Ensure-Git {
    Say "1/4  git"
    if (Get-Command git -ErrorAction SilentlyContinue) { Ok "git gia' presente"; return }
    Info "git non trovato, installo con winget..."
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    Refresh-Path
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "git non risulta installato. Installa Git for Windows da https://git-scm.com e rilancia."
    }
    Ok "git installato"
}

function Ensure-Uv {
    Say "2/4  uv (Python)"
    if (Get-Command uv -ErrorAction SilentlyContinue) { Ok "uv gia' presente"; return }
    Info "uv non trovato, installo dall'installer ufficiale..."
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    Refresh-Path
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv non risulta installato. Vedi https://docs.astral.sh/uv/ e rilancia."
    }
    Ok "uv installato"
}

function Setup-Project {
    Say "3/4  Corpus, ambiente e indice"
    # git per i percorsi lunghi, una volta per macchina (nessun admin).
    git config --global core.longpaths true
    Ok "git configurato per i percorsi lunghi"
    Info "Scarico il corpus e costruisco l'indice (alcuni minuti la prima volta)..."
    Push-Location $Root
    try {
        uv run python scripts/setup.py
        if ($LASTEXITCODE -ne 0) { throw "setup.py ha restituito un errore." }
    } finally {
        Pop-Location
    }
    Ok "Indice pronto"
}

function Find-ClaudeConfig {
    $paths = @()
    $paths += Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
    $pkgRoot = Join-Path $env:LOCALAPPDATA "Packages"
    if (Test-Path $pkgRoot) {
        Get-ChildItem $pkgRoot -Filter "Claude*" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $paths += Join-Path $_.FullName "LocalCache\Roaming\Claude\claude_desktop_config.json"
        }
    }
    foreach ($p in $paths) { if (Test-Path $p) { return $p } }
    return $paths[0]  # default: percorso standard, sara' creato
}

function Register-ClaudeDesktop {
    Say "4/4  Registrazione in Claude Desktop"
    $cfg = Find-ClaudeConfig
    $dir = Split-Path $cfg -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

    if (Test-Path $cfg) {
        Copy-Item $cfg "$cfg.bak" -Force
        $json = Get-Content $cfg -Raw | ConvertFrom-Json
    } else {
        $json = [pscustomobject]@{}
    }
    if (-not ($json.PSObject.Properties.Name -contains "mcpServers")) {
        $json | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) -Force
    }

    $uv = (Get-Command uv).Source
    $entry = [pscustomobject]@{
        command = $uv
        args    = @("--directory", $Root, "run", "python", "-m", "legal_consultant.mcp_server")
    }
    $json.mcpServers | Add-Member -NotePropertyName "legge-it" -NotePropertyValue $entry -Force

    $out = $json | ConvertTo-Json -Depth 30
    # Scrittura UTF-8 senza BOM: il parser JSON di Claude Desktop non tollera il BOM.
    [System.IO.File]::WriteAllText($cfg, $out, (New-Object System.Text.UTF8Encoding $false))
    Ok "Server 'legge-it' registrato in $cfg"
}

Write-Host "Consulente Legale - installazione" -ForegroundColor White
Ensure-Git
Ensure-Uv
Setup-Project
Register-ClaudeDesktop

Write-Host "`nFatto." -ForegroundColor Green
Write-Host "Ultimo passo manuale: chiudi del tutto Claude Desktop (anche dall'icona"
Write-Host "nella barra vicino all'orologio) e riaprilo. Poi chiedigli una domanda di"
Write-Host "diritto italiano: usera' 'legge-it' per rispondere citando le fonti."
