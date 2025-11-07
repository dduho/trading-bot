# Script PowerShell pour lancer le bot de trading
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Trading Bot" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Aller dans le répertoire du script
Set-Location $PSScriptRoot

# Activer l'environnement virtuel si présent
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Lancer le bot avec sortie non bufferisée
$env:PYTHONUNBUFFERED = "1"

Write-Host "Launching bot..." -ForegroundColor Green
Write-Host ""

# Lancer et garder la console ouverte
try {
    python run_bot.py
} catch {
    Write-Host "Error occurred: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "Bot stopped. Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
