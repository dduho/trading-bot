#!/bin/bash
# Script de réinitialisation complète du bot

echo "🔄 RÉINITIALISATION DU BOT DE TRADING"
echo "======================================"
echo ""

# Vérifier si on est dans le bon dossier
if [ ! -f "run_bot.py" ]; then
    echo "❌ Erreur: Exécutez ce script depuis le dossier trading-bot"
    exit 1
fi

# Confirmation
read -p "⚠️  ATTENTION: Cela va supprimer toutes les données d'apprentissage. Continuer? (oui/non): " confirm
if [ "$confirm" != "oui" ]; then
    echo "❌ Annulé"
    exit 0
fi

echo ""
echo "1️⃣ Arrêt du bot..."
./bot_manager.sh stop 2>/dev/null || pkill -f "python.*run_bot.py"

echo "2️⃣ Sauvegarde de l'ancienne base de données..."
if [ -f "data/trades.db" ]; then
    timestamp=$(date +%Y%m%d_%H%M%S)
    cp data/trades.db "data/trades_backup_${timestamp}.db"
    echo "✅ Sauvegarde créée: trades_backup_${timestamp}.db"
fi

echo "3️⃣ Suppression de la base de données..."
rm -f data/trades.db
echo "✅ Base de données supprimée"

echo "4️⃣ Suppression des modèles ML..."
rm -f models/*.pkl
rm -f models/*.json
echo "✅ Modèles ML supprimés"

echo "5️⃣ Suppression des logs..."
rm -f bot.log
rm -f trading_bot.log
echo "✅ Logs supprimés"

echo ""
echo "✅ RÉINITIALISATION TERMINÉE"
echo ""
echo "Le bot va maintenant :"
echo "  • Repartir avec $10,000 en mode paper"
echo "  • Commencer avec des limites basses"
echo "  • Apprendre progressivement de chaque trade"
echo ""
echo "Pour démarrer le bot :"
echo "  ./bot_manager.sh start"
echo ""
