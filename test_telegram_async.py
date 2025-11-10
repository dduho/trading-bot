#!/usr/bin/env python3
"""Test notification Telegram avec asyncio"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

import yaml
from telegram_notifier import TelegramNotifier

async def main():
    """Envoie une notification de test"""
    try:
        print("🔍 Chargement configuration...")
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("🔍 Initialisation notifier...")
        notifier = TelegramNotifier(config)
        
        print(f"   Token: {notifier.bot_token[:20]}...")
        print(f"   Chat ID: {notifier.chat_id}")
        
        print("\n📤 Envoi notification...")
        await notifier.send_info_notification(
            "🧪 **Test VM réussi !**\n\n"
            "Le bot a démarré et trade activement :\n"
            "• 4 positions SHORT ouvertes\n"
            "• Scan toutes les 15s\n"
            "• Seuil: 20%"
        )
        
        print("✅ Notification envoyée !\n")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
