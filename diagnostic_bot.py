#!/usr/bin/env python3
"""
Script de diagnostic pour le bot de trading.
Vérifie la configuration et identifie les problèmes.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def check_env_file():
    """Vérifier l'existence et le contenu du fichier .env"""
    print_header("1. VÉRIFICATION DU FICHIER .ENV")

    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Le fichier .env n'existe pas!")
        print("\n💡 Solution:")
        print("   Créez un fichier .env à partir de .env.example:")
        print("   cp .env.example .env")
        print("\n   Puis éditez .env et configurez vos credentials:")
        print("   - TELEGRAM_BOT_TOKEN")
        print("   - TELEGRAM_CHAT_ID")
        print("   - API_KEY et API_SECRET (si mode testnet ou live)")
        return False

    print(f"✅ Le fichier .env existe")

    load_dotenv()

    # Vérifier les variables essentielles
    issues = []

    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat = os.getenv('TELEGRAM_CHAT_ID')
    trading_mode = os.getenv('TRADING_MODE', 'paper')

    if not telegram_token:
        issues.append("TELEGRAM_BOT_TOKEN non défini")
    elif telegram_token == 'your_api_key_here' or 'your' in telegram_token.lower():
        issues.append("TELEGRAM_BOT_TOKEN contient une valeur d'exemple")
    else:
        print(f"✅ TELEGRAM_BOT_TOKEN: {telegram_token[:15]}...{telegram_token[-10:]}")

    if not telegram_chat:
        issues.append("TELEGRAM_CHAT_ID non défini")
    elif telegram_chat == '8350384028':
        print(f"⚠️  TELEGRAM_CHAT_ID: {telegram_chat} (semble être une valeur d'exemple)")
    else:
        print(f"✅ TELEGRAM_CHAT_ID: {telegram_chat}")

    print(f"✅ TRADING_MODE: {trading_mode}")

    if issues:
        print("\n❌ Problèmes détectés:")
        for issue in issues:
            print(f"   - {issue}")
        return False

    return True

def check_telegram_config():
    """Vérifier la configuration Telegram"""
    print_header("2. VÉRIFICATION DE LA CONFIGURATION TELEGRAM")

    load_dotenv()

    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat:
        print("❌ Credentials Telegram manquants")
        print("\n📋 ÉTAPES POUR CONFIGURER TELEGRAM:")
        print("\n1. Créer un bot Telegram:")
        print("   a. Ouvrez Telegram et cherchez @BotFather")
        print("   b. Envoyez /newbot")
        print("   c. Suivez les instructions pour créer votre bot")
        print("   d. Copiez le token fourni")
        print("\n2. Obtenir votre Chat ID:")
        print("   a. Démarrez une conversation avec votre bot (bouton Start)")
        print("   b. Exécutez: python scripts/get_chat_id.py")
        print("   c. Copiez le Chat ID affiché")
        print("\n3. Modifier le fichier .env:")
        print("   TELEGRAM_BOT_TOKEN=votre_token_ici")
        print("   TELEGRAM_CHAT_ID=votre_chat_id_ici")
        return False

    # Tester la connexion
    try:
        import asyncio
        from telegram import Bot

        async def test():
            bot = Bot(token=telegram_token)
            try:
                bot_info = await bot.get_me()
                print(f"✅ Bot Telegram connecté: @{bot_info.username}")
                print(f"   Nom: {bot_info.first_name}")
                print(f"   ID: {bot_info.id}")

                # Essayer d'envoyer un message
                try:
                    await bot.send_message(
                        chat_id=telegram_chat,
                        text="🔧 Test de diagnostic - Bot configuré correctement !"
                    )
                    print(f"✅ Message de test envoyé au Chat ID: {telegram_chat}")
                    return True
                except Exception as e:
                    print(f"❌ Impossible d'envoyer un message: {e}")
                    print("\n💡 Vérifiez que:")
                    print("   1. Vous avez cliqué 'Start' dans le chat avec votre bot")
                    print("   2. Le TELEGRAM_CHAT_ID est correct")
                    print("   3. Le bot n'est pas bloqué")
                    return False

            except Exception as e:
                print(f"❌ Impossible de se connecter au bot: {e}")
                print("\n💡 Vérifiez que:")
                print("   1. Le TELEGRAM_BOT_TOKEN est correct")
                print("   2. Le token n'a pas été révoqué")
                print("   3. Vous avez bien créé le bot via @BotFather")
                return False

        return asyncio.run(test())

    except ImportError as e:
        print(f"❌ Module manquant: {e}")
        print("\n💡 Installez les dépendances:")
        print("   pip install python-telegram-bot python-dotenv")
        return False

def check_bot_status():
    """Vérifier si le bot est en cours d'exécution"""
    print_header("3. VÉRIFICATION DU STATUT DU BOT")

    import subprocess
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )

    if "trading_bot" in result.stdout or "run_bot.py" in result.stdout:
        print("✅ Le bot est en cours d'exécution")
        return True
    else:
        print("❌ Le bot n'est PAS en cours d'exécution")
        print("\n💡 Pour démarrer le bot:")
        print("   python run_bot.py")
        return False

def check_database():
    """Vérifier la base de données"""
    print_header("4. VÉRIFICATION DE LA BASE DE DONNÉES")

    db_file = Path("trading_bot.db")
    if db_file.exists():
        size = db_file.stat().st_size
        if size == 0:
            print(f"⚠️  Base de données vide (0 octets)")
            print("   Le bot n'a probablement jamais été démarré")
        else:
            print(f"✅ Base de données existe ({size} octets)")
        return True
    else:
        print("❌ Base de données n'existe pas")
        print("   Le bot n'a jamais été démarré")
        return False

def check_logs():
    """Vérifier les logs"""
    print_header("5. VÉRIFICATION DES LOGS")

    log_file = Path("trading_bot.log")
    if log_file.exists():
        size = log_file.stat().st_size
        if size == 0:
            print(f"⚠️  Fichier de logs vide")
        else:
            print(f"✅ Fichier de logs existe ({size} octets)")
            print("\n📄 Dernières lignes du log:")
            print("-" * 70)
            with open(log_file) as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(f"   {line.rstrip()}")
            print("-" * 70)
        return True
    else:
        print("❌ Fichier de logs n'existe pas")
        print("   Le bot n'a jamais été démarré")
        return False

def main():
    print("\n🔧 DIAGNOSTIC DU BOT DE TRADING")
    print("   Ce script va vérifier la configuration de votre bot\n")

    results = {
        "env_file": check_env_file(),
        "telegram": check_telegram_config(),
        "bot_running": check_bot_status(),
        "database": check_database(),
        "logs": check_logs()
    }

    print_header("RÉSUMÉ")

    all_ok = all(results.values())

    if all_ok:
        print("✅ Tout semble OK!")
        print("\nLe bot devrait fonctionner correctement.")
    else:
        print("❌ Des problèmes ont été détectés\n")
        print("Problèmes à résoudre:")
        for check, status in results.items():
            if not status:
                print(f"   ❌ {check}")

    print("\n" + "=" * 70)

    if not results["bot_running"]:
        print("\n🚀 POUR DÉMARRER LE BOT:")
        print("   python run_bot.py")

    print()

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
