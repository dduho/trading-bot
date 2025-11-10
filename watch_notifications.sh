#!/bin/bash
# Script pour monitorer les notifications en temps réel

echo "🔍 Monitoring Trading Bot Notifications..."
echo "=========================================="
echo ""

# Show current status
echo "📊 Current Bot Status:"
gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="sudo systemctl status trading-bot --no-pager | head -15"
echo ""

# Watch for notifications in real-time
echo "📱 Watching for notification events (Ctrl+C to stop):"
echo "------------------------------------------------------"
gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="sudo tail -f /home/duhodavid12/trading-bot/trading_bot.log | grep --line-buffered -E '(📤|✅|❌|Trade recorded|sendMessage|Pool timeout|LONG|SHORT|notification)'"
