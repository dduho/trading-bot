#!/bin/bash
# Script de déploiement automatique sur Google Cloud VM

echo "🚀 Déploiement Trading Bot sur VM"
echo "=" 

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier si le dossier existe
if [ -d "trading-bot" ]; then
    echo -e "${BLUE}📂 Dossier trading-bot trouvé, mise à jour...${NC}"
    cd trading-bot
    git pull
else
    echo -e "${BLUE}📦 Clonage du repository...${NC}"
    git clone https://github.com/dduho/trading-bot.git
    cd trading-bot
fi

# 2. Créer l'environnement virtuel s'il n'existe pas
if [ ! -d "venv" ]; then
    echo -e "${BLUE}🐍 Création de l'environnement virtuel...${NC}"
    python3 -m venv venv
fi

# 3. Activer l'environnement virtuel
echo -e "${BLUE}⚡ Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

# 4. Installer/Mettre à jour les dépendances
echo -e "${BLUE}📦 Installation des dépendances...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 5. Vérifier/Créer le fichier .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Fichier .env manquant${NC}"
    echo -e "${BLUE}📝 Création du fichier .env...${NC}"
    
    # Créer .env avec les variables nécessaires
    cat > .env << 'EOF'
# Trading Bot Configuration
EXCHANGE=binance
API_KEY=T4hfSYwWzYGdHsPu1mHX4xSxQhom0imeA3dfFH1DWMCgrCDXgBToCo0YcGlUi896
API_SECRET=B9iVi9VYhoE5CVDQ5bYsv2XgwRaYHwOpJk644kQWmPSrP9u9Qsd9xnvdkaXhpS0I
TRADING_MODE=paper
DEFAULT_SYMBOL=BTC/USDT
TIMEFRAME=1m
UPDATE_INTERVAL=10
MAX_POSITION_SIZE=0.1
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=5.0
MAX_DAILY_LOSS=5.0
RSI_PERIOD=14
RSI_OVERBOUGHT=70
RSI_OVERSOLD=30
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
ENABLE_LOGGING=true
LOG_LEVEL=DEBUG

# Telegram Notifications
TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
TELEGRAM_CHAT_ID=8350384028
EOF
    echo -e "${GREEN}✅ Fichier .env créé${NC}"
else
    echo -e "${GREEN}✅ Fichier .env existe déjà${NC}"
fi

# 6. Tester la connexion Telegram
echo -e "${BLUE}📱 Test des notifications Telegram...${NC}"
python3 scripts/test_telegram.py

# 7. Arrêter le bot s'il tourne déjà
echo -e "${BLUE}🛑 Arrêt du bot existant...${NC}"
pkill -f "python.*run_bot.py" || echo "Aucun bot en cours d'exécution"

# 8. Démarrer le bot en arrière-plan
echo -e "${BLUE}🚀 Démarrage du bot...${NC}"
nohup python3 run_bot.py > bot.log 2>&1 &
BOT_PID=$!

echo -e "${GREEN}✅ Bot démarré (PID: $BOT_PID)${NC}"

# 9. Afficher les logs
echo ""
echo -e "${BLUE}📋 Logs du bot (Ctrl+C pour quitter, le bot continue en arrière-plan):${NC}"
sleep 2
tail -f bot.log
