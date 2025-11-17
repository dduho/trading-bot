"""
Autonomous Optimizer - Système d'auto-optimisation avancé
Lance des optimisations périodiques pour maximiser la performance autonome
"""

import logging
import yaml
from datetime import datetime, timedelta
from src.trade_database import TradeDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutonomousOptimizer:
    """Optimise automatiquement les paramètres du bot"""
    
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.db = TradeDatabase()
        self.load_config()
    
    def load_config(self):
        """Charge la configuration"""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def save_config(self):
        """Sauvegarde la configuration"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        logger.info(f"✅ Configuration saved to {self.config_path}")
    
    def optimize_confidence_threshold(self):
        """Optimise le seuil de confiance basé sur les performances"""
        stats = self.db.get_performance_stats(days=7)
        current_conf = self.config['strategy']['min_confidence']
        
        logger.info(f"\n{'='*60}")
        logger.info("OPTIMIZING CONFIDENCE THRESHOLD")
        logger.info(f"{'='*60}")
        logger.info(f"Current confidence: {current_conf:.2%}")
        logger.info(f"Win rate (7d): {stats['win_rate']:.1f}%")
        logger.info(f"Total trades (7d): {stats['total_trades']}")
        logger.info(f"Profit factor (7d): {stats['profit_factor']:.2f}")
        
        new_conf = current_conf
        reason = "No change needed"
        
        # Phase 1: Apprentissage (win rate < 45%)
        if stats['win_rate'] < 0.45 and stats['total_trades'] > 50:
            # Performances faibles → Augmenter légèrement la sélectivité
            new_conf = min(0.08, current_conf + 0.01)
            reason = "Low win rate - increasing selectivity"
        
        # Phase 2: Croissance (win rate 45-55%)
        elif 0.45 <= stats['win_rate'] < 0.55:
            # Performances moyennes → Maintenir ou ajuster légèrement
            if stats['profit_factor'] < 1.3:
                new_conf = min(0.10, current_conf + 0.005)
                reason = "Medium win rate but low profit factor"
            else:
                reason = "Good balance - maintaining current threshold"
        
        # Phase 3: Mature (win rate 55-65%)
        elif 0.55 <= stats['win_rate'] < 0.65:
            # Bonnes performances → Peut baisser légèrement pour plus de volume
            if stats['total_trades'] < 100:
                new_conf = max(0.05, current_conf - 0.01)
                reason = "High win rate, low volume - decreasing for more trades"
            else:
                reason = "Optimal performance - maintaining"
        
        # Phase 4: Expert (win rate > 65%)
        else:
            # Excellentes performances → Trader plus agressivement
            new_conf = max(0.03, current_conf - 0.02)
            reason = "Excellent win rate - can be more aggressive"
        
        # Limites absolues
        new_conf = max(0.03, min(0.15, new_conf))
        
        if abs(new_conf - current_conf) > 0.001:
            logger.info(f"📊 ADJUSTMENT: {current_conf:.2%} → {new_conf:.2%}")
            logger.info(f"   Reason: {reason}")
            self.config['strategy']['min_confidence'] = new_conf
            return True, new_conf, reason
        else:
            logger.info(f"✓ Confidence optimal: {current_conf:.2%}")
            return False, current_conf, reason
    
    def optimize_position_sizing(self):
        """Optimise la taille des positions basée sur la volatilité"""
        stats = self.db.get_performance_stats(days=7)
        current_size = self.config['risk']['max_position_size_percent']
        
        logger.info(f"\n{'='*60}")
        logger.info("OPTIMIZING POSITION SIZING")
        logger.info(f"{'='*60}")
        logger.info(f"Current position size: {current_size}%")
        
        new_size = current_size
        reason = "No change needed"
        
        # Si drawdown important → Réduire taille
        if stats.get('total_pnl', 0) < -100:
            new_size = max(1.0, current_size - 0.5)
            reason = "Large drawdown - reducing position size"
        
        # Si profit factor élevé → Augmenter légèrement
        elif stats['profit_factor'] > 2.0 and stats['win_rate'] > 0.55:
            new_size = min(5.0, current_size + 0.5)
            reason = "High profit factor - can increase size"
        
        # Si trop de pertes consécutives → Réduire
        recent_trades = self.db.get_recent_trades(limit=10)
        if len(recent_trades) >= 5:
            recent_losses = sum(1 for t in recent_trades[:5] if t.get('pnl', 0) < 0)
            if recent_losses >= 4:
                new_size = max(1.0, current_size - 1.0)
                reason = f"{recent_losses}/5 recent losses - reducing size"
        
        if abs(new_size - current_size) > 0.1:
            logger.info(f"📊 ADJUSTMENT: {current_size}% → {new_size}%")
            logger.info(f"   Reason: {reason}")
            self.config['risk']['max_position_size_percent'] = new_size
            return True, new_size, reason
        else:
            logger.info(f"✓ Position size optimal: {current_size}%")
            return False, current_size, reason
    
    def optimize_stop_loss_take_profit(self):
        """Optimise SL/TP basé sur volatilité et performances"""
        stats = self.db.get_performance_stats(days=7)
        current_sl = self.config['risk']['stop_loss_percent']
        current_tp = self.config['risk']['take_profit_percent']
        
        logger.info(f"\n{'='*60}")
        logger.info("OPTIMIZING STOP LOSS / TAKE PROFIT")
        logger.info(f"{'='*60}")
        logger.info(f"Current SL: {current_sl}% | TP: {current_tp}%")
        
        new_sl = current_sl
        new_tp = current_tp
        reason = "No change needed"
        
        # Analyser le ratio SL/TP actuel
        ratio = current_tp / current_sl if current_sl > 0 else 3.0
        
        # Si beaucoup de SL hit mais peu de TP → SL trop serré
        if stats['win_rate'] < 0.40 and stats['total_trades'] > 30:
            new_sl = min(3.0, current_sl + 0.25)
            new_tp = new_sl * ratio  # Maintenir le ratio
            reason = "Too many stop losses - widening SL"
        
        # Si profit factor faible → Améliorer ratio
        elif stats['profit_factor'] < 1.2 and stats['total_trades'] > 30:
            new_tp = min(6.0, current_tp + 0.5)
            reason = "Low profit factor - increasing TP"
        
        # Si excellent profit factor → Peut serrer légèrement
        elif stats['profit_factor'] > 2.5 and stats['win_rate'] > 0.60:
            new_sl = max(1.0, current_sl - 0.25)
            new_tp = new_sl * ratio
            reason = "Excellent performance - can tighten SL"
        
        if abs(new_sl - current_sl) > 0.1 or abs(new_tp - current_tp) > 0.1:
            logger.info(f"📊 ADJUSTMENT:")
            logger.info(f"   SL: {current_sl}% → {new_sl}%")
            logger.info(f"   TP: {current_tp}% → {new_tp}%")
            logger.info(f"   Ratio: {ratio:.1f}:1 → {new_tp/new_sl:.1f}:1")
            logger.info(f"   Reason: {reason}")
            self.config['risk']['stop_loss_percent'] = new_sl
            self.config['risk']['take_profit_percent'] = new_tp
            return True, (new_sl, new_tp), reason
        else:
            logger.info(f"✓ SL/TP optimal: {current_sl}%/{current_tp}% (ratio {ratio:.1f}:1)")
            return False, (current_sl, current_tp), reason
    
    def run_full_optimization(self):
        """Lance l'optimisation complète"""
        logger.info(f"\n{'='*80}")
        logger.info("AUTONOMOUS OPTIMIZATION - FULL CYCLE")
        logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*80}\n")
        
        changes_made = False
        summary = []
        
        # 1. Optimize confidence
        changed, value, reason = self.optimize_confidence_threshold()
        if changed:
            changes_made = True
            summary.append(f"Confidence: {value:.2%} ({reason})")
        
        # 2. Optimize position sizing
        changed, value, reason = self.optimize_position_sizing()
        if changed:
            changes_made = True
            summary.append(f"Position size: {value}% ({reason})")
        
        # 3. Optimize SL/TP
        changed, value, reason = self.optimize_stop_loss_take_profit()
        if changed:
            changes_made = True
            summary.append(f"SL/TP: {value[0]:.1f}%/{value[1]:.1f}% ({reason})")
        
        # Save if changes
        if changes_made:
            self.save_config()
            logger.info(f"\n{'='*80}")
            logger.info("OPTIMIZATION SUMMARY - CHANGES APPLIED:")
            for change in summary:
                logger.info(f"  • {change}")
            logger.info(f"{'='*80}\n")
        else:
            logger.info(f"\n{'='*80}")
            logger.info("OPTIMIZATION SUMMARY - NO CHANGES NEEDED")
            logger.info("All parameters are already optimal")
            logger.info(f"{'='*80}\n")
        
        return changes_made, summary


def main():
    """Point d'entrée principal"""
    optimizer = AutonomousOptimizer()
    changes_made, summary = optimizer.run_full_optimization()
    
    if changes_made:
        print("\n✅ OPTIMIZATION COMPLETE - Changes applied")
        print("Please restart the bot to apply new parameters")
    else:
        print("\n✅ OPTIMIZATION COMPLETE - All parameters optimal")


if __name__ == "__main__":
    main()
