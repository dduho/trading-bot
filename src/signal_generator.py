"""
Signal Generator Module
Generates buy/sell/hold signals based on technical analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Signal(Enum):
    """Trading signals"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class SignalGenerator:
    """Generates trading signals from technical indicators"""

    def __init__(self, config: Dict = None):
        """
        Initialize signal generator

        Args:
            config: Configuration with strategy parameters
        """
        # Fusionner la config fournie avec les valeurs par défaut
        default = self._default_config()
        if config:
            default.update(config)
            # Fusionner aussi les weights si présents
            if 'weights' in config:
                default['weights'].update(config['weights'])
        self.config = default
        self.signal_history = []

    def _default_config(self) -> Dict:
        """Default signal configuration"""
        return {
            'min_confidence': 0.6,
            'weights': {
                'rsi': 0.25,
                'macd': 0.25,
                'moving_averages': 0.25,
                'volume': 0.15,
                'trend': 0.10
            }
        }

    def analyze_rsi(self, df: pd.DataFrame) -> Dict:
        """
        Analyze RSI indicator

        Returns:
            Dict with signal, score, and reason
        """
        if df.empty or 'rsi' not in df.columns:
            return {'signal': Signal.HOLD, 'score': 0, 'reason': 'No RSI data'}

        rsi = df['rsi'].iloc[-1]

        if pd.isna(rsi):
            return {'signal': Signal.HOLD, 'score': 0, 'reason': 'Invalid RSI'}

        # RSI interpretation
        if rsi < 30:
            score = (30 - rsi) / 30  # Higher score for lower RSI
            return {
                'signal': Signal.BUY,
                'score': min(score, 1.0),
                'reason': f'RSI oversold at {rsi:.1f}'
            }
        elif rsi > 70:
            score = (rsi - 70) / 30  # Higher score for higher RSI
            return {
                'signal': Signal.SELL,
                'score': min(score, 1.0),
                'reason': f'RSI overbought at {rsi:.1f}'
            }
        else:
            # Neutral zone - slight preference based on position
            if rsi < 50:
                score = 0.3
                signal = Signal.BUY
            else:
                score = 0.3
                signal = Signal.SELL

            return {
                'signal': signal,
                'score': score,
                'reason': f'RSI neutral at {rsi:.1f}'
            }

    def analyze_macd(self, df: pd.DataFrame) -> Dict:
        """Analyze MACD indicator"""
        if df.empty or 'macd' not in df.columns:
            return {'signal': Signal.HOLD, 'score': 0, 'reason': 'No MACD data'}

        macd = df['macd'].iloc[-1]
        signal_line = df['macd_signal'].iloc[-1]
        hist = df['macd_hist'].iloc[-1]

        if pd.isna(macd) or pd.isna(signal_line):
            return {'signal': Signal.HOLD, 'score': 0, 'reason': 'Invalid MACD'}

        # MACD crossover
        if len(df) > 1:
            prev_hist = df['macd_hist'].iloc[-2]

            # Bullish crossover
            if prev_hist < 0 and hist > 0:
                return {
                    'signal': Signal.BUY,
                    'score': 0.9,
                    'reason': 'MACD bullish crossover'
                }
            # Bearish crossover
            elif prev_hist > 0 and hist < 0:
                return {
                    'signal': Signal.SELL,
                    'score': 0.9,
                    'reason': 'MACD bearish crossover'
                }

        # MACD position
        if macd > signal_line:
            score = min(abs(hist) / 10, 0.7)  # Normalize histogram
            return {
                'signal': Signal.BUY,
                'score': score,
                'reason': f'MACD bullish ({hist:.2f})'
            }
        else:
            score = min(abs(hist) / 10, 0.7)
            return {
                'signal': Signal.SELL,
                'score': score,
                'reason': f'MACD bearish ({hist:.2f})'
            }

    def analyze_moving_averages(self, df: pd.DataFrame) -> Dict:
        """Analyze moving average crossovers"""
        if df.empty or 'sma_short' not in df.columns:
            return {'signal': Signal.HOLD, 'score': 0, 'reason': 'No MA data'}

        sma_short = df['sma_short'].iloc[-1]
        sma_long = df['sma_long'].iloc[-1]

        if pd.isna(sma_short) or pd.isna(sma_long):
            return {'signal': Signal.HOLD, 'score': 0, 'reason': 'Invalid MA'}

        # Golden Cross / Death Cross
        if len(df) > 1:
            prev_short = df['sma_short'].iloc[-2]
            prev_long = df['sma_long'].iloc[-2]

            # Golden Cross (bullish)
            if prev_short < prev_long and sma_short > sma_long:
                return {
                    'signal': Signal.BUY,
                    'score': 0.95,
                    'reason': 'Golden Cross detected'
                }
            # Death Cross (bearish)
            elif prev_short > prev_long and sma_short < sma_long:
                return {
                    'signal': Signal.SELL,
                    'score': 0.95,
                    'reason': 'Death Cross detected'
                }

        # MA position
        if sma_short > sma_long:
            spread = ((sma_short - sma_long) / sma_long) * 100
            score = min(spread / 5, 0.7)  # Normalize spread
            return {
                'signal': Signal.BUY,
                'score': score,
                'reason': f'Short MA above Long MA ({spread:.2f}%)'
            }
        else:
            spread = ((sma_long - sma_short) / sma_long) * 100
            score = min(spread / 5, 0.7)
            return {
                'signal': Signal.SELL,
                'score': score,
                'reason': f'Short MA below Long MA ({spread:.2f}%)'
            }

    def analyze_volume(self, df: pd.DataFrame) -> Dict:
        """Analyze volume indicators"""
        if df.empty or 'volume_ratio' not in df.columns:
            return {'signal': Signal.HOLD, 'score': 0, 'reason': 'No volume data'}

        volume_ratio = df['volume_ratio'].iloc[-1]
        price_change = df['close'].pct_change().iloc[-1]

        if pd.isna(volume_ratio) or pd.isna(price_change):
            return {'signal': Signal.HOLD, 'score': 0, 'reason': 'Invalid volume'}

        # High volume with price increase = bullish
        if volume_ratio > 1.5 and price_change > 0:
            score = min(volume_ratio / 3, 0.8)
            return {
                'signal': Signal.BUY,
                'score': score,
                'reason': f'High volume bullish ({volume_ratio:.1f}x avg)'
            }
        # High volume with price decrease = bearish
        elif volume_ratio > 1.5 and price_change < 0:
            score = min(volume_ratio / 3, 0.8)
            return {
                'signal': Signal.SELL,
                'score': score,
                'reason': f'High volume bearish ({volume_ratio:.1f}x avg)'
            }
        else:
            return {
                'signal': Signal.HOLD,
                'score': 0.3,
                'reason': f'Normal volume ({volume_ratio:.1f}x avg)'
            }

    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze overall trend"""
        if df.empty or 'trend' not in df.columns:
            return {'signal': Signal.HOLD, 'score': 0, 'reason': 'No trend data'}

        trend = df['trend'].iloc[-1]

        if trend == 'uptrend':
            return {
                'signal': Signal.BUY,
                'score': 0.7,
                'reason': 'Market in uptrend'
            }
        elif trend == 'downtrend':
            return {
                'signal': Signal.SELL,
                'score': 0.7,
                'reason': 'Market in downtrend'
            }
        else:
            return {
                'signal': Signal.HOLD,
                'score': 0.5,
                'reason': 'Market sideways'
            }

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """
        Generate comprehensive trading signal

        Args:
            df: DataFrame with technical indicators

        Returns:
            Dict with signal, confidence, and detailed analysis
        """
        if df.empty or len(df) < 2:
            return {
                'signal': Signal.HOLD,
                'confidence': 0,
                'action': 'HOLD',
                'reason': 'Insufficient data',
                'details': {}
            }

        # Analyze all indicators
        analyses = {
            'rsi': self.analyze_rsi(df),
            'macd': self.analyze_macd(df),
            'moving_averages': self.analyze_moving_averages(df),
            'volume': self.analyze_volume(df),
            'trend': self.analyze_trend(df)
        }

        # Calculate weighted score
        buy_score = 0
        sell_score = 0

        for indicator, analysis in analyses.items():
            weight = self.config['weights'].get(indicator, 0)
            score = analysis['score'] * weight

            if analysis['signal'] in [Signal.BUY, Signal.STRONG_BUY]:
                buy_score += score
            elif analysis['signal'] in [Signal.SELL, Signal.STRONG_SELL]:
                sell_score += score

        # Determine final signal
        confidence = max(buy_score, sell_score)
        min_confidence = self.config['min_confidence']

        if buy_score > sell_score and confidence >= min_confidence:
            if confidence > 0.8:
                signal = Signal.STRONG_BUY
            else:
                signal = Signal.BUY
            action = 'BUY'
        elif sell_score > buy_score and confidence >= min_confidence:
            if confidence > 0.8:
                signal = Signal.STRONG_SELL
            else:
                signal = Signal.SELL
            action = 'SELL'
        else:
            signal = Signal.HOLD
            action = 'HOLD'

        result = {
            'signal': signal,
            'action': action,
            'confidence': round(confidence, 3),
            'buy_score': round(buy_score, 3),
            'sell_score': round(sell_score, 3),
            'timestamp': df.index[-1] if not df.empty else None,
            'price': df['close'].iloc[-1] if 'close' in df.columns else None,
            'details': analyses,
            'reason': self._generate_reason(analyses, signal)
        }

        # Store in history
        self.signal_history.append(result)
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]

        logger.info(f"Generated signal: {action} (confidence: {confidence:.2%})")
        return result

    def _generate_reason(self, analyses: Dict, signal: Signal) -> str:
        """Generate human-readable reason for the signal"""
        reasons = []
        for indicator, analysis in analyses.items():
            if analysis['score'] > 0.5:
                reasons.append(analysis['reason'])

        if reasons:
            return '; '.join(reasons[:3])  # Top 3 reasons
        else:
            return f"Signal: {signal.value}"

    def get_signal_history(self, limit: int = 10) -> List[Dict]:
        """Get recent signal history"""
        return self.signal_history[-limit:]

    def get_signal_statistics(self) -> Dict:
        """Get statistics on generated signals"""
        if not self.signal_history:
            return {}

        signals = [s['action'] for s in self.signal_history]
        confidences = [s['confidence'] for s in self.signal_history]

        return {
            'total_signals': len(signals),
            'buy_signals': signals.count('BUY'),
            'sell_signals': signals.count('SELL'),
            'hold_signals': signals.count('HOLD'),
            'avg_confidence': np.mean(confidences),
            'max_confidence': np.max(confidences),
            'min_confidence': np.min(confidences)
        }
