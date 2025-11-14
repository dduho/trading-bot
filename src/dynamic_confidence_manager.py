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
        self.max_confidence = 0.15  # Maximum absolu: 15% (signaux typiquement 14-20%)

        # Ajustement graduel
        self.adjustment_step = 0.005  # Ajuste par pas de 0.5% (très conservateur)

        # Plafond adaptatif basé sur performances
        self.adaptive_ceiling = self._calculate_adaptive_ceiling()

        logger.info(f"Dynamic Confidence Manager initialized (adaptive ceiling: {self.adaptive_ceiling:.1%})")

    def _calculate_adaptive_ceiling(self) -> float:
        """
        Calcule le plafond adaptatif basé sur les performances historiques.

        Logique:
        - Phase apprentissage (win rate < 40%): Plafond BAS (8%) pour forcer volume
        - Phase intermédiaire (40-50%): Plafond MOYEN (10%) pour équilibre
        - Phase mature (50-55%): Plafond ÉLEVÉ (12%) pour optimisation
        - Phase expert (> 55%): Plafond MAX (15%) pour max rentabilité

        Returns:
            Plafond adaptatif entre 8% et 15%
        """
        stats = self.db.get_performance_stats(days=7)  # Analyse sur 7 jours

        win_rate = stats.get('win_rate', 0)
        total_trades = stats.get('total_trades', 0)
        profit_factor = stats.get('profit_factor', 0)

        # Pas assez de données → Mode conservateur
        if total_trades < 50:
            logger.info("📊 Adaptive ceiling: 8% (apprentissage - pas assez de trades)")
            return 0.08

        # Phase 1: Apprentissage (performances faibles)
        if win_rate < 0.40 or profit_factor < 1.0:
            logger.info(f"📊 Adaptive ceiling: 8% (apprentissage - WR:{win_rate:.1%}, PF:{profit_factor:.2f})")
            return 0.08

        # Phase 2: Intermédiaire (performances moyennes)
        elif win_rate < 0.50 or profit_factor < 1.3:
            logger.info(f"📊 Adaptive ceiling: 10% (intermédiaire - WR:{win_rate:.1%}, PF:{profit_factor:.2f})")
            return 0.10

        # Phase 3: Mature (bonnes performances)
        elif win_rate < 0.55 or profit_factor < 1.8:
            logger.info(f"📊 Adaptive ceiling: 12% (mature - WR:{win_rate:.1%}, PF:{profit_factor:.2f})")
            return 0.12

        # Phase 4: Expert (excellentes performances)
        else:
            logger.info(f"📊 Adaptive ceiling: 15% (expert - WR:{win_rate:.1%}, PF:{profit_factor:.2f})")
            return 0.15

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

        # Recalculer le plafond adaptatif (peut évoluer avec les performances)
        self.adaptive_ceiling = self._calculate_adaptive_ceiling()

        # 1. Win rate trop faible → AUGMENTER confidence (SAUF si déjà proche du max adaptatif)
        if win_rate < 0.45 and total_trades > 15 and current_confidence < self.adaptive_ceiling:
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

        # 4. Trop de trades perdants d'affilée → AUGMENTER (SAUF si déjà proche du max adaptatif)
        recent_trades = self.db.get_recent_trades(limit=10)
        if len(recent_trades) >= 5:
            recent_losses = sum(1 for t in recent_trades[:5] if t.get('pnl', 0) < 0)
            if recent_losses >= 4 and current_confidence < self.adaptive_ceiling:
                adjustment += self.adjustment_step * 1.5
                reasons.append(f"{recent_losses}/5 derniers trades perdants - urgence")

        # 5. Profit factor faible → AUGMENTER confidence (SAUF si déjà proche du max adaptatif)
        if profit_factor < 1.2 and total_trades > 20 and current_confidence < self.adaptive_ceiling:
            adjustment += self.adjustment_step * 0.5
            reasons.append(f"Profit factor faible ({profit_factor:.2f}) - améliore qualité")

        # 6. PnL négatif significatif → AUGMENTER confidence (SAUF si déjà proche du max adaptatif)
        if total_pnl < -50 and current_confidence < self.adaptive_ceiling:  # -$50 ou plus
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

        # Avertir si on atteint le plafond adaptatif
        if new_confidence >= self.adaptive_ceiling:
            logger.warning(f"⚠️ Confidence atteint plafond adaptatif ({self.adaptive_ceiling:.1%}) - arrêt des augmentations auto")
            # Forcer au plafond adaptatif pour éviter de bloquer les trades
            new_confidence = min(new_confidence, self.adaptive_ceiling)

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
        current = self.config.get('strategy', {}).get('min_confidence', 0.05)

        # EMERGENCY FIX: Si confidence est trop haute (> max), forcer un reset
        if current > self.max_confidence:
            logger.warning(f"⚠️ CONFIDENCE TOO HIGH: {current:.1%} > max {self.max_confidence:.1%}! Forcing reset to 5%")
            self.config['strategy']['min_confidence'] = 0.05
            return {
                'adjusted': True,
                'old_value': current,
                'new_value': 0.05,
                'change': 0.05 - current,
                'reason': f'EMERGENCY RESET: Confidence était à {current:.1%}, bien trop élevé (max: {self.max_confidence:.1%})'
            }

        if not self.should_adjust():
            return {
                'adjusted': False,
                'reason': 'Pas assez de trades pour ajuster'
            }

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
