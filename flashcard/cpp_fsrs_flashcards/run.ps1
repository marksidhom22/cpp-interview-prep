$ErrorActionPreference = "Stop"

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExecutable = Join-Path $projectDirectory ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "The local environment is missing. Follow the setup steps in README.md first."
}

Push-Location -LiteralPath $projectDirectory
try {
    & $pythonExecutable app.py
}
finally {
    Pop-Location
}

