"""
Autonomous Watchdog - Self-healing system for the trading bot
Monitors bot health and automatically fixes common issues
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from trade_database import TradeDatabase

logger = logging.getLogger(__name__)


class AutonomousWatchdog:
    """
    Self-healing watchdog that monitors bot health and fixes issues autonomously.

    Monitors:
    - Trading activity (detects when bot stops trading)
    - Confidence levels (detects if too high/low)
    - Position stagnation (detects stuck positions)
    - Performance degradation

    Auto-fixes:
    - Resets confidence if blocking trades
    - Closes stagnant positions
    - Adjusts parameters if performance drops
    """

    def __init__(self, db: TradeDatabase, config: dict):
        """
        Initialize the autonomous watchdog.

        Args:
            db: TradeDatabase instance
            config: Bot configuration
        """
        self.db = db
        self.config = config

        # Thresholds for detection
        self.min_trades_per_hour = 2  # Minimum acceptable trading frequency
        self.max_position_age_hours = 6  # Max time a position should stay open
        self.confidence_check_interval = 30  # Check every 30 minutes

        # Last check timestamps
        self.last_health_check = datetime.now()
        self.last_intervention = None

        # Issues detected
        self.issues_detected: List[str] = []
        self.auto_fixes_applied: List[str] = []

        logger.info("🤖 Autonomous Watchdog initialized - Self-healing mode ACTIVE")

    def health_check(self) -> Dict:
        """
        Perform comprehensive health check.

        Returns:
            Dict with health status and any issues detected
        """
        now = datetime.now()
        self.issues_detected = []
        self.auto_fixes_applied = []

        # Check 1: Trading activity
        trading_issue = self._check_trading_activity()
        if trading_issue:
            self.issues_detected.append(trading_issue)

        # Check 2: Confidence level
        confidence_issue = self._check_confidence_level()
        if confidence_issue:
            self.issues_detected.append(confidence_issue)

        # Check 3: Stuck positions
        position_issue = self._check_stuck_positions()
        if position_issue:
            self.issues_detected.append(position_issue)

        # Check 4: Performance degradation
        perf_issue = self._check_performance()
        if perf_issue:
            self.issues_detected.append(perf_issue)

        self.last_health_check = now

        return {
            'timestamp': now,
            'healthy': len(self.issues_detected) == 0,
            'issues': self.issues_detected,
            'fixes_applied': self.auto_fixes_applied
        }

    def _check_trading_activity(self) -> Optional[str]:
        """
        Check if bot is trading at acceptable frequency.

        Returns:
            Issue description if problem detected, None otherwise
        """
        # Get trades from last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_trades = self.db.get_trade_history(limit=1000)

        # Filter trades from last hour
        recent_count = sum(1 for t in recent_trades
                          if datetime.fromisoformat(t['entry_time']) > one_hour_ago)

        if recent_count < self.min_trades_per_hour:
            logger.warning(f"⚠️ LOW TRADING ACTIVITY: Only {recent_count} trades in last hour (min: {self.min_trades_per_hour})")

            # AUTO-FIX 1: Lower confidence to minimum
            current_conf = self.config.get('strategy', {}).get('min_confidence', 0.05)
            if current_conf > 0.03:  # If confidence > 3%, force to minimum
                logger.warning(f"🔧 AUTO-FIX: EMERGENCY confidence reset {current_conf:.1%} → 3% to force trading")
                self.config['strategy']['min_confidence'] = 0.03
                self.auto_fixes_applied.append(f"EMERGENCY reset: confidence {current_conf:.1%} → 3%")
                self.last_intervention = datetime.now()

            # AUTO-FIX 2: Force close ALL open positions to free up space
            open_positions = self.db.get_trade_history(limit=100, status='OPEN')
            if open_positions:
                logger.warning(f"🔧 AUTO-FIX: Force-closing ALL {len(open_positions)} positions to restart trading")
                for pos in open_positions:
                    now = datetime.now()
                    self.db.update_trade(pos['id'], {
                        'status': 'closed',
                        'exit_price': pos['entry_price'],
                        'exit_time': now,
                        'pnl': 0,
                        'pnl_percent': 0,
                        'exit_reason': 'Watchdog: Emergency close - no trading activity',
                        'duration_minutes': (now - datetime.fromisoformat(pos['entry_time'])).total_seconds() / 60
                    })
                self.auto_fixes_applied.append(f"Force-closed {len(open_positions)} positions (emergency restart)")
                self.last_intervention = datetime.now()

            return f"Low trading activity: {recent_count} trades/hour (expected: ≥{self.min_trades_per_hour})"

        return None

    def _check_confidence_level(self) -> Optional[str]:
        """
        Check if confidence level is in healthy range.

        Returns:
            Issue description if problem detected, None otherwise
        """
        current_conf = self.config.get('strategy', {}).get('min_confidence', 0.05)

        # Too high: Will block most trades (signals typically 14-20%)
        if current_conf > 0.15:
            logger.warning(f"⚠️ CONFIDENCE TOO HIGH: {current_conf:.1%} (max safe: 15%)")

            # AUTO-FIX: Force reset to 5%
            logger.warning(f"🔧 AUTO-FIX: EMERGENCY confidence reset {current_conf:.1%} → 5%")
            self.config['strategy']['min_confidence'] = 0.05
            self.auto_fixes_applied.append(f"EMERGENCY reset: confidence {current_conf:.1%} → 5%")
            self.last_intervention = datetime.now()

            return f"Confidence dangerously high: {current_conf:.1%} (safe max: 15%)"

        # Too low: Might take too many bad trades
        elif current_conf < 0.03:
            logger.warning(f"⚠️ CONFIDENCE TOO LOW: {current_conf:.1%} (min safe: 3%)")

            # AUTO-FIX: Raise to 5%
            logger.warning(f"🔧 AUTO-FIX: Raising confidence from {current_conf:.1%} to 5%")
            self.config['strategy']['min_confidence'] = 0.05
            self.auto_fixes_applied.append(f"Raised confidence {current_conf:.1%} → 5%")
            self.last_intervention = datetime.now()

            return f"Confidence too low: {current_conf:.1%} (safe min: 3%)"

        return None

    def _check_stuck_positions(self) -> Optional[str]:
        """
        Check for positions that have been open too long.

        Returns:
            Issue description if problem detected, None otherwise
        """
        open_positions = self.db.get_trade_history(limit=100, status='OPEN')

        if not open_positions:
            return None

        now = datetime.now()
        stuck_positions = []

        for pos in open_positions:
            entry_time = datetime.fromisoformat(pos['entry_time'])
            age_hours = (now - entry_time).total_seconds() / 3600

            if age_hours > self.max_position_age_hours:
                stuck_positions.append({
                    'symbol': pos['symbol'],
                    'age_hours': age_hours,
                    'trade_id': pos['id']
                })

        if stuck_positions:
            logger.warning(f"⚠️ STUCK POSITIONS DETECTED: {len(stuck_positions)} positions open > {self.max_position_age_hours}h")

            # AUTO-FIX: Close stagnant positions at breakeven
            for pos in stuck_positions:
                logger.warning(f"🔧 AUTO-FIX: Force-closing stagnant position {pos['symbol']} (age: {pos['age_hours']:.1f}h)")

                # Close at entry price (breakeven)
                trade = self.db.get_trade_with_conditions(pos['trade_id'])
                if trade:
                    self.db.update_trade(pos['trade_id'], {
                        'status': 'closed',
                        'exit_price': trade['entry_price'],
                        'exit_time': now,
                        'pnl': 0,
                        'pnl_percent': 0,
                        'exit_reason': 'Watchdog: Stagnant position force-closed',
                        'duration_minutes': pos['age_hours'] * 60
                    })

                    self.auto_fixes_applied.append(f"Closed stagnant {pos['symbol']} ({pos['age_hours']:.1f}h old)")

            self.last_intervention = datetime.now()
            return f"{len(stuck_positions)} positions stuck > {self.max_position_age_hours}h"

        return None

    def _check_performance(self) -> Optional[str]:
        """
        Check if performance is degrading significantly.

        Returns:
            Issue description if problem detected, None otherwise
        """
        stats = self.db.get_performance_stats(days=1)

        # Check if win rate is critically low
        if stats['total_trades'] > 20 and stats['win_rate'] < 0.25:
            logger.warning(f"⚠️ CRITICAL WIN RATE: {stats['win_rate']:.1%} (expected: >30%)")

            # AUTO-FIX: Increase confidence to be more selective
            current_conf = self.config.get('strategy', {}).get('min_confidence', 0.05)
            new_conf = min(0.10, current_conf + 0.02)  # Increase by 2%, max 10%

            logger.warning(f"🔧 AUTO-FIX: Increasing selectivity {current_conf:.1%} → {new_conf:.1%}")
            self.config['strategy']['min_confidence'] = new_conf
            self.auto_fixes_applied.append(f"Increased selectivity: {current_conf:.1%} → {new_conf:.1%} (win rate too low)")
            self.last_intervention = datetime.now()

            return f"Critical win rate: {stats['win_rate']:.1%} (expected: >30%)"

        return None

    def should_run_check(self) -> bool:
        """
        Determine if it's time to run a health check.

        Returns:
            True if check should run, False otherwise
        """
        if not self.last_health_check:
            return True

        time_since_check = (datetime.now() - self.last_health_check).total_seconds() / 60
        return time_since_check >= self.confidence_check_interval

    def get_status_report(self) -> str:
        """
        Generate a status report for logging/notifications.

        Returns:
            Formatted status report
        """
        status = "🤖 AUTONOMOUS WATCHDOG STATUS\n\n"

        if self.issues_detected:
            status += f"⚠️ {len(self.issues_detected)} Issues Detected:\n"
            for issue in self.issues_detected:
                status += f"  • {issue}\n"
        else:
            status += "✅ All systems healthy\n"

        if self.auto_fixes_applied:
            status += f"\n🔧 {len(self.auto_fixes_applied)} Auto-fixes Applied:\n"
            for fix in self.auto_fixes_applied:
                status += f"  • {fix}\n"

        if self.last_intervention:
            time_since = (datetime.now() - self.last_intervention).total_seconds() / 60
            status += f"\n⏱️ Last intervention: {time_since:.0f} minutes ago\n"

        return status
