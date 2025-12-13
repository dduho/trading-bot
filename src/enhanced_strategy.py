"""
Enhanced Trading Strategy
Improves win rate through better market analysis and entry/exit management
"""

import logging
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EnhancedStrategy:
    """
    Improved trading strategy with:
    - Market regime detection (trending vs ranging)
    - Volume analysis
    - Multi-timeframe confirmation
    - Dynamic stop loss and take profit
    - Better exit timing
    """

    def __init__(self, config: dict):
        self.config = config

        # Market regime thresholds
        self.trending_adx_threshold = 25  # ADX > 25 = trending
        self.ranging_adx_threshold = 20   # ADX < 20 = ranging

        # Volume thresholds
        self.min_volume_ratio = 0.8  # Current volume must be 80% of average

        # Win rate tracking for adaptive behavior
        self.recent_trades = []
        self.max_recent_trades = 50

        logger.info("🚀 Enhanced Strategy initialized")

    def analyze_market_regime(self, df) -> Dict:
        """
        Determine if market is trending or ranging
        Returns regime info for strategy adjustment
        """
        try:
            latest = df.iloc[-1]

            adx = latest.get('adx', 0)
            atr = latest.get('atr', 0)
            bb_width = latest.get('bb_width', 0)

            # Determine regime
            if adx > self.trending_adx_threshold:
                regime = 'trending'
                confidence = min((adx - self.trending_adx_threshold) / 30, 1.0)
            elif adx < self.ranging_adx_threshold:
                regime = 'ranging'
                confidence = min((self.ranging_adx_threshold - adx) / 20, 1.0)
            else:
                regime = 'transitional'
                confidence = 0.5

            # Add volatility info
            volatility = 'high' if atr > df['atr'].mean() * 1.2 else 'normal'
            if atr < df['atr'].mean() * 0.8:
                volatility = 'low'

            return {
                'regime': regime,
                'confidence': confidence,
                'volatility': volatility,
                'adx': adx,
                'atr': atr,
                'bb_width': bb_width
            }

        except Exception as e:
            logger.error(f"Error analyzing market regime: {e}")
            return {
                'regime': 'unknown',
                'confidence': 0,
                'volatility': 'unknown'
            }

    def check_volume_conditions(self, df) -> Tuple[bool, str]:
        """
        Verify volume is sufficient for quality trade
        Low volume = bad liquidity = wider spreads = worse execution
        """
        try:
            if 'volume' not in df.columns:
                return True, "Volume data not available"

            latest_volume = df.iloc[-1]['volume']
            avg_volume = df['volume'].tail(20).mean()

            if latest_volume < avg_volume * self.min_volume_ratio:
                return False, f"Low volume: {latest_volume/avg_volume:.1%} of average"

            return True, f"Volume OK: {latest_volume/avg_volume:.1%} of average"

        except Exception as e:
            logger.error(f"Error checking volume: {e}")
            return True, "Volume check failed"

    def get_dynamic_stops(self, df, side: str, entry_price: float, regime: Dict) -> Tuple[float, float]:
        """
        Calculate dynamic stop loss and take profit based on:
        - Market regime (wider stops in trending, tighter in ranging)
        - Current volatility (ATR-based)
        - Recent win rate (tighter if losing streak)
        """
        try:
            latest = df.iloc[-1]
            atr = latest.get('atr', entry_price * 0.01)

            # Base stop on ATR for volatility adjustment
            # Problem identified: Fixed 1.5% stops are too wide
            # Solution: Use 2x ATR (adaptive to volatility)
            base_stop_distance = 2.0 * atr

            # Adjust for regime
            if regime['regime'] == 'trending':
                # Trending: wider stops (let trends run)
                stop_multiplier = 1.2
                tp_multiplier = 2.5  # Higher profit targets in trends
            elif regime['regime'] == 'ranging':
                # Ranging: tighter stops (quick in/out)
                stop_multiplier = 0.8
                tp_multiplier = 1.5  # Lower targets in ranges
            else:
                # Transitional: moderate
                stop_multiplier = 1.0
                tp_multiplier = 2.0

            # Calculate final stops
            stop_distance = base_stop_distance * stop_multiplier
            tp_distance = base_stop_distance * tp_multiplier

            # Cap stop loss (max 2% in any case)
            max_stop = entry_price * 0.02
            stop_distance = min(stop_distance, max_stop)

            # Minimum risk/reward ratio of 1.5
            if tp_distance < stop_distance * 1.5:
                tp_distance = stop_distance * 1.5

            if side == 'long':
                stop_loss = entry_price - stop_distance
                take_profit = entry_price + tp_distance
            else:  # short
                stop_loss = entry_price + stop_distance
                take_profit = entry_price - tp_distance

            logger.info(f"Dynamic stops: SL={stop_distance/entry_price*100:.2f}%, TP={tp_distance/entry_price*100:.2f}%, R:R={tp_distance/stop_distance:.1f}")

            return stop_loss, take_profit

        except Exception as e:
            logger.error(f"Error calculating dynamic stops: {e}")
            # Fallback to config defaults
            default_stop_pct = self.config.get('risk', {}).get('stop_loss_percent', 1.5) / 100
            default_tp_pct = self.config.get('risk', {}).get('take_profit_percent', 3.0) / 100

            if side == 'long':
                return entry_price * (1 - default_stop_pct), entry_price * (1 + default_tp_pct)
            else:
                return entry_price * (1 + default_stop_pct), entry_price * (1 - default_tp_pct)

    def should_take_trade(self, signal: Dict, df, regime: Dict) -> Tuple[bool, str]:
        """
        Enhanced trade filtering based on market conditions
        Complements intelligent_filter with regime-specific rules
        """

        # Check volume
        volume_ok, volume_reason = self.check_volume_conditions(df)
        if not volume_ok:
            return False, volume_reason

        action = signal.get('action', 'HOLD')
        if action == 'HOLD':
            return False, "No signal"

        # Regime-specific rules
        if regime['regime'] == 'ranging':
            # In ranging markets, avoid trend-following strategies
            # Only trade mean reversion (RSI extremes)
            latest = df.iloc[-1]
            rsi = latest.get('rsi', 50)

            if action == 'BUY' and rsi < 35:
                # Oversold in range = good long
                return True, "Range bounce from oversold"
            elif action == 'SELL' and rsi > 65:
                # Overbought in range = good short
                return True, "Range bounce from overbought"
            else:
                return False, f"Ranging market - wait for extremes (RSI: {rsi:.1f})"

        elif regime['regime'] == 'trending':
            # In trending markets, only trade with the trend
            latest = df.iloc[-1]
            ema_20 = latest.get('ema_20', 0)
            ema_50 = latest.get('ema_50', 0)
            price = latest.get('close', 0)

            # Determine trend direction
            trend_up = ema_20 > ema_50
            trend_down = ema_20 < ema_50

            if action == 'BUY' and trend_up:
                return True, "Trend-following long (uptrend)"
            elif action == 'SELL' and trend_down:
                return True, "Trend-following short (downtrend)"
            else:
                trend_dir = "up" if trend_up else "down"
                return False, f"Against trend ({trend_dir}) - skip counter-trend trade"

        else:  # transitional
            # Be more selective during transitions
            confidence = signal.get('confidence', 0)
            if confidence < 0.20:  # Higher threshold
                return False, f"Transitional market - need higher confidence (got {confidence:.1%})"

            return True, "Transitional market - strong signal accepted"

    def should_close_position(self, position: Dict, current_price: float, df) -> Tuple[bool, str]:
        """
        Improved exit logic - addresses the problem that stop losses lose too much
        Implements trailing stops to protect profits
        """
        entry_price = position.get('entry_price', 0)
        side = position.get('side', 'long')
        original_sl = position.get('stop_loss', 0)
        original_tp = position.get('take_profit', 0)

        # Calculate current PnL
        if side == 'long':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price

        # TRAILING STOP: If in profit, move stop to break-even or better
        if pnl_pct > 0.01:  # 1% profit
            # Move stop to break-even + small profit
            if side == 'long':
                new_sl = entry_price * 1.003  # Lock in 0.3% profit
                if current_price <= new_sl:
                    return True, "Trailing stop hit (protecting profit)"
            else:
                new_sl = entry_price * 0.997
                if current_price >= new_sl:
                    return True, "Trailing stop hit (protecting profit)"

        # Check original stops
        if side == 'long':
            if current_price <= original_sl:
                return True, "Stop loss hit"
            if current_price >= original_tp:
                return True, "Take profit hit"
        else:
            if current_price >= original_sl:
                return True, "Stop loss hit"
            if current_price <= original_tp:
                return True, "Take profit hit"

        # Time-based exit: if trade is open too long without profit
        entry_time = position.get('entry_time')
        if entry_time:
            # Convert string to datetime if needed
            if isinstance(entry_time, str):
                try:
                    entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                except:
                    entry_time = datetime.now() - timedelta(hours=1)

            time_in_trade = (datetime.now() - entry_time).total_seconds() / 60  # minutes

            # If in trade > 30 min and losing, exit
            if time_in_trade > 30 and pnl_pct < -0.003:  # -0.3%
                return True, f"Time stop: {time_in_trade:.0f}min in losing trade"

        return False, "Position OK"

    def record_trade_result(self, pnl: float):
        """Track recent performance for adaptive behavior"""
        self.recent_trades.append({
            'pnl': pnl,
            'timestamp': datetime.now()
        })

        # Keep only recent trades
        if len(self.recent_trades) > self.max_recent_trades:
            self.recent_trades.pop(0)

    def get_recent_win_rate(self) -> float:
        """Calculate recent win rate for adaptation"""
        if not self.recent_trades:
            return 0.5

        wins = sum(1 for t in self.recent_trades if t['pnl'] > 0)
        return wins / len(self.recent_trades)
