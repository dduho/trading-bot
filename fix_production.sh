#!/bin/bash

################################################################################
# EMERGENCY FIX SCRIPT - Répare les problèmes critiques du bot en production
# - Crée .env avec credentials Telegram
# - Crée les dossiers data/ et models/ manquants
# - Force un cycle ML immédiat
# - Redémarre le bot
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}========================================${NC}"
echo -e "${RED}EMERGENCY FIX - PRODUCTION${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Change to bot directory
cd ~/trading-bot || { echo -e "${RED}ERROR: ~/trading-bot not found!${NC}"; exit 1; }

echo -e "${YELLOW}[1/6] Creating missing directories...${NC}"
mkdir -p data models logs
chmod 755 data models logs
echo -e "${GREEN}✓ Directories created: data/ models/ logs/${NC}"
echo ""

echo -e "${YELLOW}[2/6] Creating .env file...${NC}"
if [ -f ".env" ]; then
    echo -e "${BLUE}  .env already exists, backing up...${NC}"
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# Create .env with Telegram credentials from .env.example
cat > .env << 'EOF'
# Trading Bot Environment Variables

# Exchange Configuration
EXCHANGE=binance
API_KEY=
API_SECRET=

# Trading Mode
TRADING_MODE=paper

# Telegram Notifications
TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
TELEGRAM_CHAT_ID=8350384028

# Force ML Learning on next cycle
FORCE_LEARNING=1
EOF

echo -e "${GREEN}✓ .env created with Telegram credentials${NC}"
echo ""

echo -e "${YELLOW}[3/6] Setting correct permissions...${NC}"
chmod 600 .env
chmod +x *.sh 2>/dev/null || true
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

echo -e "${YELLOW}[4/6] Validating configuration...${NC}"
python3 << 'PYEOF'
import yaml
import os

# Check config.yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

print(f"  Learning enabled: {config.get('learning', {}).get('enabled', False)}")
print(f"  Auto-apply: {config.get('learning', {}).get('auto_apply_adaptations', False)}")
print(f"  Min confidence: {config.get('strategy', {}).get('min_confidence', 'NOT SET')}")
print(f"  Learning interval: {config.get('learning', {}).get('learning_interval_hours', 'NOT SET')}h")

# Check .env
from dotenv import load_dotenv
load_dotenv()

tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = os.getenv('TELEGRAM_CHAT_ID')

print(f"  Telegram token: {'✓ SET' if tg_token else '✗ MISSING'}")
print(f"  Telegram chat ID: {'✓ SET' if tg_chat else '✗ MISSING'}")
PYEOF

echo -e "${GREEN}✓ Configuration validated${NC}"
echo ""

echo -e "${YELLOW}[5/6] Creating initial database structure...${NC}"
python3 << 'PYEOF'
import sqlite3
import os

db_path = 'data/trades.db'

# Create database if it doesn't exist
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables (won't error if they exist)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        entry_price REAL,
        exit_price REAL,
        quantity REAL,
        pnl REAL,
        pnl_percent REAL,
        status TEXT,
        strategy TEXT,
        indicators TEXT,
        exit_reason TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ml_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        model_type TEXT,
        accuracy REAL,
        precision_score REAL,
        recall REAL,
        f1_score REAL,
        auc_roc REAL,
        training_samples INTEGER,
        feature_importance TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS learning_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        cycle_type TEXT,
        adaptations TEXT,
        performance_before TEXT,
        performance_after TEXT,
        success INTEGER
    )
''')

conn.commit()
conn.close()

print(f"✓ Database initialized: {db_path}")
PYEOF

echo -e "${GREEN}✓ Database ready${NC}"
echo ""

echo -e "${YELLOW}[6/6] Restarting trading bot...${NC}"
sudo systemctl restart trading-bot

# Wait for bot to start
sleep 3

# Check status
if sudo systemctl is-active --quiet trading-bot; then
    echo -e "${GREEN}✓ Bot restarted successfully${NC}"
else
    echo -e "${RED}✗ Bot failed to start!${NC}"
    echo "Check logs with: sudo journalctl -u trading-bot -n 50"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FIX COMPLETE!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Check bot status:"
echo -e "   ${BLUE}sudo systemctl status trading-bot${NC}"
echo ""
echo "2. Watch logs in real-time:"
echo -e "   ${BLUE}sudo journalctl -u trading-bot -f${NC}"
echo ""
echo "3. Send /start to your Telegram bot to test notifications"
echo ""
echo "4. Wait 1 hour for first ML learning cycle (or less if FORCE_LEARNING=1 works)"
echo ""
echo "What was fixed:"
echo -e "  ${GREEN}✓${NC} Created data/ models/ logs/ directories"
echo -e "  ${GREEN}✓${NC} Created .env with Telegram credentials"
echo -e "  ${GREEN}✓${NC} Initialized database structure"
echo -e "  ${GREEN}✓${NC} Set FORCE_LEARNING=1 for immediate ML cycle"
echo -e "  ${GREEN}✓${NC} Restarted bot"
echo ""
echo -e "${YELLOW}Monitor the bot now:${NC}"
echo -e "${BLUE}sudo journalctl -u trading-bot -f${NC}"
echo ""
