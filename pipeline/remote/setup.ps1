# One-time setup of a Windows machine that judges for the solution pipeline
# (every XeLaTeX and KaTeX check; see pipeline/scripts/remote_judge.py).
# From the repo root, after cloning:
#   powershell -ExecutionPolicy Bypass -File pipeline\remote\setup.ps1
# Installs (with winget, when missing): MiKTeX, Node.js LTS, uv. Then gives MiKTeX the
# exact package set of the main machine (miktex_packages.txt), installs the Python
# environment and the frontend modules the KaTeX check bundles, and ends with a test.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))

function Have($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
function Install-Missing($command, $wingetId) {
    if (Have $command) { return }
    Write-Host "installing $wingetId"
    winget install --id $wingetId --exact --silent --accept-source-agreements --accept-package-agreements
    Refresh-Path
    if (-not (Have $command)) { throw "$command is still not on PATH after installing $wingetId (open a new terminal and rerun)" }
}

if (-not (Have winget)) { throw "winget is missing: install App Installer from the Microsoft Store" }
if (-not (Have git)) { throw "git is missing" }
Install-Missing "xelatex" "MiKTeX.MiKTeX"
Install-Missing "node" "OpenJS.NodeJS.LTS"
Install-Missing "uv" "astral-sh.uv"

Write-Host "MiKTeX: install missing packages without asking, then the main machine's package set"
initexmf --set-config-value="[MPM]AutoInstall=1"
miktex packages update-package-database
miktex packages require --package-id-file pipeline\remote\miktex_packages.txt
if ($LASTEXITCODE -ne 0) { throw "miktex packages require failed" }

Write-Host "Python environment"
uv sync --group pipeline
if ($LASTEXITCODE -ne 0) { throw "uv sync failed" }

Write-Host "frontend modules (KaTeX and esbuild for the web check)"
Push-Location frontend
npm.cmd ci --no-audit --no-fund
$npm = $LASTEXITCODE
Pop-Location
if ($npm -ne 0) { throw "npm ci failed" }

if (-not (Test-Path pipeline\.judge_key)) {
    Write-Warning "copy pipeline\.judge_key from the main machine to pipeline\.judge_key here before running a job"
}
.venv\Scripts\python.exe -I pipeline\scripts\remote_judge.py check
