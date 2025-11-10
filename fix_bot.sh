#!/bin/bash

# Script de diagnostic et réparation du bot
echo "============================================"
echo "Diagnostic et réparation du Trading Bot"
echo "============================================"

# 1. Arrêter le bot
echo ""
echo "1. Arrêt du bot..."
bash bot_manager.sh stop

# 2. Créer les dossiers manquants
echo ""
echo "2. Création des dossiers nécessaires..."
mkdir -p data
mkdir -p models
mkdir -p logs

# 3. Supprimer l'ancienne base si elle existe
echo ""
echo "3. Nettoyage de l'ancienne base..."
rm -f data/trading_history.db
rm -f data/trades.db
rm -f models/*.pkl
rm -f models/*.json
rm -f *.log

# 4. Vérifier les variables d'environnement
echo ""
echo "4. Vérification des variables d'environnement..."
if [ -f .env ]; then
    echo "   ✓ Fichier .env trouvé"
    
    # Vérifier Telegram
    if grep -q "TELEGRAM_BOT_TOKEN=" .env && grep -q "TELEGRAM_CHAT_ID=" .env; then
        echo "   ✓ Variables Telegram configurées"
    else
        echo "   ✗ Variables Telegram manquantes dans .env"
        echo ""
        echo "   Ajout des variables Telegram..."
        echo "" >> .env
        echo "# Telegram Notifications" >> .env
        echo "TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI" >> .env
        echo "TELEGRAM_CHAT_ID=8350384028" >> .env
    fi
else
    echo "   ✗ Fichier .env manquant !"
    echo "   Création du fichier .env..."
    cat > .env << 'EOF'
# Trading Configuration
EXCHANGE=binance
API_KEY=T4hfSYwWzYGdHsPu1mHX4xSxQhom0imeA3dfFH1DWMCgrCDXgBToCo0YcGlUi896
API_SECRET=B9iVi9VYhoE5CVDQ5bYsv2XgwRaYHwOpJk644kQWmPSrP9u9Qsd9xnvdkaXhppS0I
TRADING_MODE=paper

# Telegram Notifications
TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
TELEGRAM_CHAT_ID=8350384028
EOF
    echo "   ✓ Fichier .env créé"
fi

# 5. Vérifier config.yaml
echo ""
echo "5. Vérification de config.yaml..."
if [ -f config.yaml ]; then
    echo "   ✓ Fichier config.yaml trouvé"
else
    echo "   ✗ Fichier config.yaml manquant !"
fi

# 6. Tester l'import Python
echo ""
echo "6. Test des imports Python..."
~/trading-bot/venv/bin/python3 << 'PYEOF'
try:
    print("   - Import TradingBot...", end=" ")
    from src.trading_bot import TradingBot
    print("✓")
    
    print("   - Import TelegramNotifier...", end=" ")
    from src.telegram_notifier import TelegramNotifier
    print("✓")
    
    print("   - Import TradeDatabase...", end=" ")
    from src.trade_database import TradeDatabase
    print("✓")
    
    print("   - Création base de données...", end=" ")
    db = TradeDatabase()
    print("✓")
    
except Exception as e:
    print(f"\n   ✗ Erreur: {e}")
PYEOF

# 7. Afficher la configuration
echo ""
echo "7. Configuration actuelle:"
~/trading-bot/venv/bin/python3 << 'PYEOF'
import yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print(f"   - Mode: {config['trading']['mode']}")
    print(f"   - Symboles: {', '.join(config['trading']['symbols'])}")
    print(f"   - Timeframe: {config['trading']['timeframe']}")
    print(f"   - Scan interval: {config['trading']['scan_interval_seconds']}s")
    print(f"   - Min confidence: {config['ml_optimizer']['min_confidence']*100}%")
    print(f"   - Max positions: {config['risk_management']['max_open_positions']}")
    print(f"   - Max trades/jour: {config['risk_management']['max_daily_trades']}")
PYEOF

# 8. Démarrer le bot
echo ""
echo "8. Démarrage du bot..."
bash bot_manager.sh start

echo ""
echo "============================================"
echo "Réparation terminée !"
echo "============================================"
echo ""
echo "Vérifiez les logs avec:"
echo "  ./bot_manager.sh logs"
echo ""
echo "Testez Telegram avec la commande:"
echo "  /status"
echo ""
