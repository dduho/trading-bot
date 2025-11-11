#!/bin/bash

################################################################################
# RESET AND RESTART - Clean slate pour relancer le bot
################################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}========================================${NC}"
echo -e "${RED}RESET ET REDÉMARRAGE DU BOT${NC}"
echo -e "${RED}========================================${NC}"
echo ""

cd ~/trading-bot || exit 1

echo -e "${YELLOW}[1/5] Arrêt du bot...${NC}"
sudo systemctl stop trading-bot
echo -e "${GREEN}✓ Bot arrêté${NC}"
echo ""

echo -e "${YELLOW}[2/5] Sauvegarde de l'ancienne database...${NC}"
if [ -f "data/trades.db" ]; then
    BACKUP_NAME="trades_backup_$(date +%Y%m%d_%H%M%S).db"
    cp data/trades.db "data/$BACKUP_NAME"
    echo -e "${GREEN}✓ Backup créé: data/$BACKUP_NAME${NC}"
else
    echo -e "${YELLOW}○ Pas de database à sauvegarder${NC}"
fi
echo ""

echo -e "${YELLOW}[3/5] Nettoyage des données...${NC}"
rm -f data/trades.db
rm -f models/*.pkl
rm -f models/*.json
echo -e "${GREEN}✓ Database et modèles ML supprimés${NC}"
echo ""

echo -e "${YELLOW}[4/5] Recréation de la structure...${NC}"
python3 << 'PYEOF'
import sqlite3
import os

db_path = 'data/trades.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tables principales
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
        exit_reason TEXT,
        entry_time TEXT,
        exit_time TEXT,
        duration_minutes REAL,
        trading_mode TEXT,
        rsi REAL,
        macd REAL,
        macd_signal REAL,
        macd_hist REAL,
        sma_short REAL,
        sma_long REAL,
        ema_short REAL,
        ema_long REAL,
        bb_upper REAL,
        bb_middle REAL,
        bb_lower REAL,
        atr REAL,
        volume REAL,
        volume_ratio REAL,
        trend TEXT,
        signal_confidence REAL
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

print("✓ Database recréée")
PYEOF

echo -e "${GREEN}✓ Structure recréée${NC}"
echo ""

echo -e "${YELLOW}[5/5] Redémarrage du bot...${NC}"
sudo systemctl daemon-reload
sudo systemctl start trading-bot
sleep 3

if sudo systemctl is-active --quiet trading-bot; then
    echo -e "${GREEN}✓ Bot redémarré avec succès${NC}"
else
    echo -e "${RED}✗ Erreur au redémarrage${NC}"
    sudo systemctl status trading-bot
    exit 1
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RESET TERMINÉ !${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Le bot repart de zéro avec:"
echo "  • min_confidence: 0.05 (5%)"
echo "  • learning_interval: 0.5h (30min)"
echo "  • Database vierge"
echo "  • Modèles ML à entraîner"
echo ""
echo "Prochaines étapes:"
echo "  1. Attends 30-60 min pour accumuler des trades"
echo "  2. Le premier cycle ML va se déclencher"
echo "  3. Surveille avec: sudo journalctl -u trading-bot -f"
echo ""
