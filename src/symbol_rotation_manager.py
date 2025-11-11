"""
Symbol Rotation Manager
Identifie et sélectionne automatiquement les cryptos les plus rentables
"""

import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SymbolRotationManager:
    """
    Gère la rotation automatique des symboles tradés.

    Stratégie:
    - Analyse la performance par symbole
    - Garde les symboles rentables
    - Remplace les symboles non-rentables par de nouveaux candidats
    - Équilibre entre exploration (nouveaux symboles) et exploitation (symboles rentables)
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

        # Pool de symboles disponibles (par ordre de priorité)
        self.symbol_pool = [
            # Tier 1: Très volatiles et liquides
            'SOL/USDT', 'AVAX/USDT', 'MATIC/USDT', 'DOGE/USDT', 'ADA/USDT',

            # Tier 2: Volatiles
            'ATOM/USDT', 'DOT/USDT', 'LINK/USDT', 'UNI/USDT', 'NEAR/USDT',

            # Tier 3: Moyennement volatiles
            'FTM/USDT', 'ALGO/USDT', 'XLM/USDT', 'VET/USDT', 'SAND/USDT',

            # Tier 4: Caps moyens volatiles
            'MANA/USDT', 'AXS/USDT', 'GALA/USDT', 'CHZ/USDT', 'ENJ/USDT'
        ]

        self.max_symbols = 8  # Maximum de symboles actifs
        self.min_symbols = 5  # Minimum de symboles actifs
        self.min_trades_to_evaluate = 10  # Trades minimum pour évaluer un symbole

        logger.info(f"Symbol Rotation Manager initialized with pool of {len(self.symbol_pool)} symbols")

    def analyze_symbol_performance(self, days: int = 7) -> Dict[str, Dict]:
        """
        Analyse la performance de chaque symbole.

        Args:
            days: Nombre de jours à analyser

        Returns:
            Dict {symbol: {performance_metrics}}
        """
        all_trades = self.db.get_recent_trades(limit=1000)  # Tous les trades récents

        # Grouper par symbole
        by_symbol = defaultdict(list)
        for trade in all_trades:
            symbol = trade.get('symbol')
            if symbol:
                by_symbol[symbol].append(trade)

        # Calculer les métriques par symbole
        performance = {}
        for symbol, trades in by_symbol.items():
            if len(trades) < 3:  # Besoin d'au moins 3 trades
                continue

            wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
            losses = len(trades) - wins
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            avg_pnl = total_pnl / len(trades) if trades else 0

            win_pnl = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
            loss_pnl = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))

            profit_factor = (win_pnl / loss_pnl) if loss_pnl > 0 else 0

            performance[symbol] = {
                'total_trades': len(trades),
                'wins': wins,
                'losses': losses,
                'win_rate': wins / len(trades) if trades else 0,
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl,
                'profit_factor': profit_factor,
                'score': self._calculate_symbol_score(wins, len(trades), total_pnl, profit_factor)
            }

        return performance

    def _calculate_symbol_score(self, wins: int, total: int, pnl: float, profit_factor: float) -> float:
        """
        Calcule un score global pour un symbole.

        Args:
            wins: Nombre de trades gagnants
            total: Total de trades
            pnl: PnL total
            profit_factor: Profit factor

        Returns:
            Score (plus élevé = meilleur)
        """
        win_rate = wins / total if total > 0 else 0

        # Pondération:
        # - 40% win rate
        # - 30% PnL total
        # - 30% profit factor
        score = (
            win_rate * 0.4 +
            (pnl / 100) * 0.3 +  # Normalise PnL
            (profit_factor / 3) * 0.3  # Normalise profit factor
        )

        return max(0, score)  # Score minimum 0

    def select_optimal_symbols(self) -> Tuple[List[str], Dict]:
        """
        Sélectionne les symboles optimaux.

        Returns:
            Tuple (list of symbols, analysis dict)
        """
        current_symbols = self.config.get('symbols', [])
        performance = self.analyze_symbol_performance()

        # Trier les symboles actuels par performance
        current_perf = []
        for symbol in current_symbols:
            if symbol in performance:
                current_perf.append((symbol, performance[symbol]))
            else:
                # Symbole sans données → score neutre
                current_perf.append((symbol, {'score': 0.3, 'total_trades': 0}))

        # Trier par score
        current_perf.sort(key=lambda x: x[1]['score'], reverse=True)

        # Garder les meilleurs symboles
        keep_count = max(self.min_symbols - 2, 3)  # Garde au moins 3 des meilleurs
        symbols_to_keep = [s for s, _ in current_perf[:keep_count]]

        # Identifier les symboles à remplacer
        symbols_to_replace = [s for s, p in current_perf[keep_count:]
                               if p['total_trades'] >= self.min_trades_to_evaluate
                               and p['score'] < 0.3]

        # Trouver de nouveaux symboles candidats
        new_candidates = [s for s in self.symbol_pool
                          if s not in current_symbols]

        # Ajouter de nouveaux symboles
        new_symbols = list(symbols_to_keep)

        # Compléter jusqu'au max
        for candidate in new_candidates:
            if len(new_symbols) >= self.max_symbols:
                break
            new_symbols.append(candidate)

        # Toujours garder au moins min_symbols
        if len(new_symbols) < self.min_symbols:
            # Rajouter des symboles du pool
            for symbol in self.symbol_pool:
                if symbol not in new_symbols:
                    new_symbols.append(symbol)
                    if len(new_symbols) >= self.min_symbols:
                        break

        analysis = {
            'kept_symbols': symbols_to_keep,
            'removed_symbols': [s for s in current_symbols if s not in new_symbols],
            'added_symbols': [s for s in new_symbols if s not in current_symbols],
            'performance': performance
        }

        return new_symbols, analysis

    def apply_rotation(self) -> Dict:
        """
        Applique la rotation de symboles.

        Returns:
            Dict avec les résultats
        """
        current_symbols = self.config.get('symbols', [])

        # Besoin d'au moins 50 trades au total pour commencer la rotation
        stats = self.db.get_performance_stats(days=7)
        if stats['total_trades'] < 50:
            return {
                'rotated': False,
                'reason': f"Pas assez de trades ({stats['total_trades']}) pour rotation"
            }

        new_symbols, analysis = self.select_optimal_symbols()

        # Si aucun changement
        if set(new_symbols) == set(current_symbols):
            return {
                'rotated': False,
                'reason': 'Symboles actuels sont optimaux'
            }

        # Appliquer
        self.config['symbols'] = new_symbols

        logger.info(f"Symbol rotation applied:")
        logger.info(f"  Kept: {analysis['kept_symbols']}")
        logger.info(f"  Removed: {analysis['removed_symbols']}")
        logger.info(f"  Added: {analysis['added_symbols']}")

        return {
            'rotated': True,
            'old_symbols': current_symbols,
            'new_symbols': new_symbols,
            'analysis': analysis
        }
