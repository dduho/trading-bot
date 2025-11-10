#!/bin/bash
# Script de monitoring du bot en production

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🤖 TRADING BOT - MONITORING PRODUCTION            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Service status
echo "📊 SERVICE STATUS"
echo "─────────────────────────────────────────────────────────────"
systemctl is-active trading-bot > /dev/null 2>&1
if [ $? -eq 0 ]; then
    uptime_info=$(systemctl show trading-bot --property=ActiveEnterTimestamp | cut -d'=' -f2)
    echo "✅ Status: RUNNING"
    echo "⏱  Since: $uptime_info"
else
    echo "❌ Status: STOPPED"
    exit 1
fi
echo ""

# Database stats
echo "💾 DATABASE STATS"
echo "─────────────────────────────────────────────────────────────"
cd /home/duhodavid12/trading-bot
total_trades=$(sqlite3 data/trading_history.db "SELECT COUNT(*) FROM trades;" 2>/dev/null || echo "0")
open_trades=$(sqlite3 data/trading_history.db "SELECT COUNT(*) FROM trades WHERE status='open';" 2>/dev/null || echo "0")
closed_trades=$(sqlite3 data/trading_history.db "SELECT COUNT(*) FROM trades WHERE exit_time IS NOT NULL;" 2>/dev/null || echo "0")
total_pnl=$(sqlite3 data/trading_history.db "SELECT ROUND(COALESCE(SUM(pnl), 0), 2) FROM trades WHERE pnl IS NOT NULL;" 2>/dev/null || echo "0")

echo "📈 Total Trades: $total_trades"
echo "🔓 Open Positions: $open_trades"
echo "🔒 Closed Positions: $closed_trades"
echo "💰 Total PnL: \$$total_pnl USDT"
echo ""

# Recent activity
echo "🔄 RECENT ACTIVITY (last 2 min)"
echo "─────────────────────────────────────────────────────────────"
scans=$(tail -100 /home/duhodavid12/trading-bot/bot.log | grep -c "Fetched 100 candles")
iterations=$(tail -50 /home/duhodavid12/trading-bot/bot.log | grep "Iteration.*complete" | tail -1)
echo "📊 Market Scans: $scans"
if [ ! -z "$iterations" ]; then
    echo "🔁 $iterations"
fi
echo ""

# Notifications
echo "📱 TELEGRAM NOTIFICATIONS"
echo "─────────────────────────────────────────────────────────────"
recent_notifs=$(tail -100 /home/duhodavid12/trading-bot/bot.log | grep -c "sendMessage.*200 OK")
notif_errors=$(tail -100 /home/duhodavid12/trading-bot/bot.log | grep -c "ERROR.*notification")
echo "✅ Sent (last 2min): $recent_notifs"
echo "❌ Errors (last 2min): $notif_errors"
echo ""

# Last trade
echo "💼 LAST TRADE"
echo "─────────────────────────────────────────────────────────────"
last_trade=$(sqlite3 -separator ' | ' data/trading_history.db "
SELECT 
    '#' || id,
    symbol,
    UPPER(side),
    'Entry: $' || ROUND(entry_price, 4),
    CASE 
        WHEN status = 'open' THEN '🟢 OPEN'
        ELSE '🔴 CLOSED'
    END,
    CASE 
        WHEN pnl IS NOT NULL THEN 'PnL: $' || ROUND(pnl, 2)
        ELSE 'Running...'
    END
FROM trades 
ORDER BY id DESC 
LIMIT 1;" 2>/dev/null)

if [ ! -z "$last_trade" ]; then
    echo "$last_trade"
else
    echo "⏳ No trades yet"
fi
echo ""

# Performance today
echo "📅 TODAY'S PERFORMANCE"
echo "─────────────────────────────────────────────────────────────"
today_trades=$(sqlite3 data/trading_history.db "
SELECT COUNT(*) FROM trades 
WHERE DATE(entry_time) = DATE('now');" 2>/dev/null || echo "0")

today_pnl=$(sqlite3 data/trading_history.db "
SELECT ROUND(COALESCE(SUM(pnl), 0), 2) FROM trades 
WHERE DATE(exit_time) = DATE('now') AND pnl IS NOT NULL;" 2>/dev/null || echo "0")

echo "📊 Trades Today: $today_trades"
echo "💵 PnL Today: \$$today_pnl USDT"
echo ""

# System health
echo "🏥 SYSTEM HEALTH"
echo "─────────────────────────────────────────────────────────────"
memory=$(systemctl show trading-bot --property=MemoryCurrent | cut -d'=' -f2)
memory_mb=$((memory / 1024 / 1024))
echo "💾 Memory: ${memory_mb}MB"

# Check for errors
recent_errors=$(tail -100 /home/duhodavid12/trading-bot/bot.log | grep -c "ERROR")
if [ $recent_errors -gt 0 ]; then
    echo "⚠️  Errors (last 2min): $recent_errors"
else
    echo "✅ No errors"
fi
echo ""

# ML System
echo "🧠 ML SYSTEM"
echo "─────────────────────────────────────────────────────────────"
ml_enabled=$(tail -50 /home/duhodavid12/trading-bot/bot.log | grep "Learning System: ENABLED" | wc -l)
if [ $ml_enabled -gt 0 ]; then
    echo "✅ Status: ENABLED"
    echo "⏳ Waiting for 5 closed trades to start learning"
else
    echo "⏸  Status: Waiting for data"
fi
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Use: sudo journalctl -u trading-bot -f  (live logs)      ║"
echo "║  Use: sudo tail -f /home/duhodavid12/trading-bot/bot.log  ║"
echo "╚════════════════════════════════════════════════════════════╝"
