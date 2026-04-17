# Run from backend folder: .\install-deps.ps1
$ErrorActionPreference = "Stop"
function Install-Pip {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        Write-Host "Using: py -m pip"
        py -m pip install -r requirements.txt
        return
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Host "Using: python -m pip"
        python -m pip install -r requirements.txt
        return
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        Write-Host "Using: python3 -m pip"
        python3 -m pip install -r requirements.txt
        return
    }
    throw "Python not found. Install from https://www.python.org/downloads/ and check 'Add python.exe to PATH', then reopen the terminal."
}

Set-Location $PSScriptRoot
Install-Pip
Write-Host "Done. Then: py -m uvicorn main:app --reload --port 8000"
Write-Host "   or: python -m uvicorn main:app --reload --port 8000"
