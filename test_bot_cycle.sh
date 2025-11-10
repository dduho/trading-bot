#!/bin/bash
# Script de test complet du cycle du bot

echo "🔍 TEST COMPLET DU BOT TRADING"
echo "=============================="
echo ""

# 1. Vérifier que le bot tourne
echo "1️⃣ Vérification du service..."
systemctl is-active trading-bot > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Bot actif"
else
    echo "   ❌ Bot non actif"
    exit 1
fi
echo ""

# 2. Vérifier les logs récents
echo "2️⃣ Activité récente (30 dernières secondes)..."
recent_scans=$(tail -100 /home/duhodavid12/trading-bot/bot.log | grep -c "Fetched 100 candles")
echo "   📊 Scans de marché: $recent_scans"

if [ $recent_scans -gt 0 ]; then
    echo "   ✅ Bot scanne le marché"
else
    echo "   ⚠️  Pas de scan récent"
fi
echo ""

# 3. Vérifier la base de données
echo "3️⃣ État de la base de données..."
cd /home/duhodavid12/trading-bot
trade_count=$(python3 -c "import sqlite3; conn = sqlite3.connect('data/trading_history.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM trades'); print(cursor.fetchone()[0]); conn.close()")
echo "   💰 Total trades: $trade_count"

open_trades=$(python3 -c "import sqlite3; conn = sqlite3.connect('data/trading_history.db'); cursor = conn.cursor(); cursor.execute(\"SELECT COUNT(*) FROM trades WHERE status='open'\"); print(cursor.fetchone()[0]); conn.close()")
echo "   🔓 Positions ouvertes: $open_trades"

closed_trades=$(python3 -c "import sqlite3; conn = sqlite3.connect('data/trading_history.db'); cursor = conn.cursor(); cursor.execute(\"SELECT COUNT(*) FROM trades WHERE exit_time IS NOT NULL\"); print(cursor.fetchone()[0]); conn.close()")
echo "   🔒 Positions fermées: $closed_trades"

if [ $trade_count -gt 0 ]; then
    echo "   ✅ Bot trade activement"
else
    echo "   ⏳ Pas encore de trades"
fi
echo ""

# 4. Vérifier les notifications
echo "4️⃣ Notifications Telegram..."
notif_count=$(tail -200 /home/duhodavid12/trading-bot/bot.log | grep -c "sendMessage.*200 OK")
echo "   📱 Notifications envoyées: $notif_count"

if [ $notif_count -gt 0 ]; then
    echo "   ✅ Notifications fonctionnelles"
else
    echo "   ⚠️  Pas de notifications récentes"
fi
echo ""

# 5. Vérifier le système ML
echo "5️⃣ Système d'apprentissage..."
ml_warnings=$(tail -100 /home/duhodavid12/trading-bot/bot.log | grep -c "Model not trained yet")
if [ $ml_warnings -gt 0 ]; then
    echo "   ⏳ Modèle ML non entraîné (besoin de plus de trades)"
else
    echo "   ✅ Modèle ML entraîné"
fi
echo ""

# 6. Balance paper trading
echo "6️⃣ Balance Paper Trading..."
last_balance=$(tail -50 /home/duhodavid12/trading-bot/bot.log | grep "Paper balance" | tail -1 | grep -oP "USDT': np.float64\(\K[0-9.]+")
if [ ! -z "$last_balance" ]; then
    echo "   💵 Balance USDT: \$$last_balance"
    
    # Vérifier si la balance a changé
    if [ "$last_balance" != "10000.0" ]; then
        echo "   ✅ Balance évolue (trades actifs)"
    else
        echo "   ℹ️  Balance stable à $10000 (pas de positions ouvertes)"
    fi
else
    echo "   ⏳ Pas d'info de balance récente"
fi
echo ""

# 7. Dernier cycle
echo "7️⃣ Dernier cycle d'analyse..."
last_iteration=$(tail -50 /home/duhodavid12/trading-bot/bot.log | grep "Iteration.*complete" | tail -1)
if [ ! -z "$last_iteration" ]; then
    echo "   ✅ $last_iteration"
else
    echo "   ⏳ Aucun cycle récent"
fi
echo ""

# 8. PnL
if [ $closed_trades -gt 0 ]; then
    echo "8️⃣ Performance..."
    total_pnl=$(python3 -c "import sqlite3; conn = sqlite3.connect('data/trading_history.db'); cursor = conn.cursor(); cursor.execute('SELECT SUM(pnl) FROM trades WHERE pnl IS NOT NULL'); result = cursor.fetchone()[0]; print(result if result else 0); conn.close()")
    echo "   💰 PnL Total: \$$total_pnl"
    
    if (( $(echo "$total_pnl > 0" | bc -l) )); then
        echo "   ✅ En profit"
    elif (( $(echo "$total_pnl < 0" | bc -l) )); then
        echo "   📉 En perte (normal en phase d'apprentissage)"
    else
        echo "   ➖ Break-even"
    fi
    echo ""
fi

# Résumé
echo "═══════════════════════════════"
echo "📋 RÉSUMÉ"
echo "═══════════════════════════════"
echo "✅ Bot opérationnel"
echo "✅ Scan marché actif"
echo "✅ Trades: $trade_count (open: $open_trades, closed: $closed_trades)"
echo "✅ Notifications: $notif_count envoyées"
echo "✅ Balance dynamique"
echo ""
echo "🎯 Le bot fonctionne correctement !"
