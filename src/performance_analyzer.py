"""
Performance Analyzer - Analyzes trade patterns and identifies learning opportunities
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    Analyzes trading performance to identify patterns in winning and losing trades.
    Provides insights for strategy optimization and learning.
    """

    def __init__(self, db):
        """
        Initialize analyzer with database connection.

        Args:
            db: TradeDatabase instance
        """
        self.db = db
        logger.info("Performance Analyzer initialized")

    def analyze_indicator_performance(self) -> Dict[str, Any]:
        """
        Analyze which indicator conditions lead to winning vs losing trades.

        Returns:
            Dictionary with performance metrics per indicator
        """
        winning_trades = self.db.get_winning_trades(limit=500)
        losing_trades = self.db.get_losing_trades(limit=500)

        if len(winning_trades) < 10 or len(losing_trades) < 10:
            logger.warning("Insufficient trade data for indicator analysis")
            return {}

        analysis = {
            'rsi': self._analyze_rsi(winning_trades, losing_trades),
            'macd': self._analyze_macd(winning_trades, losing_trades),
            'moving_averages': self._analyze_ma(winning_trades, losing_trades),
            'volume': self._analyze_volume(winning_trades, losing_trades),
            'trend': self._analyze_trend(winning_trades, losing_trades),
            'overall': {
                'total_winning_trades': len(winning_trades),
                'total_losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / (len(winning_trades) + len(losing_trades))
            }
        }

        logger.info(f"Indicator performance analyzed: {len(winning_trades)} wins, {len(losing_trades)} losses")
        return analysis

    def _analyze_rsi(self, winning: List[Dict], losing: List[Dict]) -> Dict[str, Any]:
        """Analyze RSI performance in winning vs losing trades."""
        win_rsi = [t['rsi'] for t in winning if t.get('rsi')]
        lose_rsi = [t['rsi'] for t in losing if t.get('rsi')]

        if not win_rsi or not lose_rsi:
            return {'error': 'Insufficient RSI data'}

        return {
            'avg_winning_rsi': np.mean(win_rsi),
            'avg_losing_rsi': np.mean(lose_rsi),
            'winning_rsi_std': np.std(win_rsi),
            'losing_rsi_std': np.std(lose_rsi),
            'optimal_range': self._find_optimal_rsi_range(winning, losing),
            'recommendation': self._generate_rsi_recommendation(win_rsi, lose_rsi)
        }

    def _find_optimal_rsi_range(self, winning: List[Dict], losing: List[Dict]) -> Dict[str, float]:
        """Find RSI range with highest win rate."""
        ranges = [(0, 30), (30, 40), (40, 60), (60, 70), (70, 100)]
        best_range = None
        best_win_rate = 0

        for low, high in ranges:
            wins_in_range = sum(1 for t in winning if t.get('rsi') and low <= t['rsi'] < high)
            losses_in_range = sum(1 for t in losing if t.get('rsi') and low <= t['rsi'] < high)

            total = wins_in_range + losses_in_range
            if total > 5:  # Minimum sample size
                win_rate = wins_in_range / total
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_range = (low, high)

        return {
            'lower': best_range[0] if best_range else 30,
            'upper': best_range[1] if best_range else 70,
            'win_rate': best_win_rate
        }

    def _generate_rsi_recommendation(self, win_rsi: List[float], lose_rsi: List[float]) -> str:
        """Generate recommendation for RSI usage."""
        avg_win = np.mean(win_rsi)
        avg_lose = np.mean(lose_rsi)

        if avg_win < 35 and avg_lose > 35:
            return "Increase RSI weight for oversold conditions"
        elif avg_win > 65 and avg_lose < 65:
            return "Increase RSI weight for overbought conditions"
        else:
            return "Current RSI usage appears balanced"

    def _analyze_macd(self, winning: List[Dict], losing: List[Dict]) -> Dict[str, Any]:
        """Analyze MACD performance."""
        win_macd_hist = [t['macd_hist'] for t in winning if t.get('macd_hist') is not None]
        lose_macd_hist = [t['macd_hist'] for t in losing if t.get('macd_hist') is not None]

        if not win_macd_hist or not lose_macd_hist:
            return {'error': 'Insufficient MACD data'}

        # Analyze bullish vs bearish crossovers
        win_bullish = sum(1 for h in win_macd_hist if h > 0)
        lose_bullish = sum(1 for h in lose_macd_hist if h > 0)

        return {
            'avg_winning_macd_hist': np.mean(win_macd_hist),
            'avg_losing_macd_hist': np.mean(lose_macd_hist),
            'bullish_win_rate': win_bullish / len(win_macd_hist) if win_macd_hist else 0,
            'bullish_lose_rate': lose_bullish / len(lose_macd_hist) if lose_macd_hist else 0,
            'recommendation': self._generate_macd_recommendation(win_macd_hist, lose_macd_hist)
        }

    def _generate_macd_recommendation(self, win_hist: List[float], lose_hist: List[float]) -> str:
        """Generate recommendation for MACD usage."""
        avg_win_hist = np.mean(win_hist)
        avg_lose_hist = np.mean(lose_hist)

        if avg_win_hist > 0 and avg_lose_hist < 0:
            return "Strong bullish MACD signals are reliable - increase weight"
        elif abs(avg_win_hist - avg_lose_hist) < 0.001:
            return "MACD not providing clear edge - consider reducing weight"
        else:
            return "Current MACD usage appears effective"

    def _analyze_ma(self, winning: List[Dict], losing: List[Dict]) -> Dict[str, Any]:
        """Analyze moving average crossover performance."""
        win_ma_crossover = []
        lose_ma_crossover = []

        for t in winning:
            if t.get('sma_short') and t.get('sma_long'):
                win_ma_crossover.append(t['sma_short'] - t['sma_long'])

        for t in losing:
            if t.get('sma_short') and t.get('sma_long'):
                lose_ma_crossover.append(t['sma_short'] - t['sma_long'])

        if not win_ma_crossover or not lose_ma_crossover:
            return {'error': 'Insufficient MA data'}

        return {
            'avg_winning_crossover': np.mean(win_ma_crossover),
            'avg_losing_crossover': np.mean(lose_ma_crossover),
            'winning_positive_crossover_rate': sum(1 for x in win_ma_crossover if x > 0) / len(win_ma_crossover),
            'recommendation': "Golden cross signals are effective" if np.mean(win_ma_crossover) > 0 else "Review MA period settings"
        }

    def _analyze_volume(self, winning: List[Dict], losing: List[Dict]) -> Dict[str, Any]:
        """Analyze volume conditions."""
        win_vol_ratio = [t['volume_ratio'] for t in winning if t.get('volume_ratio')]
        lose_vol_ratio = [t['volume_ratio'] for t in losing if t.get('volume_ratio')]

        if not win_vol_ratio or not lose_vol_ratio:
            return {'error': 'Insufficient volume data'}

        return {
            'avg_winning_volume_ratio': np.mean(win_vol_ratio),
            'avg_losing_volume_ratio': np.mean(lose_vol_ratio),
            'high_volume_advantage': np.mean(win_vol_ratio) - np.mean(lose_vol_ratio),
            'recommendation': "High volume confirms good trades" if np.mean(win_vol_ratio) > np.mean(lose_vol_ratio) else "Volume not providing clear edge"
        }

    def _analyze_trend(self, winning: List[Dict], losing: List[Dict]) -> Dict[str, Any]:
        """Analyze trend conditions."""
        win_trends = [t['trend'] for t in winning if t.get('trend')]
        lose_trends = [t['trend'] for t in losing if t.get('trend')]

        if not win_trends or not lose_trends:
            return {'error': 'Insufficient trend data'}

        win_trend_counts = defaultdict(int)
        lose_trend_counts = defaultdict(int)

        for trend in win_trends:
            win_trend_counts[trend] += 1
        for trend in lose_trends:
            lose_trend_counts[trend] += 1

        return {
            'winning_trend_distribution': dict(win_trend_counts),
            'losing_trend_distribution': dict(lose_trend_counts),
            'best_trend': max(win_trend_counts.items(), key=lambda x: x[1])[0] if win_trend_counts else 'unknown',
            'recommendation': self._generate_trend_recommendation(win_trend_counts, lose_trend_counts)
        }

    def _generate_trend_recommendation(self, win_counts: Dict, lose_counts: Dict) -> str:
        """Generate recommendation for trend trading."""
        if win_counts.get('uptrend', 0) > win_counts.get('downtrend', 0):
            return "Focus on long positions in uptrends"
        elif win_counts.get('downtrend', 0) > win_counts.get('uptrend', 0):
            return "Focus on short positions in downtrends"
        else:
            return "Current trend following strategy is balanced"

    def calculate_optimal_weights(self) -> Dict[str, float]:
        """
        Calculate optimal indicator weights based on historical performance.

        Returns:
            Dictionary with suggested weights for each indicator
        """
        indicator_perf = self.analyze_indicator_performance()

        if not indicator_perf or 'overall' not in indicator_perf:
            logger.warning("Cannot calculate optimal weights - insufficient data")
            return {
                'rsi': 0.25,
                'macd': 0.25,
                'moving_averages': 0.25,
                'volume': 0.15,
                'trend': 0.10
            }

        # Score each indicator based on its predictive power
        scores = {}

        # RSI scoring
        rsi_data = indicator_perf.get('rsi', {})
        if 'optimal_range' in rsi_data and rsi_data['optimal_range'].get('win_rate', 0) > 0.6:
            scores['rsi'] = rsi_data['optimal_range']['win_rate']
        else:
            scores['rsi'] = 0.5

        # MACD scoring
        macd_data = indicator_perf.get('macd', {})
        if 'bullish_win_rate' in macd_data:
            scores['macd'] = abs(macd_data['bullish_win_rate'] - macd_data.get('bullish_lose_rate', 0.5))
        else:
            scores['macd'] = 0.5

        # MA scoring
        ma_data = indicator_perf.get('moving_averages', {})
        if 'winning_positive_crossover_rate' in ma_data:
            scores['moving_averages'] = ma_data['winning_positive_crossover_rate']
        else:
            scores['moving_averages'] = 0.5

        # Volume scoring
        vol_data = indicator_perf.get('volume', {})
        if 'high_volume_advantage' in vol_data and vol_data['high_volume_advantage'] > 0:
            scores['volume'] = min(0.8, 0.5 + vol_data['high_volume_advantage'])
        else:
            scores['volume'] = 0.4

        # Trend scoring
        trend_data = indicator_perf.get('trend', {})
        scores['trend'] = 0.5  # Base score

        # Normalize scores to weights summing to 1.0
        total_score = sum(scores.values())
        weights = {k: v / total_score for k, v in scores.items()}

        logger.info(f"Calculated optimal weights: {weights}")
        return weights

    def identify_learning_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify specific areas where bot can improve.

        Returns:
            List of learning opportunities with actionable recommendations
        """
        opportunities = []

        # Get performance data
        stats = self.db.get_performance_stats(days=30)
        indicator_perf = self.analyze_indicator_performance()

        # Check overall win rate
        if stats['win_rate'] < 0.5:
            opportunities.append({
                'type': 'low_win_rate',
                'severity': 'high',
                'current_value': stats['win_rate'],
                'target_value': 0.55,
                'recommendation': 'Overall win rate is low. Consider tightening entry criteria or adjusting indicator weights.',
                'action': 'increase_min_confidence'
            })

        # Check profit factor
        if stats.get('profit_factor', 0) < 1.5:
            opportunities.append({
                'type': 'low_profit_factor',
                'severity': 'high',
                'current_value': stats.get('profit_factor', 0),
                'target_value': 2.0,
                'recommendation': 'Profit factor is low. Winning trades are not large enough compared to losses.',
                'action': 'adjust_take_profit_ratio'
            })

        # Check for indicator-specific issues
        if indicator_perf:
            for indicator, data in indicator_perf.items():
                if indicator == 'overall':
                    continue

                if isinstance(data, dict) and 'recommendation' in data:
                    if 'increase weight' in data['recommendation'].lower():
                        opportunities.append({
                            'type': 'indicator_optimization',
                            'indicator': indicator,
                            'severity': 'medium',
                            'recommendation': data['recommendation'],
                            'action': 'adjust_indicator_weight',
                            'details': data
                        })

        # Check trade duration
        if stats.get('avg_duration') and stats['avg_duration'] > 1440:  # More than 1 day
            opportunities.append({
                'type': 'long_trade_duration',
                'severity': 'low',
                'current_value': stats['avg_duration'],
                'recommendation': 'Trades are held for long periods. Consider tighter stop losses or take profits.',
                'action': 'adjust_exit_criteria'
            })

        logger.info(f"Identified {len(opportunities)} learning opportunities")
        return opportunities

    def compare_strategy_versions(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Compare current strategy performance to previous periods.

        Args:
            days_back: Days to look back for comparison

        Returns:
            Comparison metrics
        """
        current_stats = self.db.get_performance_stats(days=days_back)

        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM strategy_performance
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        previous = cursor.fetchone()

        if not previous:
            return {'status': 'no_previous_data'}

        comparison = {
            'current': current_stats,
            'previous': dict(previous),
            'improvements': {},
            'regressions': {}
        }

        # Compare key metrics
        metrics = ['win_rate', 'total_pnl', 'profit_factor']

        for metric in metrics:
            current_val = current_stats.get(metric, 0)
            prev_val = previous[metric] if previous[metric] else 0

            if current_val > prev_val:
                comparison['improvements'][metric] = {
                    'change': current_val - prev_val,
                    'percent_change': ((current_val - prev_val) / prev_val * 100) if prev_val != 0 else 0
                }
            elif current_val < prev_val:
                comparison['regressions'][metric] = {
                    'change': current_val - prev_val,
                    'percent_change': ((current_val - prev_val) / prev_val * 100) if prev_val != 0 else 0
                }

        return comparison

    def generate_performance_report(self) -> str:
        """
        Generate a human-readable performance report.

        Returns:
            Formatted performance report string
        """
        stats = self.db.get_performance_stats(days=30)
        opportunities = self.identify_learning_opportunities()

        report = "\n" + "=" * 60 + "\n"
        report += "TRADING BOT PERFORMANCE REPORT (Last 30 Days)\n"
        report += "=" * 60 + "\n\n"

        report += "Overall Performance:\n"
        report += f"  Total Trades: {stats['total_trades']}\n"
        report += f"  Win Rate: {stats['win_rate']:.2%}\n"
        report += f"  Total P&L: ${stats['total_pnl']:.2f}\n"
        report += f"  Profit Factor: {stats.get('profit_factor', 0):.2f}\n"
        report += f"  Average Win: ${stats.get('avg_win', 0):.2f}\n"
        report += f"  Average Loss: ${stats.get('avg_loss', 0):.2f}\n\n"

        if opportunities:
            report += "Learning Opportunities:\n"
            for i, opp in enumerate(opportunities, 1):
                report += f"  {i}. [{opp['severity'].upper()}] {opp['type']}\n"
                report += f"     {opp['recommendation']}\n"

        report += "\n" + "=" * 60 + "\n"

        return report
