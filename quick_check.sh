#!/bin/bash
# Quick check if bot is trading

echo "=== BOT STATUS CHECK ==="
echo "Time: $(date '+%H:%M:%S')"
echo ""

# Get last 5 opened positions
echo "Last 5 trades:"
gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="grep 'Opened.*position' /home/black/trading-bot/trading_bot.log | tail -n 5" | while read line; do
    timestamp=$(echo "$line" | cut -d' ' -f1-2)
    symbol=$(echo "$line" | grep -oP '(SOL|AVAX|MATIC|DOGE|ADA)/USDT')
    echo "  $timestamp - $symbol"
done

echo ""

# Check if recent (last 30 min)
last_trade=$(gcloud compute ssh trading-bot-instance --zone=europe-west1-d --command="grep 'Opened.*position' /home/black/trading-bot/trading_bot.log | tail -n 1")

if [ -n "$last_trade" ]; then
    timestamp=$(echo "$last_trade" | cut -d' ' -f1-2)
    echo "Last trade: $timestamp"
    echo ""

    # Parse time (rough check)
    last_hour=$(echo "$timestamp" | cut -d':' -f1 | cut -d' ' -f2)
    current_hour=$(date '+%H')

    if [ "$last_hour" == "$current_hour" ] || [ "$((current_hour - last_hour))" -le 1 ]; then
        echo "✅ STATUS: TRADING (recent activity)"
    else
        echo "⚠️ STATUS: MIGHT BE STOPPED (old timestamp)"
    fi
else
    echo "❌ STATUS: NO TRADES FOUND"
fi

echo ""
echo "========================"
