"""
Loss Pattern Analyzer - Learns from losing trades to improve strategy
Analyzes WHY trades lose and generates actionable insights
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import sqlite3

logger = logging.getLogger(__name__)


class LossPatternAnalyzer:
    """
    Analyzes patterns in losing trades to identify:
    1. Symbols that consistently lose
    2. Stop loss distances that get hit too often
    3. Market conditions that lead to losses
    4. Timing issues (exits too early/late)
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.min_trades_for_analysis = 10
        self.poor_performance_threshold = 10.0  # < 10% win rate = poor
        self.acceptable_win_rate = 35.0  # Target: >35% win rate

    def analyze_symbol_performance(self) -> Dict:
        """
        Analyze which symbols are consistently losing

        Returns:
            Dict with symbol blacklist and recommendations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                symbol,
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
                CAST(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100 as win_rate,
                AVG(pnl) as avg_pnl
            FROM trades
            WHERE status='closed'
            GROUP BY symbol
            HAVING total_trades >= ?
            ORDER BY win_rate ASC
        ''', (self.min_trades_for_analysis,))

        results = cursor.fetchall()
        conn.close()

        blacklist = []
        warnings = []
        recommended = []

        for row in results:
            symbol, total, wins, losses, win_rate, avg_pnl = row

            if win_rate < self.poor_performance_threshold:
                blacklist.append({
                    'symbol': symbol,
                    'win_rate': win_rate,
                    'total_trades': total,
                    'avg_pnl': avg_pnl,
                    'reason': f'Consistently losing: {win_rate:.1f}% WR ({wins}W/{losses}L)'
                })
            elif win_rate < self.acceptable_win_rate / 2:  # < 17.5%
                warnings.append({
                    'symbol': symbol,
                    'win_rate': win_rate,
                    'total_trades': total,
                    'reason': f'Poor performance: {win_rate:.1f}% WR'
                })
            elif win_rate >= self.acceptable_win_rate / 2:  # Best performers
                recommended.append({
                    'symbol': symbol,
                    'win_rate': win_rate,
                    'total_trades': total,
                    'avg_pnl': avg_pnl
                })

        return {
            'blacklist': blacklist,
            'warnings': warnings,
            'recommended': recommended[:5]  # Top 5 performers
        }

    def analyze_stop_loss_effectiveness(self) -> Dict:
        """
        Analyze if stop losses are:
        1. Too tight (hit by normal volatility)
        2. Appropriate
        3. Too wide (bleeding losses)

        Returns:
            Dict with stop loss recommendations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Analyze SL hit timing
        cursor.execute('''
            SELECT
                AVG(ABS(entry_price - stop_loss) / entry_price * 100) as avg_sl_pct,
                COUNT(*) as total_sl_hits,
                SUM(CASE WHEN duration_minutes < 30 THEN 1 ELSE 0 END) as quick_hits,
                AVG(pnl_percent) as avg_loss_pct
            FROM trades
            WHERE status='closed' AND pnl <= 0 AND exit_reason LIKE '%Stop%' AND stop_loss IS NOT NULL
        ''')

        row = cursor.fetchone()
        avg_sl_pct, total_hits, quick_hits, avg_loss = row

        # Analyze winners vs losers duration
        cursor.execute('''
            SELECT
                AVG(CASE WHEN pnl > 0 THEN duration_minutes END) as winner_duration,
                AVG(CASE WHEN pnl <= 0 THEN duration_minutes END) as loser_duration,
                AVG(CASE WHEN pnl > 0 THEN pnl_percent END) as avg_win_pct,
                AVG(CASE WHEN pnl <= 0 THEN pnl_percent END) as avg_loss_pct
            FROM trades
            WHERE status='closed'
        ''')

        row = cursor.fetchone()
        winner_duration, loser_duration, avg_win, avg_loss = row

        conn.close()

        # Determine if SL is too tight
        quick_hit_ratio = quick_hits / total_hits if total_hits > 0 else 0
        too_tight = quick_hit_ratio > 0.6  # >60% hit in <30min = too tight

        issue = None
        recommendation = None

        if too_tight:
            issue = f"Stop loss TOO TIGHT: {quick_hit_ratio*100:.0f}% hit in <30min (noise, not invalidation)"
            # Recommend 2x the average loss to give room
            recommended_sl = abs(avg_loss) * 2 if avg_loss else 1.5
            recommendation = f"Increase SL to {recommended_sl:.1f}% (from {avg_sl_pct:.2f}%)"
        elif avg_sl_pct and avg_sl_pct < 1.0:
            issue = f"SL too tight ({avg_sl_pct:.2f}%) for crypto volatility"
            recommendation = "Increase SL to at least 1.5-2.0%"
        else:
            recommendation = f"Current SL ({avg_sl_pct:.2f}%) seems reasonable"

        return {
            'current_avg_sl': avg_sl_pct,
            'total_sl_hits': total_hits,
            'quick_hits': quick_hits,
            'quick_hit_ratio': quick_hit_ratio,
            'too_tight': too_tight,
            'issue': issue,
            'recommendation': recommendation,
            'winner_duration_min': winner_duration,
            'loser_duration_min': loser_duration,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss
        }

    def analyze_timing_patterns(self) -> Dict:
        """
        Analyze if trades are exited too early or too late
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                CASE
                    WHEN duration_minutes < 60 THEN '< 1h (scalp)'
                    WHEN duration_minutes < 360 THEN '1-6h (intraday)'
                    WHEN duration_minutes < 1440 THEN '6-24h (swing)'
                    ELSE '> 24h (position)'
                END as timeframe,
                COUNT(*) as total,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                CAST(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100 as win_rate
            FROM trades
            WHERE status='closed'
            GROUP BY timeframe
            ORDER BY
                CASE timeframe
                    WHEN '< 1h (scalp)' THEN 1
                    WHEN '1-6h (intraday)' THEN 2
                    WHEN '6-24h (swing)' THEN 3
                    ELSE 4
                END
        ''')

        results = cursor.fetchall()
        conn.close()

        best_timeframe = None
        best_wr = 0

        timeframes = []
        for row in results:
            tf, total, wins, wr = row
            timeframes.append({
                'timeframe': tf,
                'total': total,
                'wins': wins,
                'win_rate': wr
            })
            if wr > best_wr:
                best_wr = wr
                best_timeframe = tf

        return {
            'timeframes': timeframes,
            'best_timeframe': best_timeframe,
            'best_win_rate': best_wr,
            'recommendation': f"Focus on {best_timeframe} holds (WR: {best_wr:.1f}%)" if best_timeframe else "Insufficient data"
        }

    def generate_actionable_insights(self) -> Dict:
        """
        Generate complete analysis with actionable recommendations
        """
        logger.info("🔍 Analyzing loss patterns...")

        symbol_analysis = self.analyze_symbol_performance()
        sl_analysis = self.analyze_stop_loss_effectiveness()
        timing_analysis = self.analyze_timing_patterns()

        insights = {
            'timestamp': datetime.now().isoformat(),
            'symbol_performance': symbol_analysis,
            'stop_loss_analysis': sl_analysis,
            'timing_analysis': timing_analysis,
            'action_items': []
        }

        # Generate action items
        if symbol_analysis['blacklist']:
            insights['action_items'].append({
                'priority': 'HIGH',
                'action': 'BLACKLIST_SYMBOLS',
                'symbols': [s['symbol'] for s in symbol_analysis['blacklist']],
                'reason': 'Consistently losing (< 10% WR)'
            })

        if sl_analysis['too_tight']:
            insights['action_items'].append({
                'priority': 'CRITICAL',
                'action': 'INCREASE_STOP_LOSS',
                'current': sl_analysis['current_avg_sl'],
                'recommended': abs(sl_analysis['avg_loss_pct']) * 2 if sl_analysis['avg_loss_pct'] else 1.5,
                'reason': sl_analysis['issue']
            })

        if symbol_analysis['recommended']:
            insights['action_items'].append({
                'priority': 'MEDIUM',
                'action': 'PRIORITIZE_SYMBOLS',
                'symbols': [s['symbol'] for s in symbol_analysis['recommended']],
                'reason': 'Best performing symbols'
            })

        return insights

    def print_analysis_report(self, insights: Dict):
        """Pretty print the analysis report"""
        print("\n" + "="*60)
        print("LOSS PATTERN ANALYSIS REPORT")
        print("="*60)

        # Symbol blacklist
        if insights['symbol_performance']['blacklist']:
            print("\n❌ SYMBOLS TO BLACKLIST (<10% WR):")
            for s in insights['symbol_performance']['blacklist']:
                print(f"  - {s['symbol']}: {s['win_rate']:.1f}% WR - {s['reason']}")

        # Symbol warnings
        if insights['symbol_performance']['warnings']:
            print("\n⚠️ SYMBOLS TO WATCH:")
            for s in insights['symbol_performance']['warnings']:
                print(f"  - {s['symbol']}: {s['win_rate']:.1f}% WR")

        # Best symbols
        if insights['symbol_performance']['recommended']:
            print("\n✅ BEST PERFORMING SYMBOLS:")
            for s in insights['symbol_performance']['recommended']:
                print(f"  - {s['symbol']}: {s['win_rate']:.1f}% WR ({s['total_trades']} trades)")

        # Stop loss analysis
        print("\n📏 STOP LOSS ANALYSIS:")
        sl = insights['stop_loss_analysis']
        print(f"  Current avg SL: {sl['current_avg_sl']:.2f}%")
        print(f"  Quick hits (<30min): {sl['quick_hits']}/{sl['total_sl_hits']} ({sl['quick_hit_ratio']*100:.0f}%)")
        if sl['issue']:
            print(f"  ⚠️ ISSUE: {sl['issue']}")
        print(f"  💡 RECOMMENDATION: {sl['recommendation']}")

        # Timing analysis
        print("\n⏱️ TIMING ANALYSIS:")
        for tf in insights['timing_analysis']['timeframes']:
            print(f"  {tf['timeframe']}: {tf['win_rate']:.1f}% WR ({tf['wins']}W from {tf['total']} trades)")
        print(f"  💡 {insights['timing_analysis']['recommendation']}")

        # Action items
        if insights['action_items']:
            print("\n🎯 ACTION ITEMS:")
            for item in insights['action_items']:
                print(f"  [{item['priority']}] {item['action']}")
                if 'symbols' in item:
                    print(f"    Symbols: {', '.join(item['symbols'])}")
                if 'current' in item and 'recommended' in item:
                    print(f"    Change: {item['current']:.2f}% → {item['recommended']:.1f}%")
                print(f"    Reason: {item['reason']}")

        print("\n" + "="*60)


if __name__ == "__main__":
    # Test module standalone
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/trading_history.db'

    analyzer = LossPatternAnalyzer(db_path)
    insights = analyzer.generate_actionable_insights()
    analyzer.print_analysis_report(insights)
