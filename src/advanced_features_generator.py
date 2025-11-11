"""
Advanced Features Generator
Génère des features ML avancées pour améliorer les prédictions
"""

import logging
import numpy as np
from typing import Dict, List

logger = logging.getLogger(__name__)


class AdvancedFeaturesGenerator:
    """
    Génère des features ML avancées à partir des indicateurs de base.

    Features ajoutées:
    - Patterns de chandeliers
    - Divergences RSI/Price
    - Momentum multi-timeframe
    - Volatilité normalisée
    - Support/Resistance proximity
    - Time-based features
    """

    def __init__(self):
        """Initialize generator"""
        logger.info("Advanced Features Generator initialized")

    def generate_features(self, market_data: Dict, indicators: Dict) -> Dict[str, float]:
        """
        Génère des features avancées.

        Args:
            market_data: Données de marché (OHLCV)
            indicators: Indicateurs techniques calculés

        Returns:
            Dict de features avancées
        """
        features = {}

        # 1. Pattern Recognition Features
        features.update(self._candlestick_patterns(market_data))

        # 2. Momentum Features
        features.update(self._momentum_features(indicators, market_data))

        # 3. Volatility Features
        features.update(self._volatility_features(indicators, market_data))

        # 4. Divergence Features
        features.update(self._divergence_features(indicators, market_data))

        # 5. Support/Resistance Features
        features.update(self._support_resistance_features(market_data))

        # 6. Time-based Features
        features.update(self._time_features())

        # 7. Market Regime Features
        features.update(self._market_regime_features(indicators))

        return features

    def _candlestick_patterns(self, data: Dict) -> Dict[str, float]:
        """Détecte les patterns de chandeliers"""
        if not all(k in data for k in ['open', 'high', 'low', 'close']):
            return {}

        o, h, l, c = data['open'], data['high'], data['low'], data['close']
        body = abs(c - o)
        range_val = h - l

        features = {}

        # Doji
        features['pattern_doji'] = 1.0 if body / range_val < 0.1 else 0.0

        # Hammer / Hanging Man
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)
        features['pattern_hammer'] = 1.0 if (lower_shadow > 2 * body and upper_shadow < body) else 0.0

        # Engulfing
        prev_body = abs(data.get('prev_close', c) - data.get('prev_open', o))
        features['pattern_engulfing'] = 1.0 if body > 1.5 * prev_body else 0.0

        # Marubozu (strong trend)
        features['pattern_marubozu'] = 1.0 if body / range_val > 0.9 else 0.0

        return features

    def _momentum_features(self, indicators: Dict, data: Dict) -> Dict[str, float]:
        """Features de momentum"""
        features = {}

        rsi = indicators.get('rsi', 50)
        macd_hist = indicators.get('macd_histogram', 0)

        # RSI zones
        features['rsi_extreme_oversold'] = 1.0 if rsi < 25 else 0.0
        features['rsi_extreme_overbought'] = 1.0 if rsi > 75 else 0.0
        features['rsi_neutral'] = 1.0 if 45 <= rsi <= 55 else 0.0

        # MACD momentum strength
        features['macd_strong_bullish'] = 1.0 if macd_hist > 0.5 else 0.0
        features['macd_strong_bearish'] = 1.0 if macd_hist < -0.5 else 0.0

        # Rate of change
        if 'prev_close' in data and data['prev_close'] != 0:
            roc = (data['close'] - data['prev_close']) / data['prev_close'] * 100
            features['roc_1candle'] = roc
            features['roc_strong'] = 1.0 if abs(roc) > 2 else 0.0

        return features

    def _volatility_features(self, indicators: Dict, data: Dict) -> Dict[str, float]:
        """Features de volatilité"""
        features = {}

        atr = indicators.get('atr', 0)
        close = data.get('close', 0)

        # Volatilité normalisée
        if close != 0:
            features['volatility_ratio'] = atr / close

        # Bollinger Band width
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        if bb_upper > bb_lower and close != 0:
            bb_width = (bb_upper - bb_lower) / close
            features['bb_width'] = bb_width
            features['bb_squeeze'] = 1.0 if bb_width < 0.02 else 0.0  # Squeeze détecté
            features['bb_expansion'] = 1.0 if bb_width > 0.05 else 0.0  # Expansion

        return features

    def _divergence_features(self, indicators: Dict, data: Dict) -> Dict[str, float]:
        """Détecte les divergences RSI/Price"""
        features = {}

        # Nécessite données historiques
        if 'price_history' in data and 'rsi_history' in indicators:
            price_hist = data['price_history'][-5:]  # 5 dernières bougies
            rsi_hist = indicators['rsi_history'][-5:]

            if len(price_hist) >= 3 and len(rsi_hist) >= 3:
                # Bullish divergence: Price lower low, RSI higher low
                price_trend = price_hist[-1] - price_hist[0]
                rsi_trend = rsi_hist[-1] - rsi_hist[0]

                features['divergence_bullish'] = 1.0 if price_trend < 0 and rsi_trend > 0 else 0.0
                features['divergence_bearish'] = 1.0 if price_trend > 0 and rsi_trend < 0 else 0.0

        return features

    def _support_resistance_features(self, data: Dict) -> Dict[str, float]:
        """Features de support/résistance"""
        features = {}

        if 'support_level' in data and 'resistance_level' in data:
            close = data['close']
            support = data['support_level']
            resistance = data['resistance_level']

            if resistance > support and resistance != 0:
                # Distance au support/résistance (normalisée)
                range_sr = resistance - support
                features['distance_to_support'] = (close - support) / range_sr
                features['distance_to_resistance'] = (resistance - close) / range_sr

                # Proche du support/résistance
                features['near_support'] = 1.0 if (close - support) / range_sr < 0.05 else 0.0
                features['near_resistance'] = 1.0 if (resistance - close) / range_sr < 0.05 else 0.0

        return features

    def _time_features(self) -> Dict[str, float]:
        """Features temporelles"""
        from datetime import datetime

        now = datetime.now()
        features = {}

        # Heure du jour (normalisée 0-1)
        features['hour_of_day'] = now.hour / 24.0

        # Jour de la semaine (0=lundi, 1=dimanche normalisé)
        features['day_of_week'] = now.weekday() / 7.0

        # Weekend
        features['is_weekend'] = 1.0 if now.weekday() >= 5 else 0.0

        # Heures de trading actives (Europe/US overlap 14h-17h UTC)
        active_hours = 14 <= now.hour < 17
        features['active_trading_hours'] = 1.0 if active_hours else 0.0

        return features

    def _market_regime_features(self, indicators: Dict) -> Dict[str, float]:
        """Détecte le régime de marché"""
        features = {}

        # Utilise les MAs pour détecter le régime
        sma_short = indicators.get('sma_short', 0)
        sma_long = indicators.get('sma_long', 0)
        close = indicators.get('close', 0)

        if sma_long > 0:
            # Trend strength
            ma_distance = abs(sma_short - sma_long) / sma_long
            features['trend_strength'] = ma_distance

            # Régime
            if ma_distance < 0.01:
                features['regime_ranging'] = 1.0
                features['regime_trending'] = 0.0
            else:
                features['regime_ranging'] = 0.0
                features['regime_trending'] = 1.0

            # Bull/Bear market
            if sma_short > sma_long:
                features['regime_bullish'] = 1.0
                features['regime_bearish'] = 0.0
            else:
                features['regime_bullish'] = 0.0
                features['regime_bearish'] = 1.0

        return features
