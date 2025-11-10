#!/usr/bin/env python3
"""Test manuel d'envoi de notification Telegram"""

import asyncio
from telegram import Bot

async def send_test():
    bot = Bot(token='8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI')
    
    message = """
🧪 **TEST MANUEL BOT TRADING**

Si vous recevez ce message, les notifications Telegram fonctionnent !

✅ Token: OK
✅ Chat ID: OK  
✅ Connexion: OK

Prochain test : notification automatique du bot...
    """
    
    await bot.send_message(
        chat_id='8350384028', 
        text=message,
        parse_mode='Markdown'
    )
    print('✅ Message envoyé avec succès!')

if __name__ == '__main__':
    asyncio.run(send_test())
