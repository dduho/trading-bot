"""
Dynamic Symbol Selector
Automatically selects and prioritizes symbols based on performance
Avoids trading unprofitable assets, focuses on winners
"""

import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SymbolSelector:
    """Dynamically manages which symbols to trade based on performance"""

    def __init__(self, db, config: dict):
        self.db = db
        self.config = config

        # All available symbols from config
        self.available_symbols = config.get('trading_pairs', [])

        # Performance thresholds
        self.min_trades_for_evaluation = 20  # Need at least 20 trades to evaluate
        self.poor_performance_threshold = 0.30  # < 30% WR = poor
        self.good_performance_threshold = 0.40  # > 40% WR = good

        # Cache for performance data
        self.symbol_performance = {}
        self.last_update = None
        self.update_interval = timedelta(hours=2)  # Re-evaluate every 2 hours

        # Initialize
        self._update_performance_data()

    def should_trade_symbol(self, symbol: str) -> Tuple[bool, str]:
        """
        Determine if we should trade this symbol based on its performance

        Returns:
            (should_trade, reason)
        """
        # Update data if needed
        if self._needs_update():
            self._update_performance_data()

        # Check if symbol is available
        if symbol not in self.available_symbols:
            return False, f"Symbol {symbol} not in available pairs"

        # Get performance data
        perf = self.symbol_performance.get(symbol)

        # If no data yet, allow trading (learning phase)
        if not perf:
            return True, "No performance data yet - learning"

        total_trades = perf['total_trades']
        win_rate = perf['win_rate']

        # Need minimum trades to evaluate
        if total_trades < self.min_trades_for_evaluation:
            return True, f"Still learning {symbol} ({total_trades}/{self.min_trades_for_evaluation} trades)"

        # Block poor performers
        if win_rate < self.poor_performance_threshold:
            return False, f"Poor performance on {symbol}: {win_rate:.1%} WR ({total_trades} trades)"

        # Prefer good performers
        if win_rate >= self.good_performance_threshold:
            return True, f"✓ Good performer: {symbol} {win_rate:.1%} WR"

        # Moderate performers - allow but log
        return True, f"Moderate performer: {symbol} {win_rate:.1%} WR"

    def get_preferred_symbols(self) -> List[str]:
        """
        Get list of symbols sorted by performance (best first)
        Only includes symbols with good/moderate performance
        """
        if self._needs_update():
            self._update_performance_data()

        # Filter out poor performers
        good_symbols = []

        for symbol in self.available_symbols:
            perf = self.symbol_performance.get(symbol)

            # Include if:
            # - No data yet (still learning)
            # - Not enough trades (still learning)
            # - Win rate >= threshold (good performer)
            if not perf:
                good_symbols.append((symbol, 0.5, 0))  # Neutral priority
            elif perf['total_trades'] < self.min_trades_for_evaluation:
                good_symbols.append((symbol, 0.5, perf['total_trades']))  # Neutral priority
            elif perf['win_rate'] >= self.poor_performance_threshold:
                good_symbols.append((symbol, perf['win_rate'], perf['total_trades']))

        # Sort by win rate (descending)
        good_symbols.sort(key=lambda x: x[1], reverse=True)

        return [s[0] for s in good_symbols]

    def get_performance_summary(self) -> str:
        """Get human-readable summary of symbol performance"""
        if self._needs_update():
            self._update_performance_data()

        lines = ["📊 Symbol Performance Summary:"]

        # Sort by win rate
        sorted_symbols = sorted(
            self.symbol_performance.items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )

        for symbol, perf in sorted_symbols:
            wr = perf['win_rate']
            trades = perf['total_trades']

            if trades < self.min_trades_for_evaluation:
                status = "🎓 Learning"
            elif wr >= self.good_performance_threshold:
                status = "✅ Good"
            elif wr >= self.poor_performance_threshold:
                status = "⚠️ Moderate"
            else:
                status = "❌ Poor"

            lines.append(f"  {status} {symbol}: {wr:.1%} WR ({trades} trades)")

        return "\n".join(lines)

    def _needs_update(self) -> bool:
        """Check if performance data needs to be refreshed"""
        if not self.last_update:
            return True

        return datetime.now() - self.last_update > self.update_interval

    def _update_performance_data(self):
        """Fetch latest performance data from database"""
        try:
            logger.info("🔄 Updating symbol performance data...")

            # Get recent trades (last 7 days or 500 trades)
            trades = self.db.get_trade_history(limit=500, status='closed')

            # Calculate performance per symbol
            symbol_stats = {}

            for trade in trades:
                symbol = trade.get('symbol')
                if not symbol:
                    continue

                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {
                        'total_trades': 0,
                        'wins': 0,
                        'total_pnl': 0
                    }

                stats = symbol_stats[symbol]
                stats['total_trades'] += 1

                pnl = trade.get('pnl', 0)
                stats['total_pnl'] += pnl

                if pnl > 0:
                    stats['wins'] += 1

            # Calculate win rates
            self.symbol_performance = {}

            for symbol, stats in symbol_stats.items():
                total = stats['total_trades']
                wins = stats['wins']

                self.symbol_performance[symbol] = {
                    'total_trades': total,
                    'wins': wins,
                    'win_rate': wins / total if total > 0 else 0,
                    'total_pnl': stats['total_pnl']
                }

            self.last_update = datetime.now()

            # Log summary
            logger.info(self.get_performance_summary())

        except Exception as e:
            logger.error(f"Error updating symbol performance: {e}")
