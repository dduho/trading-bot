# PowerShell Script to Upload Trading Bot to Oracle Cloud
# Run this from your trading-bot directory on Windows

################################################################################
# Configuration
################################################################################

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  UPLOAD TRADING BOT TO ORACLE CLOUD" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get SSH key path
$defaultKeyPath = Join-Path $env:USERPROFILE "Downloads\ssh-key-*.key"
$keyFiles = Get-ChildItem -Path (Join-Path $env:USERPROFILE "Downloads") -Filter "ssh-key-*.key" -ErrorAction SilentlyContinue

if ($keyFiles) {
    $keyPath = $keyFiles[0].FullName
    Write-Host "Found SSH key: $keyPath" -ForegroundColor Green
} else {
    Write-Host "Enter the full path to your SSH private key:" -ForegroundColor Yellow
    $keyPath = Read-Host "Key path"

    if (-not (Test-Path $keyPath)) {
        Write-Host "Error: Key file not found at $keyPath" -ForegroundColor Red
        exit 1
    }
}

# Get server IP
Write-Host ""
Write-Host "Enter your Oracle Cloud server IP address:" -ForegroundColor Yellow
$serverIP = Read-Host "Server IP"

# Validate IP format (basic)
if ($serverIP -notmatch '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$') {
    Write-Host "Warning: IP format looks incorrect" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 0
    }
}

################################################################################
# Fix SSH Key Permissions (Windows)
################################################################################

Write-Host ""
Write-Host "Fixing SSH key permissions..." -ForegroundColor Cyan

# Remove inheritance and grant only current user read access
$acl = Get-Acl $keyPath
$acl.SetAccessRuleProtection($true, $false)
$acl.Access | ForEach-Object { $acl.RemoveAccessRule($_) } | Out-Null

$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $env:USERNAME,
    "Read",
    "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl $keyPath $acl

Write-Host "Key permissions fixed" -ForegroundColor Green

################################################################################
# Test Connection
################################################################################

Write-Host ""
Write-Host "Testing connection to server..." -ForegroundColor Cyan

$testConnection = ssh -i $keyPath -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$serverIP "echo 'Connection OK'" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Connection successful!" -ForegroundColor Green
} else {
    Write-Host "Warning: Could not connect to server" -ForegroundColor Yellow
    Write-Host "Error: $testConnection" -ForegroundColor Red
    $continue = Read-Host "Continue with upload anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

################################################################################
# Upload Files
################################################################################

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  STARTING FILE UPLOAD" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$currentDir = Get-Location

Write-Host "Uploading from: $currentDir" -ForegroundColor Yellow
Write-Host "To: ubuntu@${serverIP}:~/trading-bot/" -ForegroundColor Yellow
Write-Host ""

# Files to exclude
$excludePatterns = @(
    "*.pyc",
    "__pycache__",
    ".git",
    "venv",
    "env",
    ".vscode",
    ".idea",
    "*.log",
    "upload_to_oracle.ps1",
    "*.key"
)

Write-Host "Excluding:" -ForegroundColor Yellow
$excludePatterns | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
Write-Host ""

# Build SCP command with exclusions
$scpArgs = @(
    "-i", $keyPath,
    "-r",
    "-o", "StrictHostKeyChecking=no"
)

# Add exclude patterns
foreach ($pattern in $excludePatterns) {
    $scpArgs += "--exclude=$pattern"
}

# Add source and destination
$scpArgs += "."
$scpArgs += "ubuntu@${serverIP}:~/trading-bot/"

Write-Host "Starting upload..." -ForegroundColor Cyan
Write-Host ""

# Execute SCP
$uploadResult = & scp @scpArgs 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  UPLOAD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "  UPLOAD FAILED" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Red
    Write-Host $uploadResult -ForegroundColor Red
    exit 1
}

################################################################################
# Verify Upload
################################################################################

Write-Host "Verifying upload..." -ForegroundColor Cyan

$verifyCmd = "ls -lah ~/trading-bot/ | head -20"
$verification = ssh -i $keyPath ubuntu@$serverIP $verifyCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Files on server:" -ForegroundColor Green
    Write-Host $verification
} else {
    Write-Host "Could not verify upload" -ForegroundColor Yellow
}

################################################################################
# Next Steps
################################################################################

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  NEXT STEPS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Connect to your server:" -ForegroundColor Yellow
Write-Host "   ssh -i `"$keyPath`" ubuntu@$serverIP" -ForegroundColor Green
Write-Host ""

Write-Host "2. Run the setup script:" -ForegroundColor Yellow
Write-Host "   cd ~/trading-bot" -ForegroundColor Green
Write-Host "   chmod +x setup_oracle_cloud.sh" -ForegroundColor Green
Write-Host "   ./setup_oracle_cloud.sh" -ForegroundColor Green
Write-Host ""

Write-Host "3. Or install manually:" -ForegroundColor Yellow
Write-Host "   pip3 install -r requirements.txt --break-system-packages" -ForegroundColor Green
Write-Host ""

# Option to connect immediately
Write-Host ""
$connectNow = Read-Host "Connect to server now? (y/n)"

if ($connectNow -eq 'y') {
    Write-Host ""
    Write-Host "Connecting to server..." -ForegroundColor Cyan
    Write-Host "Type 'exit' to disconnect" -ForegroundColor Yellow
    Write-Host ""

    & ssh -i $keyPath ubuntu@$serverIP
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host ""
