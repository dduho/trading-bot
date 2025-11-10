#!/bin/bash
# Script de gestion du Trading Bot sur VM

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

case "$1" in
    start)
        echo -e "${BLUE}🚀 Démarrage du Trading Bot...${NC}"
        cd ~/trading-bot
        source venv/bin/activate
        nohup python3 run_bot.py > bot.log 2>&1 &
        PID=$!
        echo -e "${GREEN}✅ Bot démarré en arrière-plan (PID: $PID)${NC}"
        echo -e "${BLUE}💡 Pour voir les logs: ./bot_manager.sh logs${NC}"
        sleep 2
        echo -e "\n${BLUE}📋 Dernières lignes des logs:${NC}"
        tail -n 5 ~/trading-bot/bot.log
        ;;
    
    stop)
        echo -e "${YELLOW}🛑 Arrêt du Trading Bot...${NC}"
        pkill -f "python.*run_bot.py" && echo -e "${GREEN}✅ Bot arrêté${NC}" || echo -e "${RED}❌ Aucun bot en cours${NC}"
        ;;
    
    restart)
        echo -e "${BLUE}🔄 Redémarrage du Trading Bot...${NC}"
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        if pgrep -f "python.*run_bot.py" > /dev/null; then
            PID=$(pgrep -f "python.*run_bot.py")
            echo -e "${GREEN}✅ Bot en cours d'exécution (PID: $PID)${NC}"
        else
            echo -e "${RED}❌ Bot arrêté${NC}"
        fi
        ;;
    
    logs)
        echo -e "${BLUE}📋 Logs du bot (Ctrl+C pour quitter):${NC}"
        tail -f ~/trading-bot/bot.log
        ;;
    
    update)
        echo -e "${BLUE}📦 Mise à jour du bot...${NC}"
        cd ~/trading-bot
        $0 stop
        git pull
        source venv/bin/activate
        pip install -r requirements.txt > /dev/null 2>&1
        $0 start
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|update}"
        echo ""
        echo "Commandes disponibles:"
        echo "  start   - Démarrer le bot"
        echo "  stop    - Arrêter le bot"
        echo "  restart - Redémarrer le bot"
        echo "  status  - Vérifier si le bot tourne"
        echo "  logs    - Afficher les logs en temps réel"
        echo "  update  - Mettre à jour et redémarrer le bot"
        exit 1
        ;;
esac
