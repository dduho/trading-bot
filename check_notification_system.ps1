#!/usr/bin/env pwsh
# Quick check script for trading bot notification system

Write-Host "`n🔍 TRADING BOT NOTIFICATION SYSTEM CHECK" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

# Check bot status
Write-Host "📊 Bot Status:" -ForegroundColor Yellow
gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="sudo systemctl is-active trading-bot && echo '✅ Bot is running' || echo '❌ Bot is stopped'"

# Check if event loop started
Write-Host "`n📡 Event Loop Status:" -ForegroundColor Yellow
gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="sudo grep 'Notification event loop started' /home/duhodavid12/trading-bot/trading_bot.log | tail -1"

# Check for recent notifications
Write-Host "`n📤 Recent Notifications (last 5):" -ForegroundColor Yellow
gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="sudo grep -E '(sendMessage.*200 OK|Telegram notification sent successfully)' /home/duhodavid12/trading-bot/trading_bot.log | tail -5"

# Check for Pool timeout errors (should be ZERO with new system)
Write-Host "`n⚠️  Pool Timeout Errors:" -ForegroundColor Yellow
$errors = gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="sudo grep 'Pool timeout' /home/duhodavid12/trading-bot/trading_bot.log | wc -l"
if ($errors -eq 0) {
    Write-Host "✅ No pool timeout errors found!" -ForegroundColor Green
} else {
    Write-Host "❌ Found $errors pool timeout errors" -ForegroundColor Red
}

# Check for recent trades
Write-Host "`n💰 Recent Trades (last 3):" -ForegroundColor Yellow
gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="sudo grep 'Trade recorded' /home/duhodavid12/trading-bot/trading_bot.log | tail -3"

# Bot uptime
Write-Host "`n⏱️  Bot Uptime:" -ForegroundColor Yellow
gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="sudo systemctl show trading-bot -p ActiveEnterTimestamp --no-pager"

Write-Host "`n=========================================`n" -ForegroundColor Cyan
Write-Host "✅ Check complete!`n" -ForegroundColor Green
