#!/usr/bin/env python3
"""
Market Alerts Runner - Surveillance des indices et actions
Lance en parallèle du bot principal
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from market_alerts import MarketAlertsSystem
from telegram_notifier import TelegramNotifier
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_alerts.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for market alerts"""
    load_dotenv()

    print("=" * 67)
    print("          MARKET ALERTS SYSTEM - Indices & Stocks               ")
    print("=" * 67)
    print()

    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Initialize Telegram notifier
    telegram = TelegramNotifier(config)

    # Initialize market alerts system
    alerts = MarketAlertsSystem(config, telegram)

    if not alerts.enabled:
        logger.warning("Market alerts system is disabled in config")
        print("⚠️ Market alerts disabled in config.yaml")
        return

    # Get check interval
    check_interval = alerts.alerts_config.get('check_interval_minutes', 15)

    print(f"✅ Market Alerts System started")
    print(f"📊 Check interval: {check_interval} minutes")
    print(f"🔔 Telegram notifications: {'Enabled' if telegram.enabled else 'Disabled'}")
    print()

    # Main loop
    # (Startup notification sent by first iteration)
    iteration = 0
    try:
        while True:
            iteration += 1
            logger.info(f"=" * 50)
            logger.info(f"Iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Check all markets
            alerts.check_all_markets()

            logger.info(f"✓ Market check complete. Next check in {check_interval} minutes")

            # Wait until next check
            time.sleep(check_interval * 60)

    except KeyboardInterrupt:
        logger.info("Market alerts system stopped by user")
        print("\n\n👋 Market Alerts System stopped")

    except Exception as e:
        logger.error(f"Fatal error in market alerts: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
