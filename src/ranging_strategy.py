"""
Ranging Market Strategy - Optimized for sideways/choppy markets
Trades mean reversion instead of trend following
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class RangingStrategy:
    """
    Strategy optimized for ranging/choppy markets where trend following fails

    Key principles:
    1. Trade mean reversion (price returns to average)
    2. Use Bollinger Bands for entry/exit instead of fixed %
    3. Quick profits (2-3%) instead of letting it run
    4. Tight time stops (exit if no movement in 1-2h)
    """

    def __init__(self, config: dict):
        self.config = config

        # Bollinger Bands settings
        self.bb_period = 20  # 20-period moving average
        self.bb_std = 2.0    # 2 standard deviations

        # Mean reversion settings
        self.rsi_oversold = 30   # RSI < 30 = oversold (buy opportunity)
        self.rsi_overbought = 70 # RSI > 70 = overbought (sell opportunity)

        # Quick profit targets for ranging
        self.target_profit_pct = 2.0  # Target 2% profit (quick in/out)
        self.max_hold_minutes = 120   # Exit if no profit in 2h

        logger.info("🔄 Ranging Strategy initialized - Mean reversion mode")

    def analyze_market_regime(self, df: pd.DataFrame) -> str:
        """
        Determine if market is trending or ranging

        Returns:
            'trending', 'ranging', or 'choppy'
        """
        if len(df) < 50:
            return 'unknown'

        # ADX (Average Directional Index) - measures trend strength
        # Simple approximation: compare recent highs/lows range
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        range_pct = (recent_high - recent_low) / recent_low * 100

        # Price vs MA deviation
        close = df['close'].values
        ma_20 = np.mean(close[-20:])
        current = close[-1]
        deviation = abs(current - ma_20) / ma_20 * 100

        if deviation > 3.0 and range_pct > 5.0:
            return 'trending'
        elif range_pct < 2.0:
            return 'choppy'  # Very tight range
        else:
            return 'ranging'  # Normal oscillation

    def calculate_bollinger_bands(self, df: pd.DataFrame) -> Dict:
        """
        Calculate Bollinger Bands for entry/exit signals

        Returns:
            Dict with upper, middle, lower bands and current position
        """
        if len(df) < self.bb_period:
            return None

        closes = df['close'].values

        # Middle band = SMA
        middle = np.mean(closes[-self.bb_period:])

        # Standard deviation
        std = np.std(closes[-self.bb_period:])

        # Upper/Lower bands
        upper = middle + (self.bb_std * std)
        lower = middle - (self.bb_std * std)

        current = closes[-1]

        # Position in bands (0-100%)
        if upper > lower:
            position_pct = (current - lower) / (upper - lower) * 100
        else:
            position_pct = 50

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'current': current,
            'position_pct': position_pct,
            'std': std,
            'bandwidth': (upper - lower) / middle * 100  # Band width in %
        }

    def should_enter_long(self, df: pd.DataFrame, indicators: Dict) -> Tuple[bool, str, float]:
        """
        Ranging strategy LONG entry:
        - Price near lower Bollinger Band (oversold)
        - RSI oversold
        - Expecting bounce back to mean

        Returns:
            (should_enter, reason, confidence_score)
        """
        bb = self.calculate_bollinger_bands(df)
        if not bb:
            return False, "Insufficient data for Bollinger Bands", 0

        rsi = indicators.get('rsi', 50)
        current_price = bb['current']

        score = 0
        reasons = []

        # 1. Price position in Bollinger Bands (40 points max)
        # LEARNING MODE: Relaxed thresholds to generate 5-10 trades/day
        if bb['position_pct'] < 20:  # Near lower band (relaxed from 15%)
            score += 40
            reasons.append(f"Near lower BB ({bb['position_pct']:.0f}% position)")
        elif bb['position_pct'] < 35:  # Below middle (relaxed from 30%)
            score += 25
            reasons.append(f"Below middle BB ({bb['position_pct']:.0f}% position)")
        elif bb['position_pct'] < 45:  # Lower half (NEW - for learning)
            score += 15
            reasons.append(f"Lower half BB ({bb['position_pct']:.0f}% position)")
        else:
            return False, f"Not oversold (BB position: {bb['position_pct']:.0f}%)", 0

        # 2. RSI confirmation (30 points max)
        if rsi < 30:
            score += 30
            reasons.append(f"RSI oversold ({rsi:.0f})")
        elif rsi < 40:
            score += 20
            reasons.append(f"RSI low ({rsi:.0f})")
        elif rsi < 50:
            score += 10
            reasons.append(f"RSI neutral-low ({rsi:.0f})")

        # 3. Band width (volatility check) (20 points max)
        if bb['bandwidth'] > 3.0:  # Wide bands = good volatility for bounce
            score += 20
            reasons.append(f"Good volatility (BW: {bb['bandwidth']:.1f}%)")
        elif bb['bandwidth'] > 1.5:
            score += 10
            reasons.append(f"Moderate volatility (BW: {bb['bandwidth']:.1f}%)")

        # 4. Volume confirmation (10 points)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 1.2:
            score += 10
            reasons.append("Above avg volume")

        reason = " | ".join(reasons)
        confidence = score / 100  # Convert to 0-1

        # LEARNING MODE: Lower threshold to generate more trades for learning
        should_enter = score >= 35  # Lowered from 50 to increase trade volume

        if should_enter:
            logger.info(f"📈 RANGING LONG signal: {reason} (score: {score}/100)")

        return should_enter, reason, confidence

    def should_enter_short(self, df: pd.DataFrame, indicators: Dict) -> Tuple[bool, str, float]:
        """
        Ranging strategy SHORT entry:
        - Price near upper Bollinger Band (overbought)
        - RSI overbought
        - Expecting pullback to mean

        Returns:
            (should_enter, reason, confidence_score)
        """
        bb = self.calculate_bollinger_bands(df)
        if not bb:
            return False, "Insufficient data for Bollinger Bands", 0

        rsi = indicators.get('rsi', 50)
        current_price = bb['current']

        score = 0
        reasons = []

        # 1. Price position in Bollinger Bands (40 points max)
        # LEARNING MODE: Relaxed thresholds to generate 5-10 trades/day
        if bb['position_pct'] > 80:  # Near upper band (relaxed from 85%)
            score += 40
            reasons.append(f"Near upper BB ({bb['position_pct']:.0f}% position)")
        elif bb['position_pct'] > 65:  # Above middle (relaxed from 70%)
            score += 25
            reasons.append(f"Above middle BB ({bb['position_pct']:.0f}% position)")
        elif bb['position_pct'] > 55:  # Upper half (NEW - for learning)
            score += 15
            reasons.append(f"Upper half BB ({bb['position_pct']:.0f}% position)")
        else:
            return False, f"Not overbought (BB position: {bb['position_pct']:.0f}%)", 0

        # 2. RSI confirmation (30 points max)
        if rsi > 70:
            score += 30
            reasons.append(f"RSI overbought ({rsi:.0f})")
        elif rsi > 60:
            score += 20
            reasons.append(f"RSI high ({rsi:.0f})")
        elif rsi > 50:
            score += 10
            reasons.append(f"RSI neutral-high ({rsi:.0f})")

        # 3. Band width (volatility check) (20 points max)
        if bb['bandwidth'] > 3.0:
            score += 20
            reasons.append(f"Good volatility (BW: {bb['bandwidth']:.1f}%)")
        elif bb['bandwidth'] > 1.5:
            score += 10
            reasons.append(f"Moderate volatility (BW: {bb['bandwidth']:.1f}%)")

        # 4. Volume confirmation (10 points)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 1.2:
            score += 10
            reasons.append("Above avg volume")

        reason = " | ".join(reasons)
        confidence = score / 100

        # LEARNING MODE: Lower threshold to generate more trades for learning
        should_enter = score >= 35  # Lowered from 50 to increase trade volume

        if should_enter:
            logger.info(f"📉 RANGING SHORT signal: {reason} (score: {score}/100)")

        return should_enter, reason, confidence

    def calculate_ranging_stops(self, df: pd.DataFrame, side: str, entry_price: float) -> Tuple[float, float]:
        """
        Calculate stops for ranging strategy using Bollinger Bands

        For LONG:
        - Stop: Below lower Bollinger Band (bounce failed)
        - Target: Middle or upper BB (mean reversion complete)

        For SHORT:
        - Stop: Above upper Bollinger Band (pullback failed)
        - Target: Middle or lower BB

        Returns:
            (stop_loss, take_profit)
        """
        bb = self.calculate_bollinger_bands(df)

        if not bb:
            # Fallback to percentage-based
            if side == 'long':
                stop_loss = entry_price * 0.975  # -2.5%
                take_profit = entry_price * 1.020  # +2%
            else:
                stop_loss = entry_price * 1.025  # +2.5%
                take_profit = entry_price * 0.980  # -2%
            return stop_loss, take_profit

        if side == 'long':
            # Stop: Slightly below lower BB (bounce failed)
            stop_loss = bb['lower'] * 0.995

            # Target: Middle BB (conservative) or 2% profit
            target_middle = bb['middle']
            target_pct = entry_price * 1.020
            take_profit = min(target_middle, target_pct)  # Whichever is closer

            # Ensure minimum R:R of 1.5:1
            risk = entry_price - stop_loss
            if (take_profit - entry_price) < risk * 1.5:
                take_profit = entry_price + (risk * 1.5)

        else:  # short
            # Stop: Slightly above upper BB
            stop_loss = bb['upper'] * 1.005

            # Target: Middle BB or 2% profit
            target_middle = bb['middle']
            target_pct = entry_price * 0.980
            take_profit = max(target_middle, target_pct)

            # Ensure minimum R:R
            risk = stop_loss - entry_price
            if (entry_price - take_profit) < risk * 1.5:
                take_profit = entry_price - (risk * 1.5)

        # Log the setup
        risk_pct = abs(entry_price - stop_loss) / entry_price * 100
        reward_pct = abs(take_profit - entry_price) / entry_price * 100
        rr_ratio = reward_pct / risk_pct if risk_pct > 0 else 0

        logger.info(f"🎯 RANGING STOPS: SL={risk_pct:.2f}%, TP={reward_pct:.2f}%, R:R={rr_ratio:.1f}:1 (BB-based)")

        return stop_loss, take_profit

    def should_exit_early(self, position: Dict, current_price: float, entry_time) -> Tuple[bool, str]:
        """
        Check if position should exit early due to ranging strategy rules

        Returns:
            (should_exit, reason)
        """
        from datetime import datetime

        # Time-based exit (no movement in 2h)
        if entry_time:
            duration_minutes = (datetime.now() - entry_time).total_seconds() / 60
            if duration_minutes > self.max_hold_minutes:
                return True, f"Time stop: {duration_minutes:.0f}min > {self.max_hold_minutes}min (no movement)"

        # Could add more early exit logic here
        # e.g., if price crosses middle BB in wrong direction

        return False, ""


if __name__ == "__main__":
    # Test the strategy
    print("Ranging Strategy - Mean Reversion for sideways markets")
    print("Key features:")
    print("  - Trades bounces at Bollinger Band extremes")
    print("  - Uses RSI for confirmation")
    print("  - Quick 2% targets instead of trend-following")
    print("  - Time stops at 2h (no endless holds)")
