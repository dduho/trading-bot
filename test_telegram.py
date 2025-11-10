#!/usr/bin/env python3
"""Test rapide des notifications Telegram"""
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Importer le notifier
from telegram_notifier import TelegramNotifier

def test_notification():
    """Envoie une notification de test"""
    try:
        print("🔍 Chargement de la configuration...")
        import yaml
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("🔍 Initialisation du notifier...")
        notifier = TelegramNotifier(config)
        
        print(f"   Token: {notifier.bot_token[:20]}...")
        print(f"   Chat ID: {notifier.chat_id}")
        
        print("\n📤 Envoi de la notification de test...")
        notifier.send_info_notification(
            "🧪 Test depuis VM - Si vous recevez ce message, Telegram fonctionne correctement !"
        )
        
        print("✅ Notification envoyée avec succès !\n")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_notification()
    sys.exit(0 if success else 1)
