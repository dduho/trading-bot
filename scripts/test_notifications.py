#!/usr/bin/env python3
"""
Tester toutes les types de notifications Telegram.
Usage: python scripts/test_notifications.py
"""

import asyncio
import sys
sys.path.append('src')

import yaml
from telegram_notifier import TelegramNotifier

async def test_all_notifications():
    """Tester tous les types de notifications"""
    
    print("\n" + "=" * 60)
    print("  TEST DES NOTIFICATIONS TELEGRAM")
    print("=" * 60 + "\n")
    
    # Charger config
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Erreur lors du chargement de config.yaml: {e}")
        return False
    
    # Initialiser notifier
    try:
        notifier = TelegramNotifier(config)
        print("✅ TelegramNotifier initialisé\n")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        print("\n💡 Vérifiez que .env contient TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID\n")
        return False
    
    # Test de connexion
    print("🔍 Test 0: Vérification de la connexion...")
    if not await notifier.test_connection():
        print("❌ La connexion a échoué\n")
        return False
    print("✅ Connexion OK\n")
    
    # Test 1: Ouverture de position
    print("📤 Test 1: Notification d'ouverture de position...")
    try:
        await notifier.send_trade_notification(
            action='OPEN',
            symbol='SOL/USDT',
            side='BUY',
            entry_price=142.35,
            quantity=0.0352,
            position_value=5.0,
            stop_loss=139.50,
            take_profit=151.08,
            signal_data={
                'confidence': 0.72,
                'action': 'STRONG_BUY',
                'rsi': 42.5,
                'macd': 0.85,
                'ema': 143.2,
                'sma': 141.8,
                'volume_change': 25.3
            },
            portfolio_info={
                'open_positions': 2,
                'max_positions': 3,
                'balance': 100.0,
                'position_size_percent': 5.0
            }
        )
        print("✅ Envoyé\n")
        await asyncio.sleep(3)
    except Exception as e:
        print(f"❌ Erreur: {e}\n")
    
    # Test 2: Fermeture avec profit
    print("📤 Test 2: Notification de fermeture (profit)...")
    try:
        await notifier.send_trade_notification(
            action='CLOSE',
            symbol='SOL/USDT',
            side='SELL',
            entry_price=142.35,
            exit_price=148.72,
            quantity=0.0352,
            pnl=0.22,
            pnl_percent=4.48,
            duration='1h 23min',
            reason='Take Profit',
            portfolio_info={
                'open_positions': 1,
                'max_positions': 3,
                'balance': 100.22,
                'total_pnl_percent': 0.22
            }
        )
        print("✅ Envoyé\n")
        await asyncio.sleep(3)
    except Exception as e:
        print(f"❌ Erreur: {e}\n")
    
    # Test 3: Fermeture avec perte
    print("📤 Test 3: Notification de fermeture (perte)...")
    try:
        await notifier.send_trade_notification(
            action='CLOSE',
            symbol='AVAX/USDT',
            side='SELL',
            entry_price=40.02,
            exit_price=39.15,
            quantity=0.128,
            pnl=-0.11,
            pnl_percent=-2.17,
            duration='28min',
            reason='Stop Loss',
            portfolio_info={
                'open_positions': 0,
                'max_positions': 3,
                'balance': 99.89,
                'total_pnl_percent': -0.11
            }
        )
        print("✅ Envoyé\n")
        await asyncio.sleep(3)
    except Exception as e:
        print(f"❌ Erreur: {e}\n")
    
    # Test 4: Learning cycle
    print("📤 Test 4: Notification de learning cycle...")
    try:
        await notifier.send_learning_notification(
            duration=12.3,
            trades_analyzed=47,
            model_metrics={
                'accuracy': 0.625,
                'precision': 0.683,
                'recall': 0.587,
                'f1_score': 0.63,
                'auc_score': 0.71
            },
            weight_changes={
                'Moving Averages': 2.07,
                'MACD': -1.28,
                'RSI': 0.74,
                'Volume': -1.19,
                'Trend': -0.35
            },
            adaptations=[
                'Optimized indicator weights',
                'Adjusted min_confidence threshold',
                'Updated risk/reward ratio'
            ],
            performance={
                'win_rate': 58.3,
                'total_pnl': 12.45,
                'profit_factor': 2.18
            }
        )
        print("✅ Envoyé\n")
        await asyncio.sleep(3)
    except Exception as e:
        print(f"❌ Erreur: {e}\n")
    
    # Test 5: Erreur critique
    print("📤 Test 5: Notification d'erreur critique...")
    try:
        await notifier.send_error_notification(
            module='OrderExecutor',
            error_type='InsufficientFunds',
            error_message='Fonds insuffisants pour exécuter l\'ordre BUY sur SOL/USDT.',
            severity='critical',
            context={
                'symbol': 'SOL/USDT',
                'required': '5.00 USDT',
                'available': '3.22 USDT'
            }
        )
        print("✅ Envoyé\n")
        await asyncio.sleep(3)
    except Exception as e:
        print(f"❌ Erreur: {e}\n")
    
    # Test 6: Erreur normale (warning)
    print("📤 Test 6: Notification d'avertissement...")
    try:
        await notifier.send_error_notification(
            module='MarketDataFeed',
            error_type='NetworkError',
            error_message='Impossible de récupérer les données OHLCV. Connection timeout.',
            severity='warning',
            context={
                'attempts': '3/5',
                'next_retry': '60s'
            }
        )
        print("✅ Envoyé\n")
        await asyncio.sleep(3)
    except Exception as e:
        print(f"❌ Erreur: {e}\n")
    
    # Test 7: Rapport de statut
    print("📤 Test 7: Rapport de statut quotidien...")
    try:
        await notifier.send_status_report(
            stats={
                'total_trades': 12,
                'winning_trades': 8,
                'losing_trades': 4,
                'total_pnl': 4.85,
                'total_pnl_percent': 4.85
            },
            portfolio={
                'balance': 104.85,
                'max_positions': 3
            },
            positions=[
                {
                    'symbol': 'ADA/USDT',
                    'unrealized_pnl': 0.12,
                    'unrealized_pnl_percent': 2.4
                }
            ],
            ml_status={
                'enabled': True,
                'accuracy': 0.625
            },
            trading_mode='PAPER',
            uptime='2 jours 14h 32min'
        )
        print("✅ Envoyé\n")
        await asyncio.sleep(3)
    except Exception as e:
        print(f"❌ Erreur: {e}\n")
    
    # Test 8: Message simple
    print("📤 Test 8: Message d'information simple...")
    try:
        await notifier.send_info_notification(
            "ℹ️ *Bot démarré avec succès*\n\n"
            "Mode: PAPER TRADING\n"
            "Notifications Telegram: Activées\n"
            "ML Learning: Activé (cycles toutes les 2h)"
        )
        print("✅ Envoyé\n")
    except Exception as e:
        print(f"❌ Erreur: {e}\n")
    
    print("=" * 60)
    print("✅ TESTS TERMINÉS!")
    print("=" * 60)
    print("\n📱 Vérifiez votre Telegram pour voir tous les messages.\n")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_all_notifications())
    sys.exit(0 if success else 1)
