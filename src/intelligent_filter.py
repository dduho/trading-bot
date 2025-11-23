"""
Intelligent Signal Filter
Filtre les signaux pour ne garder que les meilleurs setups
Réduit les pertes en évitant les trades à faible probabilité de succès
"""

import logging
from typing import Dict, Tuple
from datetime import datetime, timedelta
from symbol_selector import SymbolSelector

logger = logging.getLogger(__name__)


class IntelligentFilter:
    """Filtre intelligent pour améliorer la qualité des trades"""

    def __init__(self, db, config: dict):
        self.db = db
        self.config = config

        # Initialize dynamic symbol selector
        self.symbol_selector = SymbolSelector(db, config)
        logger.info("🎯 Dynamic Symbol Selector initialized")

        # Déterminer si on est en phase d'apprentissage
        self.is_learning_phase = self._is_in_learning_phase()

        if self.is_learning_phase:
            # Phase apprentissage: Plus permissif pour collecter des données
            self.min_signal_strength = 0.10  # 10% minimum (permissif)
            self.min_confluence = 1
            logger.info("🎓 LEARNING MODE: Intelligent filter in learning mode (permissive)")
        else:
            # Phase exploitation: Plus strict pour maximiser profits
            self.min_signal_strength = 0.18  # 18% minimum (strict)
            self.min_confluence = 2
            logger.info("💰 PROFIT MODE: Intelligent filter in profit mode (selective)")

    def should_take_trade(self, signal: Dict, market_conditions: Dict, symbol: str) -> Tuple[bool, str]:
        """
        Décide si un signal doit être tradé ou filtré

        Returns:
            (should_trade, reason)
        """

        # Filtre 0: Performance du symbole (prioritaire)
        should_trade_symbol, symbol_reason = self.symbol_selector.should_trade_symbol(symbol)
        if not should_trade_symbol:
            return False, symbol_reason

        # Filtre 1: Confiance minimale
        confidence = signal.get('confidence', 0)
        if confidence < self.min_signal_strength:
            return False, f"Signal trop faible ({confidence:.1%} < {self.min_signal_strength:.1%})"

        # Filtre 2: Confluence des indicateurs
        details = signal.get('details', {})
        aligned_indicators = self._count_aligned_indicators(details, signal['action'])
        if aligned_indicators < self.min_confluence:
            return False, f"Confluence insuffisante ({aligned_indicators}/{self.min_confluence} indicateurs)"

        # Filtre 3: Conditions de marché défavorables (DÉSACTIVÉ en apprentissage)
        if not self.is_learning_phase:
            if self._is_market_choppy(market_conditions):
                return False, "Marché trop choppy (range-bound)"

        # Filtre 4: Historique récent du symbole (DÉSACTIVÉ en apprentissage)
        # recent_performance = self._get_recent_symbol_performance(symbol)
        # if recent_performance and recent_performance < 0.30:
        #     return False, f"Performance récente faible sur {symbol} ({recent_performance:.1%})"

        # Filtre 5: Trop de pertes consécutives (DÉSACTIVÉ en apprentissage)
        if not self.is_learning_phase:
            consecutive_losses = self._get_consecutive_losses()
            if consecutive_losses >= 5:
                # Seulement après 5 pertes (au lieu de 3), on devient plus sélectif
                if confidence < 0.25:
                    return False, f"5+ pertes consécutives, need higher confidence ({confidence:.1%} < 25%)"

        return True, f"✓ Good setup: conf={confidence:.1%}, confluence={aligned_indicators}, market=trending"

    def _is_in_learning_phase(self) -> bool:
        """Détermine si le bot est en phase d'apprentissage"""
        try:
            stats = self.db.get_performance_stats(days=7)
            total_trades = stats.get('total_trades', 0)
            win_rate = stats.get('win_rate', 0)

            # Phase apprentissage si:
            # - Moins de 100 trades (pas assez de données)
            # - OU win rate < 45% (performances pas encore stables)
            if total_trades < 100:
                return True
            if win_rate < 0.45:
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking learning phase: {e}")
            return True  # Par défaut en mode apprentissage

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

    def get_symbol_performance_summary(self) -> str:
        """Get symbol performance summary from selector"""
        return self.symbol_selector.get_performance_summary()
