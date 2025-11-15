"""
Intelligent Signal Filter
Filtre les signaux pour ne garder que les meilleurs setups
Réduit les pertes en évitant les trades à faible probabilité de succès
"""

import logging
from typing import Dict, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class IntelligentFilter:
    """Filtre intelligent pour améliorer la qualité des trades"""

    def __init__(self, db, config: dict):
        self.db = db
        self.config = config
        self.min_signal_strength = 0.12  # Minimum 12% de confiance
        self.min_confluence = 1  # Au moins 1 indicateur aligné (plus permissif)

    def should_take_trade(self, signal: Dict, market_conditions: Dict, symbol: str) -> Tuple[bool, str]:
        """
        Décide si un signal doit être tradé ou filtré

        Returns:
            (should_trade, reason)
        """

        # Filtre 1: Confiance minimale
        confidence = signal.get('confidence', 0)
        if confidence < self.min_signal_strength:
            return False, f"Signal trop faible ({confidence:.1%} < {self.min_signal_strength:.1%})"

        # Filtre 2: Confluence des indicateurs
        details = signal.get('details', {})
        aligned_indicators = self._count_aligned_indicators(details, signal['action'])
        if aligned_indicators < self.min_confluence:
            return False, f"Confluence insuffisante ({aligned_indicators}/{self.min_confluence} indicateurs)"

        # Filtre 3: Conditions de marché défavorables
        if self._is_market_choppy(market_conditions):
            return False, "Marché trop choppy (range-bound)"

        # Filtre 4: Historique récent du symbole (DÉSACTIVÉ - trop strict)
        # recent_performance = self._get_recent_symbol_performance(symbol)
        # if recent_performance and recent_performance < 0.30:
        #     return False, f"Performance récente faible sur {symbol} ({recent_performance:.1%})"

        # Filtre 5: Trop de pertes consécutives (assooupli)
        consecutive_losses = self._get_consecutive_losses()
        if consecutive_losses >= 5:
            # Seulement après 5 pertes (au lieu de 3), on devient plus sélectif
            if confidence < 0.25:
                return False, f"5+ pertes consécutives, need higher confidence ({confidence:.1%} < 25%)"

        return True, f"✓ Good setup: conf={confidence:.1%}, confluence={aligned_indicators}, market=trending"

    def _count_aligned_indicators(self, details: Dict, action: str) -> int:
        """Compte combien d'indicateurs sont alignés avec le signal"""
        count = 0

        for indicator, data in details.items():
            signal_type = data.get('signal')
            if signal_type:
                if action == 'BUY' and 'BUY' in str(signal_type):
                    count += 1
                elif action == 'SELL' and 'SELL' in str(signal_type):
                    count += 1

        return count

    def _is_market_choppy(self, market_conditions: Dict) -> bool:
        """Détecte si le marché est en range (choppy) plutôt qu'en tendance"""
        # Si RSI proche de 50 et MACD proche de 0 = marché sans direction
        rsi = market_conditions.get('rsi', 50)
        macd_hist = abs(market_conditions.get('macd_hist', 0))

        # RSI entre 45-55 ET MACD très faible = choppy
        if 45 <= rsi <= 55 and macd_hist < 0.0005:
            return True

        return False

    def _get_recent_symbol_performance(self, symbol: str, days: int = 1) -> float:
        """Obtient le win rate récent pour ce symbole spécifique"""
        try:
            trades = self.db.get_trade_history(limit=100, status='closed')
            symbol_trades = [t for t in trades if t.get('symbol') == symbol]

            if not symbol_trades or len(symbol_trades) < 3:
                return None  # Pas assez de données

            # Garder seulement les 10 derniers trades
            recent = symbol_trades[:10]
            wins = sum(1 for t in recent if t.get('pnl', 0) > 0)

            return wins / len(recent) if recent else None
        except Exception as e:
            logger.error(f"Error getting symbol performance: {e}")
            return None

    def _get_consecutive_losses(self) -> int:
        """Compte le nombre de pertes consécutives récentes"""
        try:
            trades = self.db.get_trade_history(limit=10, status='closed')

            consecutive = 0
            for trade in trades:
                if trade.get('pnl', 0) < 0:
                    consecutive += 1
                else:
                    break  # Stop au premier win

            return consecutive
        except Exception as e:
            logger.error(f"Error counting consecutive losses: {e}")
            return 0

    def adjust_position_size(self, base_size: float, signal: Dict, consecutive_losses: int) -> float:
        """Ajuste la taille de position selon les conditions"""
        size = base_size

        # Réduit la taille après des pertes
        if consecutive_losses >= 3:
            size *= 0.5  # Divise par 2 après 3 pertes
            logger.warning(f"⚠️ Position size reduced 50% due to {consecutive_losses} consecutive losses")
        elif consecutive_losses >= 2:
            size *= 0.75  # Réduit de 25% après 2 pertes

        # Augmente légèrement sur signaux très forts
        confidence = signal.get('confidence', 0)
        if confidence > 0.35:
            size *= 1.2  # +20% sur signaux >35%

        return size
