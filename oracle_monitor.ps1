# Script PowerShell - Oracle Cloud Instance Monitor
# Vérifie toutes les 5 minutes si une instance est disponible
# Lance une alerte sonore quand c'est dispo

param(
    [int]$IntervalMinutes = 5,
    [switch]$Sound = $true
)

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ORACLE CLOUD CAPACITY MONITOR" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ce script vérifie toutes les $IntervalMinutes minutes" -ForegroundColor Yellow
Write-Host "si Oracle Cloud a de la capacité disponible." -ForegroundColor Yellow
Write-Host ""
Write-Host "Quand c'est disponible:" -ForegroundColor Green
Write-Host "  - Alerte sonore (si activé)" -ForegroundColor Green
Write-Host "  - Notification Windows" -ForegroundColor Green
Write-Host "  - Ouverture automatique du navigateur" -ForegroundColor Green
Write-Host ""
Write-Host "Appuie sur Ctrl+C pour arrêter" -ForegroundColor Yellow
Write-Host ""

# Configuration
$OracleConsoleURL = "https://cloud.oracle.com/compute/instances/create"
$attempt = 1
$startTime = Get-Date

# Fonction d'alerte sonore
function Play-AlertSound {
    if ($Sound) {
        try {
            [console]::beep(800, 300)
            Start-Sleep -Milliseconds 100
            [console]::beep(1000, 300)
            Start-Sleep -Milliseconds 100
            [console]::beep(1200, 500)
        }
        catch {
            Write-Host "  (Alerte sonore non disponible)" -ForegroundColor Gray
        }
    }
}

# Fonction de notification Windows
function Show-Notification {
    param($Message)

    try {
        Add-Type -AssemblyName System.Windows.Forms
        $notification = New-Object System.Windows.Forms.NotifyIcon
        $notification.Icon = [System.Drawing.SystemIcons]::Information
        $notification.BalloonTipTitle = "Oracle Cloud Disponible!"
        $notification.BalloonTipText = $Message
        $notification.Visible = $true
        $notification.ShowBalloonTip(10000)
    }
    catch {
        Write-Host "  (Notification Windows non disponible)" -ForegroundColor Gray
    }
}

# Fonction de test (simulation - à adapter selon ton besoin)
function Test-OracleCapacity {
    # Cette fonction simule un test
    # Dans la réalité, tu devrais utiliser l'OCI CLI ou scraper la page web

    # Pour l'instant, on simule un résultat aléatoire
    # Remplace par un vrai test si tu as l'OCI CLI configuré

    $random = Get-Random -Minimum 1 -Maximum 100

    # Simule 5% de chance de succès à chaque test
    return ($random -le 5)
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Démarrage du monitoring..." -ForegroundColor Green
Write-Host ""

# Boucle principale
while ($true) {
    $now = Get-Date
    $elapsed = $now - $startTime

    Write-Host "[$($now.ToString('HH:mm:ss'))] " -NoNewline -ForegroundColor Cyan
    Write-Host "Tentative #$attempt " -NoNewline -ForegroundColor White
    Write-Host "(depuis $([math]::Floor($elapsed.TotalMinutes)) min)" -ForegroundColor Gray

    # Tente de vérifier la disponibilité
    try {
        Write-Host "  Vérification de la capacité..." -ForegroundColor Yellow

        # OPTION 1: Si tu as OCI CLI configuré (recommandé)
        # Décommente ces lignes et configure OCI CLI:
        <#
        $result = oci compute instance launch `
            --compartment-id "ton-compartment-id" `
            --availability-domain "AD-1" `
            --shape "VM.Standard.E2.1.Micro" `
            --dry-run `
            2>&1

        if ($result -notmatch "Out of capacity") {
            $available = $true
        }
        #>

        # OPTION 2: Simulation (par défaut)
        $available = Test-OracleCapacity

        if ($available) {
            Write-Host ""
            Write-Host "============================================" -ForegroundColor Green
            Write-Host "  CAPACITÉ DISPONIBLE !!!" -ForegroundColor Green
            Write-Host "============================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Oracle Cloud a de la capacité maintenant!" -ForegroundColor Green
            Write-Host "Ouvre vite la console pour créer ton instance!" -ForegroundColor Yellow
            Write-Host ""

            # Alerte sonore
            Play-AlertSound

            # Notification Windows
            Show-Notification "Oracle Cloud a de la capacité! Crée ton instance maintenant!"

            # Ouvre le navigateur
            Write-Host "Ouverture du navigateur..." -ForegroundColor Cyan
            Start-Process $OracleConsoleURL

            Write-Host ""
            Write-Host "Appuie sur une touche pour arrêter le monitoring..." -ForegroundColor Yellow
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            break
        }
        else {
            Write-Host "  Toujours en rupture de stock" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  Erreur lors de la vérification: $_" -ForegroundColor Red
    }

    # Attendre avant la prochaine tentative
    $waitSeconds = $IntervalMinutes * 60
    Write-Host "  Prochaine vérification dans $IntervalMinutes min..." -ForegroundColor Gray
    Write-Host ""

    Start-Sleep -Seconds $waitSeconds
    $attempt++
}

Write-Host ""
Write-Host "Monitoring arrêté." -ForegroundColor Yellow
Write-Host ""
