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

    def __init__(self, db: TradeDatabase, config: dict, risk_manager=None):
        """
        Initialize the autonomous watchdog.

        Args:
            db: TradeDatabase instance
            config: Bot configuration
            risk_manager: RiskManager instance (for clearing phantom positions)
        """
        self.db = db
        self.config = config
        self.risk_manager = risk_manager

        # Thresholds for detection
        self.min_trades_per_hour = 0.5  # LOWERED: 0.5 trades/hour minimum (was 2) - more realistic
        self.max_position_age_hours = 24  # INCREASED: 24h max age (was 6h) - less aggressive closing
        self.confidence_check_interval = 30  # Check every 30 minutes (was 5)

        # Last check timestamps
        self.last_health_check = datetime.now()
        self.last_intervention = None
        self.last_confidence_reset = None  # Track last confidence reset to avoid spam

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

        # Check 0: Clear phantom positions (positions in risk_manager but not in DB)
        phantom_issue = self._clear_phantom_positions()
        if phantom_issue:
            self.issues_detected.append(phantom_issue)

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

    def _clear_phantom_positions(self) -> Optional[str]:
        """
        Clear phantom positions (exist in risk_manager but not in database as OPEN).

        Returns:
            Issue description if phantoms detected, None otherwise
        """
        if not self.risk_manager:
            return None

        # Get open positions from database
        db_open_positions = self.db.get_trade_history(limit=100, status='OPEN')
        db_open_symbols = {pos['symbol'] for pos in db_open_positions}

        # Get positions from risk_manager
        rm_positions = list(self.risk_manager.positions.keys())

        # Find phantoms: in risk_manager but not in DB
        phantoms = [symbol for symbol in rm_positions if symbol not in db_open_symbols]

        if phantoms:
            logger.warning(f"⚠️ PHANTOM POSITIONS DETECTED: {len(phantoms)} positions in memory but not in DB: {phantoms}")

            for symbol in phantoms:
                logger.warning(f"🧹 AUTO-FIX: Clearing phantom position {symbol} from risk_manager")
                # Force close in risk_manager (doesn't matter what price, it's phantom)
                self.risk_manager.close_position(symbol, 0, 'Watchdog: Phantom position cleared')
                self.auto_fixes_applied.append(f"Cleared phantom position: {symbol}")

            self.last_intervention = datetime.now()
            return f"{len(phantoms)} phantom positions cleared: {', '.join(phantoms)}"

        return None

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

            # Check if the real problem is daily_trades limit being hit
            if self.risk_manager:
                current_daily = self.risk_manager.daily_trades
                max_daily = self.config.get('risk', {}).get('max_daily_trades', 80)
                
                if current_daily >= max_daily:
                    logger.error(f"� CRITICAL: Daily trade limit reached ({current_daily}/{max_daily}) - Cannot trade until daily reset!")
                    logger.error(f"   Last reset: {self.risk_manager.last_reset}")
                    logger.error(f"   Current date: {datetime.now().date()}")
                    
                    # Check if daily reset is stuck (should have reset by now)
                    if datetime.now().date() > self.risk_manager.last_reset:
                        logger.error(f"🔧 AUTO-FIX: Daily reset STUCK - Forcing reset NOW")
                        self.risk_manager.daily_trades = 0
                        self.risk_manager.daily_pnl = 0
                        self.risk_manager.last_reset = datetime.now().date()
                        self.auto_fixes_applied.append(f"FORCE daily reset: {current_daily} → 0 trades (stuck reset)")
                        self.last_intervention = datetime.now()
                        return f"Daily trade limit stuck at {current_daily} - FORCE reset applied"
                    
                    # Daily limit legitimately hit - don't spam confidence resets
                    return f"Daily trade limit reached: {current_daily}/{max_daily} (waiting for midnight reset)"

            # Only reset confidence if we haven't done it recently (avoid spam)
            current_conf = self.config.get('strategy', {}).get('min_confidence', 0.05)
            
            # Don't reset confidence if already at or below 3%
            if current_conf <= 0.03:
                logger.info("ℹ️ Confidence already at minimum (3%) - no reset needed")
                return f"Low activity: {recent_count} trades/hour, but confidence already minimal"
            
            # Don't reset confidence more than once per hour
            if self.last_confidence_reset:
                time_since_last_reset = (datetime.now() - self.last_confidence_reset).total_seconds() / 60
                if time_since_last_reset < 60:
                    logger.info(f"ℹ️ Confidence was reset {time_since_last_reset:.0f}min ago - skipping spam reset")
                    return f"Low activity: {recent_count} trades/hour (recent conf reset {time_since_last_reset:.0f}min ago)"

            # AUTO-FIX: Reset confidence to 3%
            logger.warning(f"🔧 AUTO-FIX: Confidence reset {current_conf:.1%} → 3% (low activity)")
            self.config['strategy']['min_confidence'] = 0.03
            self.auto_fixes_applied.append(f"Confidence reset: {current_conf:.1%} → 3%")
            self.last_intervention = datetime.now()
            self.last_confidence_reset = datetime.now()

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
        if stats['total_trades'] > 30 and stats['win_rate'] < 0.30:
            logger.warning(f"⚠️ CRITICAL WIN RATE: {stats['win_rate']:.1%} (expected: >30%)")

            # AUTO-FIX: Increase confidence to be more selective, but CAP at 10%
            current_conf = self.config.get('strategy', {}).get('min_confidence', 0.05)
            
            # Don't adjust if already at or above 10%
            if current_conf >= 0.10:
                logger.info(f"ℹ️ Confidence already at {current_conf:.1%} (max 10%) - no increase")
                return f"Critical win rate: {stats['win_rate']:.1%}, but confidence at max (10%)"
            
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
