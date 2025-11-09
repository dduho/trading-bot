#!/usr/bin/env python3
"""
Script pour récupérer votre Chat ID Telegram.

Instructions:
1. Démarrez une conversation avec votre bot sur Telegram
2. Envoyez-lui n'importe quel message (ex: "Hello")
3. Exécutez ce script

Usage: python scripts/get_chat_id.py
"""

import requests
import sys

def get_chat_id(bot_token: str):
    """Récupère le Chat ID depuis les updates Telegram"""
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    print("🔍 Récupération des updates Telegram...")
    print(f"   Token: {bot_token[:15]}...{bot_token[-10:]}\n")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ Erreur API Telegram: {data.get('description', 'Unknown error')}")
            return None
        
        updates = data.get('result', [])
        
        if not updates:
            print("⚠️  Aucun message trouvé!")
            print("\n📱 INSTRUCTIONS:")
            print("   1. Ouvrez Telegram")
            print("   2. Cherchez votre bot par son username")
            print("   3. Cliquez sur 'Start' ou envoyez-lui un message")
            print("   4. Réexécutez ce script\n")
            return None
        
        # Afficher tous les chat IDs trouvés
        chat_ids = set()
        
        print(f"✅ {len(updates)} message(s) trouvé(s):\n")
        
        for i, update in enumerate(updates, 1):
            message = update.get('message', {})
            chat = message.get('chat', {})
            
            chat_id = chat.get('id')
            chat_type = chat.get('type', 'unknown')
            username = chat.get('username', 'N/A')
            first_name = chat.get('first_name', 'N/A')
            text = message.get('text', 'N/A')
            
            if chat_id:
                chat_ids.add(str(chat_id))
                
                print(f"   Message {i}:")
                print(f"   ├─ Chat ID: {chat_id}")
                print(f"   ├─ Type: {chat_type}")
                print(f"   ├─ Nom: {first_name}")
                print(f"   ├─ Username: @{username}")
                print(f"   └─ Texte: \"{text}\"\n")
        
        if chat_ids:
            # Prendre le premier chat ID (généralement le vôtre)
            main_chat_id = list(chat_ids)[0]
            
            print("=" * 60)
            print("✅ CONFIGURATION À AJOUTER AU FICHIER .env:")
            print("=" * 60)
            print(f"\nTELEGRAM_BOT_TOKEN={bot_token}")
            print(f"TELEGRAM_CHAT_ID={main_chat_id}\n")
            print("=" * 60)
            
            if len(chat_ids) > 1:
                print(f"\n⚠️  Plusieurs Chat IDs trouvés: {', '.join(chat_ids)}")
                print("   Utilisez celui qui correspond à votre compte personnel.\n")
            
            return main_chat_id
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


if __name__ == "__main__":
    # Token du bot (peut être passé en argument ou hardcodé temporairement)
    if len(sys.argv) > 1:
        bot_token = sys.argv[1]
    else:
        # Token fourni par l'utilisateur
        bot_token = "8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI"
    
    print("\n" + "=" * 60)
    print("  RÉCUPÉRATION DU CHAT ID TELEGRAM")
    print("=" * 60 + "\n")
    
    chat_id = get_chat_id(bot_token)
    
    if chat_id:
        print("\n✅ Chat ID récupéré avec succès!")
        print("\n📝 Prochaines étapes:")
        print("   1. Copiez les lignes ci-dessus dans votre fichier .env")
        print("   2. Testez la connexion avec: python scripts/test_telegram.py")
        print("   3. Démarrez le bot avec les notifications activées\n")
    else:
        print("\n❌ Impossible de récupérer le Chat ID")
        print("   Assurez-vous d'avoir envoyé un message au bot d'abord.\n")
