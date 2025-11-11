"""
Dynamic Confidence Manager
Ajuste automatiquement min_confidence selon les performances
"""

import logging
from typing import Dict, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DynamicConfidenceManager:
    """
    Gère l'ajustement dynamique du seuil de confiance minimum.

    Stratégie:
    - Si win rate élevé + peu de trades → BAISSER confidence (trader plus)
    - Si win rate faible + beaucoup de trades → AUGMENTER confidence (être sélectif)
    - Si profit factor élevé → Peut se permettre de baisser confidence
    - Si drawdown important → AUGMENTER confidence immédiatement
    """

    def __init__(self, db, config: Dict):
        """
        Initialize manager.

        Args:
            db: TradeDatabase instance
            config: Configuration dictionary
        """
        self.db = db
        self.config = config

        # Targets
        self.target_win_rate = 0.55  # 55% target
        self.target_trades_per_day = 30  # Vise 30 trades/jour
        self.min_confidence = 0.03  # Minimum absolu: 3%
        self.max_confidence = 0.70  # Maximum: 70%

        # Ajustement graduel
        self.adjustment_step = 0.02  # Ajuste par pas de 2%

        logger.info("Dynamic Confidence Manager initialized")

    def should_adjust(self) -> bool:
        """Détermine si un ajustement est nécessaire"""
        stats = self.db.get_performance_stats(days=1)

        # Besoin d'au moins 10 trades pour ajuster
        if stats['total_trades'] < 10:
            return False

        return True

    def calculate_optimal_confidence(self) -> Tuple[float, str]:
        """
        Calcule le niveau de confiance optimal.

        Returns:
            Tuple (new_confidence, reason)
        """
        stats = self.db.get_performance_stats(days=1)
        current_confidence = self.config.get('strategy', {}).get('min_confidence', 0.05)

        win_rate = stats.get('win_rate', 0)
        total_trades = stats.get('total_trades', 0)
        profit_factor = stats.get('profit_factor', 1.0)
        total_pnl = stats.get('total_pnl', 0)

        # Analyser la situation
        reasons = []
        adjustment = 0

        # 1. Win rate trop faible → AUGMENTER confidence
        if win_rate < 0.45 and total_trades > 15:
            adjustment += self.adjustment_step
            reasons.append(f"Win rate faible ({win_rate:.1%}) - augmente sélectivité")

        # 2. Win rate élevé → BAISSER confidence (trader plus)
        elif win_rate > 0.60 and total_trades < self.target_trades_per_day:
            adjustment -= self.adjustment_step
            reasons.append(f"Win rate élevé ({win_rate:.1%}) + peu de trades - peut trader plus")

        # 3. Pas assez de trades → BAISSER confidence
        if total_trades < 15:
            adjustment -= self.adjustment_step * 0.5
            reasons.append(f"Seulement {total_trades} trades/jour - augmente volume")

        # 4. Trop de trades perdants d'affilée → AUGMENTER
        recent_trades = self.db.get_recent_trades(limit=10)
        if len(recent_trades) >= 5:
            recent_losses = sum(1 for t in recent_trades[:5] if t.get('pnl', 0) < 0)
            if recent_losses >= 4:
                adjustment += self.adjustment_step * 1.5
                reasons.append(f"{recent_losses}/5 derniers trades perdants - urgence")

        # 5. Profit factor faible → AUGMENTER confidence
        if profit_factor < 1.2 and total_trades > 20:
            adjustment += self.adjustment_step * 0.5
            reasons.append(f"Profit factor faible ({profit_factor:.2f}) - améliore qualité")

        # 6. PnL négatif significatif → AUGMENTER confidence
        if total_pnl < -50:  # -$50 ou plus
            adjustment += self.adjustment_step * 2
            reasons.append(f"PnL négatif important (${total_pnl:.2f}) - mode défensif")

        # 7. Excellentes performances → BAISSER confidence
        if profit_factor > 2.0 and win_rate > 0.55:
            adjustment -= self.adjustment_step * 0.5
            reasons.append(f"Excellentes perfs (PF={profit_factor:.2f}) - peut être agressif")

        # Calculer nouvelle confidence
        new_confidence = current_confidence + adjustment

        # Limites
        new_confidence = max(self.min_confidence, min(self.max_confidence, new_confidence))

        # Si aucun changement significatif
        if abs(new_confidence - current_confidence) < 0.005:
            return current_confidence, "Aucun ajustement nécessaire"

        reason = " | ".join(reasons) if reasons else "Ajustement standard"

        logger.info(f"Confidence: {current_confidence:.2%} → {new_confidence:.2%} ({reason})")

        return new_confidence, reason

    def apply_adjustment(self) -> Dict:
        """
        Applique l'ajustement de confidence.

        Returns:
            Dict avec les résultats
        """
        if not self.should_adjust():
            return {
                'adjusted': False,
                'reason': 'Pas assez de trades pour ajuster'
            }

        current = self.config.get('strategy', {}).get('min_confidence', 0.05)
        new_confidence, reason = self.calculate_optimal_confidence()

        if abs(new_confidence - current) < 0.005:
            return {
                'adjusted': False,
                'reason': reason
            }

        # Appliquer
        self.config['strategy']['min_confidence'] = new_confidence

        return {
            'adjusted': True,
            'old_value': current,
            'new_value': new_confidence,
            'change': new_confidence - current,
            'reason': reason
        }
