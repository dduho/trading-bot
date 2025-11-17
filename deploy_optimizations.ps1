# Deploy Optimizations to VM
# Usage: .\deploy_optimizations.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TRADING BOT - DEPLOY OPTIMIZATIONS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Commit changes to git
Write-Host "[1/5] Committing changes to git..." -ForegroundColor Yellow
git add .
git commit -m "Autonomous bot optimizations: fixed daily reset, watchdog spam, improved thresholds"
git push origin main
Write-Host "✅ Changes pushed to git" -ForegroundColor Green
Write-Host ""

# 2. Connect to VM and pull changes
Write-Host "[2/5] Pulling changes on VM..." -ForegroundColor Yellow
gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command="cd ~/trading-bot && git pull origin main"
Write-Host "✅ Changes pulled on VM" -ForegroundColor Green
Write-Host ""

# 3. Stop the bot
Write-Host "[3/5] Stopping trading bot..." -ForegroundColor Yellow
gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command="pkill -f 'python.*run_bot.py' || true"
Start-Sleep -Seconds 3
Write-Host "✅ Bot stopped" -ForegroundColor Green
Write-Host ""

# 4. Run autonomous optimizer
Write-Host "[4/5] Running autonomous optimizer..." -ForegroundColor Yellow
gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command="cd ~/trading-bot && python3 autonomous_optimizer.py"
Write-Host "✅ Optimization complete" -ForegroundColor Green
Write-Host ""

# 5. Restart the bot
Write-Host "[5/5] Restarting trading bot..." -ForegroundColor Yellow
gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command="cd ~/trading-bot && nohup python3 run_bot.py > trading_bot.log 2>&1 &"
Start-Sleep -Seconds 5
Write-Host "✅ Bot restarted" -ForegroundColor Green
Write-Host ""

# 6. Show recent logs
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RECENT LOGS (last 30 lines):" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command="tail -n 30 ~/trading-bot/trading_bot.log"
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Monitor with: gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command='tail -f ~/trading-bot/trading_bot.log'" -ForegroundColor Cyan
