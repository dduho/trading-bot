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

    def __init__(self, config: dict):
        self.config = config

        # Grade thresholds for setup quality
        # Lowered from 80 to 65 to allow more quality trades (fresh DB needs building data)
        self.GRADE_A_PLUS = 65  # Trade A+ setups
        self.GRADE_A = 55
        self.GRADE_B = 45

        # Multi-timeframe weights
        self.timeframe_weights = {
            '1h': 0.35,   # Higher timeframe = more weight
            '15m': 0.30,
            '5m': 0.20,
            '1m': 0.15
        }

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
            if structure.get('has_room_to_move', False):
                score += 20
                reasons.append(f"✓ Room to move: {structure.get('resistance_distance_pct', 0):.1f}% to resistance (+20)")
            else:
                score += 5
                reasons.append("✗ Near resistance/support (+5)")

            # 4. RISK/REWARD SETUP (15 points)
            # Check if we have good R:R based on structure
            if signal == 'BUY':
                potential_reward = structure.get('resistance_distance_pct', 0)
                potential_risk = structure.get('support_distance_pct', 3)
            else:
                potential_reward = structure.get('support_distance_pct', 0)
                potential_risk = structure.get('resistance_distance_pct', 3)

            risk_reward = potential_reward / potential_risk if potential_risk > 0 else 0

            if risk_reward >= 3:
                score += 15
                reasons.append(f"✓ Excellent R:R {risk_reward:.1f}:1 (+15)")
            elif risk_reward >= 2:
                score += 10
                reasons.append(f"✓ Good R:R {risk_reward:.1f}:1 (+10)")
            else:
                score += 0
                reasons.append(f"✗ Poor R:R {risk_reward:.1f}:1 (+0)")

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

    def should_take_trade(self, signal: str, df: pd.DataFrame, market_regime: Dict) -> Tuple[bool, str]:
        """
        Final decision: Should we take this trade?

        Rules (like the pros):
        1. ONLY take A+ setups (80+)
        2. Never trade against major trend
        3. Must have volume confirmation
        4. Must have room to move (not at resistance)
        """
        score, reasoning = self.grade_setup(df, signal, market_regime)

        # STRICT: Only A+ setups
        if score >= self.GRADE_A_PLUS:
            return True, f"✅ TRADE: {reasoning}"
        else:
            return False, f"⛔ SKIP: {reasoning}"

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
