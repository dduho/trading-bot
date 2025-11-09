"""
Test Telegram Commands
Script pour tester les commandes interactives du bot Telegram
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import asyncio
from dotenv import load_dotenv
from telegram import Bot

# Load environment variables
load_dotenv()

async def test_commands():
    """Test all Telegram commands"""
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquants dans .env")
        return
    
    bot = Bot(token=token)
    
    print("🧪 Test des Commandes Telegram")
    print("=" * 60)
    
    # Test 1: Message de guide
    print("\n1️⃣ Envoi du guide des commandes...")
    message = (
        "🧪 *Test des Commandes Telegram*\n\n"
        "Testez les commandes suivantes :\n\n"
        "/start - Message de bienvenue\n"
        "/help - Aide complète\n"
        "/status - État du bot\n"
        "/ml - Métriques ML\n"
        "/positions - Positions ouvertes\n"
        "/performance - Stats globales\n"
        "/today - Résumé du jour\n\n"
        "💡 _Tapez une commande pour la tester !_"
    )
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
        print("✅ Guide envoyé avec succès")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ Test terminé")
    print("\nℹ️  Les commandes sont maintenant actives quand le bot tourne.")
    print("   Démarrez le bot avec: python run_bot.py")
    print("   Puis testez les commandes dans Telegram!")

if __name__ == "__main__":
    asyncio.run(test_commands())
