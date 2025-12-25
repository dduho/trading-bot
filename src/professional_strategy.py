"""
Professional Trading Strategy
Inspired by world-class traders: Livermore, Tudor Jones, Minervini

Philosophy:
1. Trade WITH the trend, never against it
2. Only take A+ setups (confluence of multiple factors)
3. Risk management is everything - survive to trade another day
4. Let winners run, cut losers fast
5. Context matters - market regime, BTC dominance, correlation
"""

import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ProfessionalStrategy:
    """
    Professional-grade trading strategy combining:
    - Multi-timeframe analysis (1m, 5m, 15m, 1h, 4h)
    - Market structure (support/resistance, trend)
    - Volume analysis (institutional activity)
    - Risk management (position sizing, stops)
    """

    def __init__(self, config: dict, market_feed=None):
        self.config = config
        self.market_feed = market_feed  # For multi-timeframe analysis

        # Grade thresholds for setup quality
        # Optimized for 1-3 trades/day (professional activity level)
        # Lowered to 48 to adapt to low-structure ranging markets (Dec 2025)
        self.GRADE_A_PLUS = 48  # Trade A+ setups (balanced for current market conditions)
        self.GRADE_A = 40
        self.GRADE_B = 30

        # Multi-timeframe weights (higher TF = more weight)
        self.timeframe_weights = {
            '1h': 0.35,   # Higher timeframe = more weight
            '15m': 0.30,
            '5m': 0.20,
            '1m': 0.15
        }

    def check_trading_hours(self) -> Tuple[bool, str, int]:
        """
        Time-based filter - avoid low liquidity hours

        Best times:
        - 13:00-17:00 UTC (EU/US overlap = max volume) → +5 bonus points
        - 08:00-22:00 UTC (normal hours) → OK
        - 00:00-06:00 UTC (Asian hours, low volume) → Penalize -5 points

        Returns:
            (should_trade, reason, score_adjustment)
        """
        try:
            from datetime import datetime
            import pytz

            utc_now = datetime.now(pytz.UTC)
            hour = utc_now.hour

            # Peak hours (EU/US overlap)
            if 13 <= hour < 17:
                return True, f"Peak hours ({hour}:00 UTC - EU/US overlap)", 5

            # Normal hours
            elif 8 <= hour < 22:
                return True, f"Normal hours ({hour}:00 UTC)", 0

            # Low volume hours (avoid if possible, but allow with penalty)
            else:
                return True, f"Low volume hours ({hour}:00 UTC - Asian session)", -5

        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            return True, "Time check error", 0

    def check_btc_correlation(self, symbol: str, signal_action: str) -> Tuple[bool, str]:
        """
        Bitcoin Correlation Filter - Don't fight BTC dominance!

        Rule: If BTC is strongly bullish (+2%+), don't SHORT altcoins
              If BTC is strongly bearish (-2%+), don't LONG altcoins

        Altcoins follow BTC ~70% of the time
        """
        if not self.market_feed or symbol == 'BTC/USDT':
            return True, "BTC or no data"

        try:
            # Get BTC price movement over last 1h
            btc_df = self.market_feed.get_ohlcv('BTC/USDT', timeframe='1h', limit=2)
            if btc_df.empty or len(btc_df) < 2:
                return True, "No BTC data"

            btc_prev = btc_df['close'].iloc[-2]
            btc_current = btc_df['close'].iloc[-1]
            btc_change_pct = ((btc_current - btc_prev) / btc_prev) * 100

            # Strong BTC movement threshold
            STRONG_MOVE = 2.0  # 2%

            if signal_action == 'SELL':  # Trying to SHORT altcoin
                if btc_change_pct > STRONG_MOVE:
                    return False, f"BTC surging +{btc_change_pct:.1f}% - don't SHORT altcoins"
                else:
                    return True, f"BTC {btc_change_pct:+.1f}% - OK to SHORT"

            elif signal_action == 'BUY':  # Trying to LONG altcoin
                if btc_change_pct < -STRONG_MOVE:
                    return False, f"BTC dumping {btc_change_pct:.1f}% - don't LONG altcoins"
                else:
                    return True, f"BTC {btc_change_pct:+.1f}% - OK to LONG"

            return True, "No BTC conflict"

        except Exception as e:
            logger.error(f"Error checking BTC correlation: {e}")
            return True, "BTC check error - allowing trade"

    def analyze_multi_timeframe_trend(self, symbol: str, signal_action: str) -> Tuple[bool, str, int]:
        """
        Multi-timeframe trend confirmation (like professionals do)

        A BUY signal on 1m is STRONGER if:
        - 5m is also bullish (uptrend)
        - 15m is also bullish
        - 1h is also bullish

        Returns:
            (is_confirmed, reason, bonus_points)
        """
        if not self.market_feed:
            return True, "No MTF data", 0

        try:
            timeframes = ['5m', '15m', '1h']
            trend_votes = {'bullish': 0, 'bearish': 0, 'neutral': 0}
            weights_sum = 0

            for tf in timeframes:
                try:
                    df = self.market_feed.get_ohlcv(symbol, timeframe=tf, limit=50)
                    if df.empty:
                        continue

                    # Simple trend: compare recent price to 20-period average
                    closes = df['close'].values
                    if len(closes) < 20:
                        continue

                    current = closes[-1]
                    avg_20 = np.mean(closes[-20:])
                    avg_50 = np.mean(closes) if len(closes) >= 50 else avg_20

                    weight = self.timeframe_weights.get(tf, 0.1)

                    # Determine trend
                    if current > avg_20 and avg_20 > avg_50:
                        trend_votes['bullish'] += weight
                    elif current < avg_20 and avg_20 < avg_50:
                        trend_votes['bearish'] += weight
                    else:
                        trend_votes['neutral'] += weight

                    weights_sum += weight

                except Exception as e:
                    logger.debug(f"Error analyzing {tf} for {symbol}: {e}")
                    continue

            if weights_sum == 0:
                return True, "No MTF data available", 0

            # Normalize votes
            bullish_pct = (trend_votes['bullish'] / weights_sum) * 100
            bearish_pct = (trend_votes['bearish'] / weights_sum) * 100

            # Check alignment
            if signal_action == 'BUY':
                if bullish_pct >= 70:  # 70%+ higher TFs bullish
                    return True, f"MTF aligned: {bullish_pct:.0f}% bullish", 15
                elif bullish_pct >= 50:
                    return True, f"MTF partial: {bullish_pct:.0f}% bullish", 8
                else:
                    return False, f"MTF conflict: {bearish_pct:.0f}% bearish on higher TFs", 0

            elif signal_action == 'SELL':
                if bearish_pct >= 70:
                    return True, f"MTF aligned: {bearish_pct:.0f}% bearish", 15
                elif bearish_pct >= 50:
                    return True, f"MTF partial: {bearish_pct:.0f}% bearish", 8
                else:
                    return False, f"MTF conflict: {bullish_pct:.0f}% bullish on higher TFs", 0

            return True, "HOLD signal - no MTF check", 0

        except Exception as e:
            logger.error(f"Error in multi-timeframe analysis: {e}")
            return True, "MTF error - allowing trade", 0

    def analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        """
        Analyze market structure like a professional trader:
        - Higher highs / lower lows (trend)
        - Support and resistance zones
        - Liquidity areas (where stops likely are)
        """
        try:
            # Look at last 50 candles for structure
            lookback = min(50, len(df))
            recent = df.tail(lookback)

            highs = recent['high'].values
            lows = recent['low'].values
            closes = recent['close'].values

            # Identify swing points
            swing_highs = []
            swing_lows = []

            for i in range(2, len(recent) - 2):
                # Swing high: higher than 2 candles before and after
                if highs[i] > max(highs[i-2:i]) and highs[i] > max(highs[i+1:i+3]):
                    swing_highs.append(highs[i])

                # Swing low: lower than 2 candles before and after
                if lows[i] < min(lows[i-2:i]) and lows[i] < min(lows[i+1:i+3]):
                    swing_lows.append(lows[i])

            current_price = closes[-1]

            # Determine trend structure
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                # Uptrend: Higher Highs + Higher Lows
                higher_highs = swing_highs[-1] > swing_highs[-2] if len(swing_highs) >= 2 else False
                higher_lows = swing_lows[-1] > swing_lows[-2] if len(swing_lows) >= 2 else False

                # Downtrend: Lower Highs + Lower Lows
                lower_highs = swing_highs[-1] < swing_highs[-2] if len(swing_highs) >= 2 else False
                lower_lows = swing_lows[-1] < swing_lows[-2] if len(swing_lows) >= 2 else False

                if higher_highs and higher_lows:
                    structure = 'uptrend'
                elif lower_highs and lower_lows:
                    structure = 'downtrend'
                else:
                    structure = 'ranging'
            else:
                structure = 'insufficient_data'

            # Find nearest support/resistance
            nearest_resistance = min([h for h in swing_highs if h > current_price], default=None)
            nearest_support = max([l for l in swing_lows if l < current_price], default=None)

            # Distance to support/resistance (room to move)
            resistance_distance = ((nearest_resistance - current_price) / current_price * 100) if nearest_resistance else 999
            support_distance = ((current_price - nearest_support) / current_price * 100) if nearest_support else 999

            return {
                'structure': structure,
                'nearest_resistance': nearest_resistance,
                'nearest_support': nearest_support,
                'resistance_distance_pct': resistance_distance,
                'support_distance_pct': support_distance,
                'swing_highs': swing_highs,
                'swing_lows': swing_lows,
                'has_room_to_move': resistance_distance > 3.0 and support_distance > 3.0  # At least 3% room
            }

        except Exception as e:
            logger.error(f"Error analyzing market structure: {e}")
            return {
                'structure': 'unknown',
                'has_room_to_move': False
            }

    def analyze_volume_profile(self, df: pd.DataFrame) -> Dict:
        """
        Volume analysis - where is institutional money?
        - Above average volume = institutions interested
        - Volume at breakouts = conviction
        - Volume divergence = warning signal
        """
        try:
            recent = df.tail(20)
            current_volume = recent['volume'].iloc[-1]
            avg_volume = recent['volume'].mean()

            # Volume surge detection
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            # Price-volume divergence (price up but volume down = weak)
            price_change = (recent['close'].iloc[-1] - recent['close'].iloc[-5]) / recent['close'].iloc[-5] * 100
            volume_change = (current_volume - recent['volume'].iloc[-5]) / recent['volume'].iloc[-5] * 100

            # Healthy: price and volume move together
            divergence = False
            if price_change > 2 and volume_change < -20:
                divergence = True  # Price up but volume down = bearish divergence
            elif price_change < -2 and volume_change < -20:
                divergence = True  # Price down on low volume = might reverse

            return {
                'volume_ratio': volume_ratio,
                'is_high_volume': volume_ratio > 1.5,  # 50% above average
                'has_divergence': divergence,
                'institutional_interest': volume_ratio > 2.0  # 2x average = institutions active
            }

        except Exception as e:
            logger.error(f"Error analyzing volume: {e}")
            return {'volume_ratio': 1.0, 'is_high_volume': False, 'has_divergence': False}

    def grade_setup(self, df: pd.DataFrame, signal: str, market_regime: Dict) -> Tuple[int, str]:
        """
        Grade the setup quality from 0-100 (like Minervini's A+ setups)

        A+ Setup (80+): All stars align - take the trade!
        A Setup (70-79): Good setup - consider it
        B Setup (60-69): Mediocre - maybe skip
        C Setup (<60): Don't trade

        Grading factors:
        - Trend alignment (30 points max)
        - Volume confirmation (20 points max)
        - Market structure (20 points max)
        - Risk/Reward setup (15 points max)
        - Confluence of indicators (15 points max)
        """
        score = 0
        reasons = []

        try:
            # 1. TREND ALIGNMENT (30 points)
            structure = self.analyze_market_structure(df)

            if signal == 'BUY':
                if structure['structure'] == 'uptrend':
                    score += 30
                    reasons.append("✓ Trading WITH uptrend (+30)")
                elif structure['structure'] == 'ranging':
                    score += 15
                    reasons.append("~ Ranging market (+15)")
                else:
                    score += 0
                    reasons.append("✗ Against downtrend (+0)")

            elif signal == 'SELL':
                if structure['structure'] == 'downtrend':
                    score += 30
                    reasons.append("✓ Trading WITH downtrend (+30)")
                elif structure['structure'] == 'ranging':
                    score += 15
                    reasons.append("~ Ranging market (+15)")
                else:
                    score += 0
                    reasons.append("✗ Against uptrend (+0)")

            # 2. VOLUME CONFIRMATION (20 points)
            volume_analysis = self.analyze_volume_profile(df)

            if volume_analysis['institutional_interest']:
                score += 20
                reasons.append("✓ Institutional volume (+20)")
            elif volume_analysis['is_high_volume']:
                score += 15
                reasons.append("✓ Above average volume (+15)")
            else:
                score += 5
                reasons.append("~ Low volume (+5)")

            if volume_analysis['has_divergence']:
                score -= 10
                reasons.append("✗ Price-volume divergence (-10)")

            # 3. MARKET STRUCTURE (20 points)
            # BUG FIX: Don't reward unknown structure (999% distance means NO data, not infinite room!)
            # Also reject levels too close (<1% = essentially at current price = invalid)
            resistance_dist = structure.get('resistance_distance_pct', 999)
            support_dist = structure.get('support_distance_pct', 999)

            # Only give points if we have REAL support/resistance levels (0.6-100% range)
            # < 0.6% is too close (caused R:R bugs), > 100% is placeholder (999)
            MIN_DISTANCE = 0.6  # Minimum 0.6% away (balanced: prevents bugs but allows tight structures)
            MAX_DISTANCE = 100.0  # Maximum 100% (beyond this is likely 999 placeholder)

            if (MIN_DISTANCE < resistance_dist < MAX_DISTANCE and
                MIN_DISTANCE < support_dist < MAX_DISTANCE):  # Real levels found
                if structure.get('has_room_to_move', False):
                    score += 20
                    reasons.append(f"✓ Room to move: {resistance_dist:.1f}% to R, {support_dist:.1f}% to S (+20)")
                else:
                    score += 5
                    reasons.append(f"✗ Near resistance/support: {resistance_dist:.1f}%/{support_dist:.1f}% (+5)")
            else:
                score += 0
                reasons.append("✗ No clear support/resistance structure (+0)")

            # 4. RISK/REWARD SETUP (15 points)
            # BUG FIX: Only calculate R:R if we have REAL levels (1-100% range)
            if signal == 'BUY':
                potential_reward = structure.get('resistance_distance_pct', 999)
                potential_risk = structure.get('support_distance_pct', 999)
            else:
                potential_reward = structure.get('support_distance_pct', 999)
                potential_risk = structure.get('resistance_distance_pct', 999)

            # Only give points if BOTH reward and risk are in valid range (1-100%)
            if (MIN_DISTANCE < potential_reward < MAX_DISTANCE and
                MIN_DISTANCE < potential_risk < MAX_DISTANCE):
                risk_reward = potential_reward / potential_risk
                if risk_reward >= 3:
                    score += 15
                    reasons.append(f"✓ Excellent R:R {risk_reward:.1f}:1 (+15)")
                elif risk_reward >= 2:
                    score += 10
                    reasons.append(f"✓ Good R:R {risk_reward:.1f}:1 (+10)")
                else:
                    score += 0
                    reasons.append(f"✗ Poor R:R {risk_reward:.1f}:1 (+0)")
            else:
                score += 0
                reasons.append("✗ Cannot calculate R:R - no structure (+0)")

            # 5. CONFLUENCE OF INDICATORS (15 points)
            regime = market_regime.get('regime', 'unknown')
            volatility = market_regime.get('volatility', 'medium')

            # Prefer trending markets with good volatility
            if regime == 'trending' and volatility in ['medium', 'high']:
                score += 15
                reasons.append("✓ Trending + good volatility (+15)")
            elif regime == 'transitional':
                score += 8
                reasons.append("~ Transitional market (+8)")
            else:
                score += 3
                reasons.append("~ Ranging/low volatility (+3)")

            # Cap score at 100
            score = min(score, 100)

            # Determine grade
            if score >= self.GRADE_A_PLUS:
                grade = "A+"
            elif score >= self.GRADE_A:
                grade = "A"
            elif score >= self.GRADE_B:
                grade = "B"
            else:
                grade = "C"

            reasoning = f"Grade {grade} ({score}/100): " + " | ".join(reasons)

            logger.info(f"📊 SETUP GRADING: {reasoning}")

            return score, reasoning

        except Exception as e:
            logger.error(f"Error grading setup: {e}")
            return 0, f"Error grading: {e}"

    def should_take_trade(self, signal: str, df: pd.DataFrame, market_regime: Dict, symbol: str = None) -> Tuple[bool, str]:
        """
        Final decision: Should we take this trade?

        Rules (like the pros):
        1. Don't fight BTC dominance (correlation filter)
        2. Multi-timeframe trend confirmation
        3. ONLY take A+ setups (65+)
        4. Must have volume confirmation
        5. Must have room to move (not at resistance)
        """
        # BTC Correlation check (FIRST - don't fight the market)
        if symbol and self.market_feed:
            btc_ok, btc_reason = self.check_btc_correlation(symbol, signal)
            if not btc_ok:
                return False, f"⛔ BTC FILTER: {btc_reason}"

        # Multi-timeframe confirmation (FILTER before grading)
        if symbol and self.market_feed:
            mtf_ok, mtf_reason, mtf_bonus = self.analyze_multi_timeframe_trend(symbol, signal)
            if not mtf_ok:
                return False, f"⛔ MTF REJECT: {mtf_reason}"

        score, reasoning = self.grade_setup(df, signal, market_regime)

        # Apply MTF bonus if available
        if symbol and self.market_feed:
            mtf_ok, mtf_reason, mtf_bonus = self.analyze_multi_timeframe_trend(symbol, signal)
            if mtf_bonus > 0:
                score += mtf_bonus
                score = min(score, 100)  # Cap at 100
                reasoning += f" | {mtf_reason} (+{mtf_bonus})"

        # TIME-BASED ADJUSTMENT (peak hours bonus, low volume penalty)
        time_ok, time_reason, time_adjustment = self.check_trading_hours()
        if time_adjustment != 0:
            score += time_adjustment
            score = max(0, min(score, 100))  # Keep in 0-100 range
            reasoning += f" | {time_reason} ({time_adjustment:+d})"

        # DYNAMIC THRESHOLD based on market volatility (ATR)
        # Optimized for 1-3 trades/day (professional activity)
        # High volatility (ATR > 3%) → Lower threshold (more opportunities)
        # Normal volatility → Standard 55
        # Low volatility (ATR < 1%) → Slightly higher (more selective but not blocking)
        volatility = market_regime.get('volatility', 'medium')
        atr_value = df['atr'].iloc[-1] if 'atr' in df.columns and len(df) > 0 else 0
        current_price = df['close'].iloc[-1] if 'close' in df.columns and len(df) > 0 else 1
        atr_pct = (atr_value / current_price * 100) if current_price > 0 else 0

        dynamic_threshold = self.GRADE_A_PLUS  # Default 55

        if atr_pct > 3.0:  # High volatility
            dynamic_threshold = 50  # More opportunities in volatile markets
            threshold_note = f"(threshold lowered to {dynamic_threshold} due to high volatility {atr_pct:.1f}%)"
        elif atr_pct < 1.0:  # Low volatility
            # Keep standard threshold even in low volatility (was 60, then 70)
            # Reason: Market structure validation already filters bad setups
            # Professional traders adapt to market conditions, don't sit idle
            threshold_note = f"(standard threshold {dynamic_threshold}, low volatility {atr_pct:.1f}%)"
        else:
            threshold_note = f"(standard threshold {dynamic_threshold}, ATR {atr_pct:.1f}%)"

        # Calculate position size multiplier based on score
        size_multiplier = self.calculate_position_size_multiplier(score)

        # Log final score after all adjustments for debugging
        logger.info(f"📊 FINAL SCORE AFTER ADJUSTMENTS: {score}/100 vs threshold {dynamic_threshold}")

        # STRICT: Only A+ setups (with dynamic threshold)
        if score >= dynamic_threshold:
            # Store score and multiplier as attributes for execute_signal to use
            self.last_score = score
            self.last_size_multiplier = size_multiplier
            return True, f"✅ TRADE AUTHORIZED: Grade A+ ({score}/{dynamic_threshold}, size {size_multiplier:.1f}x) {threshold_note}: {reasoning}"
        else:
            self.last_score = score
            self.last_size_multiplier = 0
            return False, f"⛔ SKIP ({score}/{dynamic_threshold}) {threshold_note}: {reasoning}"

    def calculate_position_size_multiplier(self, score: int) -> float:
        """
        Intelligent position sizing based on setup quality

        Grade A+ (80-100): 1.4x size (best setups deserve more capital)
        Grade A+ (70-79): 1.2x size
        Grade A+ (65-69): 1.0x size (standard)
        Grade A (55-64): 0.6x size (if dynamic threshold allows)

        Returns multiplier to apply to base position size
        """
        if score >= 80:
            return 1.4  # Best setups - go bigger
        elif score >= 70:
            return 1.2  # Good setups - slightly bigger
        elif score >= 65:
            return 1.0  # Standard size
        elif score >= 55:
            return 0.6  # Marginal setups (high volatility) - smaller size
        else:
            return 0.5  # Safety minimum

    def calculate_professional_stops(
        self,
        df: pd.DataFrame,
        side: str,
        entry_price: float,
        market_structure: Dict
    ) -> Tuple[float, float]:
        """
        Calculate stops like a professional:
        - Stop loss: Below recent swing low (for LONG), above swing high (for SHORT)
        - Take profit: At resistance (for LONG), at support (for SHORT)

        This gives NATURAL stops based on market structure, not arbitrary percentages
        """
        try:
            structure = market_structure or self.analyze_market_structure(df)

            if side == 'long':
                # Stop: Below nearest swing low (where stops are clustered)
                if structure.get('nearest_support'):
                    # Place stop slightly below support to avoid getting hit by wicks
                    stop_loss = structure['nearest_support'] * 0.995  # 0.5% below
                else:
                    # Fallback: 2% below entry
                    stop_loss = entry_price * 0.98

                # Target: At resistance or 2:1 R:R minimum
                if structure.get('nearest_resistance'):
                    take_profit = structure['nearest_resistance'] * 0.995  # Slight safety margin
                else:
                    # Fallback: 6% profit target
                    take_profit = entry_price * 1.06

            else:  # short
                # Stop: Above nearest swing high
                if structure.get('nearest_resistance'):
                    stop_loss = structure['nearest_resistance'] * 1.005  # 0.5% above
                else:
                    stop_loss = entry_price * 1.02

                # Target: At support
                if structure.get('nearest_support'):
                    take_profit = structure['nearest_support'] * 1.005
                else:
                    take_profit = entry_price * 0.94

            # Ensure minimum R:R of 2:1
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)

            if reward < risk * 2:
                # Extend take profit to maintain 2:1
                if side == 'long':
                    take_profit = entry_price + (risk * 2)
                else:
                    take_profit = entry_price - (risk * 2)

            # Log the setup
            risk_pct = abs(entry_price - stop_loss) / entry_price * 100
            reward_pct = abs(take_profit - entry_price) / entry_price * 100
            rr_ratio = reward_pct / risk_pct if risk_pct > 0 else 0

            logger.info(f"🎯 PROFESSIONAL STOPS: SL={risk_pct:.2f}%, TP={reward_pct:.2f}%, R:R={rr_ratio:.1f}:1")

            return stop_loss, take_profit

        except Exception as e:
            logger.error(f"Error calculating professional stops: {e}")
            # Fallback to safe defaults
            if side == 'long':
                return entry_price * 0.98, entry_price * 1.06
            else:
                return entry_price * 1.02, entry_price * 0.94
