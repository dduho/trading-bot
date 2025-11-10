#!/bin/bash
# Script pour corriger et configurer le service systemd

echo "🔧 Configuration du service systemd pour le Trading Bot"
echo "========================================================"

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ce script doit être exécuté avec sudo"
    echo "Utilisation: sudo bash fix_systemd.sh"
    exit 1
fi

# Arrêter le service actuel
echo "🛑 Arrêt du service actuel..."
systemctl stop trading-bot.service

# Créer le nouveau fichier de service
echo "📝 Création du fichier de service corrigé..."
cat > /etc/systemd/system/trading-bot.service << 'EOF'
[Unit]
Description=Trading Bot with Machine Learning
After=network.target

[Service]
Type=simple
User=duhodavid12
WorkingDirectory=/home/duhodavid12/trading-bot
Environment="PATH=/home/duhodavid12/trading-bot/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/duhodavid12/trading-bot/venv/bin/python3 /home/duhodavid12/trading-bot/run_bot.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/duhodavid12/trading-bot/bot.log
StandardError=append:/home/duhodavid12/trading-bot/bot.log

[Install]
WantedBy=multi-user.target
EOF

# Recharger systemd
echo "🔄 Rechargement de systemd..."
systemctl daemon-reload

# Activer le service
echo "✅ Activation du service..."
systemctl enable trading-bot.service

echo ""
echo "✅ Configuration terminée!"
echo ""
echo "📋 Commandes disponibles:"
echo "  sudo systemctl start trading-bot    - Démarrer le bot"
echo "  sudo systemctl stop trading-bot     - Arrêter le bot"
echo "  sudo systemctl restart trading-bot  - Redémarrer le bot"
echo "  sudo systemctl status trading-bot   - Voir le statut"
echo "  journalctl -u trading-bot -f        - Voir les logs en temps réel"
echo ""
echo "💡 Vous pouvez aussi utiliser: ./bot_manager.sh"
