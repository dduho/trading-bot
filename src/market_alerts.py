"""
Market Alerts System - Surveillance des indices et actions
Analyse uniquement (pas de trading automatique)
"""

import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)


class MarketAlertsSystem:
    """Système d'alertes pour surveiller indices, forex et actions"""

    def __init__(self, config: dict, telegram_notifier=None):
        self.config = config
        self.telegram = telegram_notifier
        self.alerts_config = config.get('market_alerts', {})
        self.enabled = self.alerts_config.get('enabled', False)

        # Cache des derniers prix pour détecter les mouvements
        self.last_prices = {}
        self.last_check_time = {}

        logger.info("🔔 Market Alerts System initialized")
        if self.enabled:
            indices_count = len(self.alerts_config.get('indices', []))
            stocks_count = len(self.alerts_config.get('stocks', []))
            logger.info(f"   Monitoring {indices_count} indices + {stocks_count} stocks")

    def check_all_markets(self):
        """Vérifier tous les marchés configurés"""
        if not self.enabled:
            return

        logger.info("🔍 Checking market alerts...")

        # Vérifier les indices
        for index_config in self.alerts_config.get('indices', []):
            try:
                self._check_market(index_config, market_type='index')
                time.sleep(1)  # Rate limiting Yahoo Finance
            except Exception as e:
                logger.error(f"Error checking {index_config['name']}: {e}")

        # Vérifier les actions
        for stock_config in self.alerts_config.get('stocks', []):
            try:
                self._check_market(stock_config, market_type='stock')
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error checking {stock_config['name']}: {e}")

    def _check_market(self, market_config: dict, market_type: str):
        """Vérifier un marché spécifique"""
        symbol = market_config['symbol']
        name = market_config['name']
        threshold = market_config.get('alert_threshold', 0.5)

        # Télécharger les données (1 jour de données 5m)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='1d', interval='5m')

        if df.empty:
            logger.warning(f"⚠️ No data for {name} ({symbol})")
            return

        current_price = df['Close'].iloc[-1]

        # Calculer le mouvement depuis la dernière vérification
        if symbol in self.last_prices:
            last_price = self.last_prices[symbol]
            pct_change = ((current_price - last_price) / last_price) * 100

            # Alerte si mouvement significatif
            if abs(pct_change) >= threshold:
                self._send_movement_alert(
                    name=name,
                    symbol=symbol,
                    current_price=current_price,
                    pct_change=pct_change,
                    market_type=market_type,
                    df=df
                )

        # Mettre à jour le cache
        self.last_prices[symbol] = current_price
        self.last_check_time[symbol] = datetime.now()

    def _send_movement_alert(
        self,
        name: str,
        symbol: str,
        current_price: float,
        pct_change: float,
        market_type: str,
        df: pd.DataFrame
    ):
        """Envoyer une alerte de mouvement significatif"""

        # Calculer indicateurs techniques
        analysis = self._analyze_market(df)

        # Direction emoji
        direction = "📈" if pct_change > 0 else "📉"

        # Type de marché emoji
        market_emoji = "📊" if market_type == 'index' else "📈"

        # Construire le message
        message = f"""
{market_emoji} **ALERTE MARCHÉ: {name}**

{direction} **Mouvement: {pct_change:+.2f}%**
💰 Prix actuel: ${current_price:.2f}

📊 **Analyse Technique:**
• RSI: {analysis['rsi']:.1f} {self._interpret_rsi(analysis['rsi'])}
• MACD: {analysis['macd_signal']}
• Tendance: {analysis['trend']}
• Volume: {analysis['volume_status']}

💡 **Suggestion:** {analysis['suggestion']}

_Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}_
        """.strip()

        # Envoyer via Telegram
        if self.telegram and self.alerts_config.get('telegram_alerts', {}).get('enabled', True):
            try:
                self.telegram.send_urgent_message(message)
                logger.info(f"✅ Alert sent for {name}: {pct_change:+.2f}%")
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")

    def _analyze_market(self, df: pd.DataFrame) -> Dict:
        """Analyser un marché avec indicateurs techniques"""

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50

        # MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_signal = "Haussier 🟢" if macd.iloc[-1] > signal.iloc[-1] else "Baissier 🔴"

        # Tendance (SMA 20 vs prix actuel)
        sma20 = df['Close'].rolling(window=20).mean()
        current_price = df['Close'].iloc[-1]
        trend = "Hausse 📈" if current_price > sma20.iloc[-1] else "Baisse 📉"

        # Volume
        avg_volume = df['Volume'].mean()
        current_volume = df['Volume'].iloc[-1]
        volume_status = "Élevé 🔊" if current_volume > avg_volume * 1.2 else "Normal 🔉"

        # Suggestion
        suggestion = self._generate_suggestion(current_rsi, macd_signal, trend)

        return {
            'rsi': current_rsi,
            'macd_signal': macd_signal,
            'trend': trend,
            'volume_status': volume_status,
            'suggestion': suggestion
        }

    def _interpret_rsi(self, rsi: float) -> str:
        """Interpréter le RSI"""
        if rsi > 70:
            return "(Suracheté 🔴)"
        elif rsi < 30:
            return "(Survendu 🟢)"
        else:
            return "(Neutre ⚪)"

    def _generate_suggestion(self, rsi: float, macd_signal: str, trend: str) -> str:
        """Générer une suggestion de trading"""

        # Logique simple: confluence d'indicateurs
        bullish_signals = 0
        bearish_signals = 0

        # RSI
        if rsi < 30:
            bullish_signals += 1
        elif rsi > 70:
            bearish_signals += 1

        # MACD
        if "Haussier" in macd_signal:
            bullish_signals += 1
        elif "Baissier" in macd_signal:
            bearish_signals += 1

        # Tendance
        if "Hausse" in trend:
            bullish_signals += 1
        elif "Baisse" in trend:
            bearish_signals += 1

        # Décision
        if bullish_signals >= 2:
            return "BUY 🟢 (confluence haussière)"
        elif bearish_signals >= 2:
            return "SELL 🔴 (confluence baissière)"
        else:
            return "HOLD ⚪ (signaux mixtes)"

    def get_market_overview(self) -> str:
        """Obtenir un aperçu de tous les marchés surveillés"""
        if not self.enabled:
            return "Market alerts system is disabled"

        overview_lines = ["📊 **MARKET OVERVIEW**\n"]

        # Indices
        overview_lines.append("**Indices:**")
        for index_config in self.alerts_config.get('indices', []):
            symbol = index_config['symbol']
            name = index_config['name']

            if symbol in self.last_prices:
                price = self.last_prices[symbol]
                overview_lines.append(f"• {name}: ${price:.2f}")

        # Stocks
        if self.alerts_config.get('stocks'):
            overview_lines.append("\n**Actions:**")
            for stock_config in self.alerts_config.get('stocks', []):
                symbol = stock_config['symbol']
                name = stock_config['name']

                if symbol in self.last_prices:
                    price = self.last_prices[symbol]
                    overview_lines.append(f"• {name}: ${price:.2f}")

        return "\n".join(overview_lines)
