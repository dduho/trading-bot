#!/bin/bash
# Script de déploiement et reset complet pour VM

echo "========================================"
echo "🚀 DÉPLOIEMENT & RESET COMPLET"
echo "========================================"
echo ""

# Déterminer le chemin utilisé par systemd
SYSTEMD_PATH=$(systemctl show trading-bot -P WorkingDirectory 2>/dev/null)

if [ -z "$SYSTEMD_PATH" ]; then
    echo "⚠️  Service systemd non trouvé, utilisation du chemin par défaut"
    SYSTEMD_PATH="/home/duhodavid12/trading-bot"
fi

echo "📁 Chemin systemd détecté: $SYSTEMD_PATH"
echo ""

# Arrêter le bot
echo "1️⃣  Arrêt du bot..."
sudo systemctl stop trading-bot 2>/dev/null
pkill -f "python.*run_bot.py" 2>/dev/null
sleep 2
echo "   ✅ Bot arrêté"
echo ""

# Aller dans le bon répertoire
cd "$SYSTEMD_PATH" || exit 1

# Pull dernières modifications
echo "2️⃣  Mise à jour du code..."
git fetch origin main
git reset --hard origin/main
echo "   ✅ Code mis à jour"
echo ""

# Installer/mettre à jour les dépendances
echo "3️⃣  Installation des dépendances..."
./venv/bin/pip install -q -r requirements.txt
echo "   ✅ Dépendances installées"
echo ""

# Reset complet de la base de données
echo "4️⃣  Reset de la base de données..."
rm -f data/trading_history.db
rm -f data/trades.db
echo "   ✅ Base supprimée (0 trades)"
echo ""

# Supprimer les modèles ML
echo "5️⃣  Suppression des modèles ML..."
rm -f models/*.pkl
rm -f models/*.json
echo "   ✅ Modèles supprimés"
echo ""

# Nettoyer les logs
echo "6️⃣  Nettoyage des logs..."
rm -f bot.log
rm -f trading_bot.log
> /dev/null 2>&1
echo "   ✅ Logs nettoyés"
echo ""

# Vérifier le fichier .env
echo "7️⃣  Vérification de .env..."
if [ ! -f .env ]; then
    echo "   ⚠️  Création de .env..."
    cat > .env << 'EOF'
# Trading Configuration
EXCHANGE=binance
API_KEY=T4hfSYwWzYGdHsPu1mHX4xSxQhom0imeA3dfFH1DWMCgrCDXgBToCo0YcGlUi896
API_SECRET=B9iVi9VYhoE5CVDQ5bYsv2XgwRaYHwOpJk644kQWmPSrP9u9Qsd9xnvdkaXhpS0I
TRADING_MODE=paper

# Telegram Notifications
TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
TELEGRAM_CHAT_ID=8350384028
EOF
fi
echo "   ✅ .env vérifié"
echo ""

# Redémarrer le bot
echo "8️⃣  Redémarrage du bot..."
sudo systemctl restart trading-bot
sleep 3
echo ""

# Vérifier le statut
echo "9️⃣  Vérification du statut..."
if sudo systemctl is-active --quiet trading-bot; then
    echo "   ✅ Bot démarré avec succès !"
    
    # Afficher les dernières lignes de logs
    echo ""
    echo "📋 Derniers logs (10s):"
    sleep 7
    sudo journalctl -u trading-bot --since "10 seconds ago" --no-pager | tail -20
else
    echo "   ❌ Erreur au démarrage !"
    echo ""
    echo "📋 Logs d'erreur:"
    sudo journalctl -u trading-bot --since "1 minute ago" --no-pager | tail -30
    exit 1
fi

echo ""
echo "========================================"
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "========================================"
echo ""
echo "📊 État actuel:"
echo "   • Trades: 0"
echo "   • Balance: $10,000"
echo "   • Seuil confiance: 20%"
echo "   • Max positions: 5"
echo "   • Max trades/jour: 50"
echo ""
echo "📱 Testez avec Telegram:"
echo "   /status"
echo ""
