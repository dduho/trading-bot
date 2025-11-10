#!/bin/bash

################################################################################
# Production Setup Script
# Creates necessary directories and validates configuration
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Trading Bot - Production Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running in correct directory
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}ERROR: config.yaml not found!${NC}"
    echo "Please run this script from the trading-bot directory"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p data models logs

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env created from .env.example${NC}"
        echo -e "${YELLOW}⚠ IMPORTANT: Edit .env and add your credentials!${NC}"
    else
        echo -e "${RED}ERROR: .env.example not found!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Check .env has required variables
echo -e "${YELLOW}Validating .env configuration...${NC}"

check_env_var() {
    local var_name=$1
    local var_value=$(grep "^$var_name=" .env 2>/dev/null | cut -d'=' -f2)

    if [ -z "$var_value" ] || [ "$var_value" = "your_${var_name,,}_here" ] || [[ "$var_value" =~ "your_" ]]; then
        echo -e "${RED}✗ $var_name not configured${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $var_name configured${NC}"
        return 0
    fi
}

all_configured=true

check_env_var "TELEGRAM_BOT_TOKEN" || all_configured=false
check_env_var "TELEGRAM_CHAT_ID" || all_configured=false
check_env_var "API_KEY" || echo -e "${YELLOW}⚠ API_KEY not set (OK if paper trading)${NC}"
check_env_var "API_SECRET" || echo -e "${YELLOW}⚠ API_SECRET not set (OK if paper trading)${NC}"

echo ""

if [ "$all_configured" = false ]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}CONFIGURATION REQUIRED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Edit .env and configure:"
    echo "  1. TELEGRAM_BOT_TOKEN (from @BotFather)"
    echo "  2. TELEGRAM_CHAT_ID (your Telegram user ID)"
    echo ""
    echo "To get your Telegram Chat ID:"
    echo "  1. Message your bot on Telegram"
    echo "  2. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
    echo "  3. Look for \"chat\":{\"id\":YOUR_ID}"
    echo ""
    exit 1
fi

# Test Python dependencies
echo -e "${YELLOW}Checking Python dependencies...${NC}"
python3 -c "import ccxt, pandas, sklearn, telegram" 2>/dev/null && \
    echo -e "${GREEN}✓ All Python dependencies installed${NC}" || \
    echo -e "${YELLOW}⚠ Some Python dependencies missing (run: pip3 install -r requirements.txt)${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SETUP COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Review config.yaml settings"
echo "  2. Start the bot: sudo systemctl start trading-bot"
echo "  3. Check logs: sudo journalctl -u trading-bot -f"
echo "  4. Send /start to your Telegram bot"
echo ""
echo -e "${YELLOW}Directory structure:${NC}"
ls -la data/ models/ logs/ 2>/dev/null || echo "Directories created"
echo ""
