#!/usr/bin/env python3
"""
Script de test pour les notifications Telegram.
Usage: python scripts/test_telegram.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from telegram import Bot

async def test_telegram_connection():
    """Tester la connexion au bot Telegram"""
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print("\n" + "=" * 60)
    print("  TEST DE CONNEXION TELEGRAM")
    print("=" * 60 + "\n")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN non défini dans .env")
        return False
    
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID non défini dans .env")
        return False
    
    print(f"🔍 Test de connexion...")
    print(f"   Bot Token: {bot_token[:15]}...{bot_token[-10:]}")
    print(f"   Chat ID: {chat_id}")
    
    try:
        bot = Bot(token=bot_token)
        
        # Obtenir les infos du bot
        print(f"\n📡 Connexion au bot...")
        bot_info = await bot.get_me()
        print(f"✅ Bot connecté: @{bot_info.username}")
        print(f"   Nom: {bot_info.first_name}")
        print(f"   ID: {bot_info.id}")
        
        # Envoyer un message de test
        print(f"\n📤 Envoi d'un message de test...")
        message = await bot.send_message(
            chat_id=chat_id,
            text="🤖 *Test de connexion réussi!*\n\nLe bot de notifications Telegram est configuré correctement.\n\nVous recevrez maintenant des notifications pour:\n• Ouverture/fermeture de positions\n• Cycles d'apprentissage ML\n• Erreurs critiques\n• Rapports quotidiens",
            parse_mode='Markdown'
        )
        
        print(f"✅ Message envoyé (ID: {message.message_id})")
        print(f"\n" + "=" * 60)
        print("✅ CONFIGURATION TELEGRAM OK!")
        print("=" * 60)
        print("\n📝 Prochaines étapes:")
        print("   1. Vérifiez que vous avez reçu le message sur Telegram")
        print("   2. Testez les notifications: python scripts/test_notifications.py")
        print("   3. Démarrez le bot avec: python run_bot.py\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        print("\n💡 Solutions possibles:")
        print("   1. Vérifiez que le token est correct")
        print("   2. Vérifiez que le chat ID est correct")
        print("   3. Assurez-vous d'avoir cliqué 'Start' dans le chat avec le bot")
        print("   4. Réexécutez: python scripts/get_chat_id.py\n")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_telegram_connection())
    sys.exit(0 if success else 1)
