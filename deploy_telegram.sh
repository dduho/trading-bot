#!/bin/bash
# Script de déploiement automatisé Telegram sur VM

echo "=========================================="
echo "  DÉPLOIEMENT TELEGRAM SUR VM"
echo "=========================================="
echo ""

# Couleurs pour output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Étape 1: Pull des derniers changements
echo -e "${YELLOW}[1/7] Pull des derniers changements Git...${NC}"
if git pull origin main; then
    echo -e "${GREEN}✓ Git pull réussi${NC}"
else
    echo -e "${RED}✗ Erreur lors du git pull${NC}"
    exit 1
fi
echo ""

# Étape 2: Vérifier Python
echo -e "${YELLOW}[2/7] Vérification de Python...${NC}"
python_version=$(python --version 2>&1)
echo "Python version: $python_version"
echo -e "${GREEN}✓ Python disponible${NC}"
echo ""

# Étape 3: Installer les dépendances
echo -e "${YELLOW}[3/7] Installation des dépendances...${NC}"
if pip install python-telegram-bot==20.7; then
    echo -e "${GREEN}✓ python-telegram-bot installé${NC}"
else
    echo -e "${RED}✗ Erreur lors de l'installation${NC}"
    exit 1
fi
echo ""

# Étape 4: Vérifier le fichier .env
echo -e "${YELLOW}[4/7] Vérification du fichier .env...${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}✓ Fichier .env trouvé${NC}"
    
    # Vérifier les credentials Telegram
    if grep -q "TELEGRAM_BOT_TOKEN" .env && grep -q "TELEGRAM_CHAT_ID" .env; then
        echo -e "${GREEN}✓ Credentials Telegram présents${NC}"
    else
        echo -e "${RED}✗ Credentials Telegram manquants dans .env${NC}"
        echo "Veuillez ajouter:"
        echo "TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI"
        echo "TELEGRAM_CHAT_ID=8350384028"
        exit 1
    fi
else
    echo -e "${RED}✗ Fichier .env non trouvé${NC}"
    echo "Création du fichier .env..."
    cat > .env << EOF
# Trading Bot Environment Variables
EXCHANGE=binance
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
TRADING_MODE=paper

# Telegram Notifications
TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
TELEGRAM_CHAT_ID=8350384028
EOF
    echo -e "${GREEN}✓ Fichier .env créé${NC}"
fi
echo ""

# Étape 5: Tester la connexion Telegram
echo -e "${YELLOW}[5/7] Test de connexion Telegram...${NC}"
if python scripts/test_telegram.py; then
    echo -e "${GREEN}✓ Connexion Telegram OK${NC}"
else
    echo -e "${RED}✗ Échec de connexion Telegram${NC}"
    echo "Vérifiez vos credentials dans .env"
    exit 1
fi
echo ""

# Étape 6: Arrêter l'ancien bot
echo -e "${YELLOW}[6/7] Arrêt de l'ancien bot (si actif)...${NC}"
bot_pid=$(ps aux | grep "[p]ython run_bot.py" | awk '{print $2}')
if [ -n "$bot_pid" ]; then
    echo "Bot trouvé avec PID: $bot_pid"
    kill $bot_pid
    sleep 2
    echo -e "${GREEN}✓ Ancien bot arrêté${NC}"
else
    echo "Aucun bot en cours d'exécution"
fi
echo ""

# Étape 7: Démarrer le nouveau bot
echo -e "${YELLOW}[7/7] Démarrage du bot avec notifications Telegram...${NC}"
nohup python run_bot.py > bot.log 2>&1 &
new_pid=$!
sleep 3

# Vérifier que le bot démarre
if ps -p $new_pid > /dev/null; then
    echo -e "${GREEN}✓ Bot démarré avec succès (PID: $new_pid)${NC}"
    
    # Afficher les dernières lignes de log
    echo ""
    echo "Dernières lignes de log:"
    echo "------------------------"
    tail -15 bot.log
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  ✓ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
    echo "==========================================${NC}"
    echo ""
    echo "Bot PID: $new_pid"
    echo "Logs: tail -f bot.log"
    echo ""
    echo "Vous devriez recevoir un message de démarrage sur Telegram!"
else
    echo -e "${RED}✗ Erreur: Le bot n'a pas démarré${NC}"
    echo "Vérifiez les logs: cat bot.log"
    exit 1
fi
