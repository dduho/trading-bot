#!/bin/bash
# Script de réinitialisation SIMPLE et RAPIDE

echo "🔄 RESET DU BOT"
echo ""

# Arrêter le bot
echo "Arrêt du bot..."
pkill -f "python.*run_bot.py" 2>/dev/null
sudo systemctl stop trading-bot 2>/dev/null
sleep 2

# Supprimer la database
echo "Suppression de la base de données..."
rm -f ~/trading-bot/data/trading_history.db
rm -f ~/trading-bot/data/trades.db
echo "✅ Database supprimée"

# Supprimer les modèles ML
echo "Suppression des modèles ML..."
rm -f ~/trading-bot/models/*.pkl
rm -f ~/trading-bot/models/*.json
echo "✅ Modèles supprimés"

# Supprimer les logs
echo "Nettoyage des logs..."
rm -f ~/trading-bot/bot.log
rm -f ~/trading-bot/trading_bot.log
echo "✅ Logs nettoyés"

echo ""
echo "✅ RESET TERMINÉ!"
echo ""
echo "Le bot repart à ZÉRO:"
echo "  • 0 trades"
echo "  • $10,000 capital"
echo "  • Apprentissage depuis le début"
echo ""
echo "Redémarrez avec: ./bot_manager.sh start"
