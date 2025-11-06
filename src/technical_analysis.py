"""
Technical Analysis Module
Calculates technical indicators and analyzes market conditions
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Performs technical analysis on market data"""

    def __init__(self, config: Dict = None):
        """
        Initialize technical analyzer

        Args:
            config: Configuration dict with indicator parameters
        """
        self.config = config or self._default_config()

    def _default_config(self) -> Dict:
        """Default indicator configuration"""
        return {
            'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
            'macd': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
            'moving_averages': {'sma_short': 20, 'sma_long': 50, 'ema_short': 12, 'ema_long': 26},
            'bollinger_bands': {'period': 20, 'std_dev': 2}
        }

    def calculate_rsi(self, df: pd.DataFrame, period: int = None) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)

        Args:
            df: DataFrame with 'close' column
            period: RSI period (default from config)

        Returns:
            Series with RSI values
        """
        if period is None:
            period = self.config['rsi']['period']

        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Args:
            df: DataFrame with 'close' column

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        fast = self.config['macd'].get('fast_period', self.config['macd'].get('fast', 12))
        slow = self.config['macd'].get('slow_period', self.config['macd'].get('slow', 26))
        signal = self.config['macd'].get('signal_period', self.config['macd'].get('signal', 9))

        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_sma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return df['close'].rolling(window=period).mean()

    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df['close'].ewm(span=period, adjust=False).mean()

    def calculate_bollinger_bands(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands

        Returns:
            Tuple of (upper band, middle band, lower band)
        """
        bb_config = self.config.get('bollinger_bands', self.config.get('bb', {}))
        period = bb_config.get('period', 20)
        std_dev = bb_config.get('std_dev', bb_config.get('std', 2))

        middle = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper, middle, lower

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR) for volatility

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period

        Returns:
            Series with ATR values
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator

        Returns:
            Tuple of (%K, %D)
        """
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()

        k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=3).mean()

        return k_percent, d_percent

    def calculate_volume_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate volume-based indicators"""
        volume_sma = df['volume'].rolling(window=20).mean()
        volume_ratio = df['volume'] / volume_sma

        # On-Balance Volume (OBV)
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()

        return {
            'volume_sma': volume_sma,
            'volume_ratio': volume_ratio,
            'obv': obv
        }

    def analyze_trend(self, df: pd.DataFrame) -> str:
        """
        Determine market trend

        Returns:
            'uptrend', 'downtrend', or 'sideways'
        """
        ma_config = self.config.get('moving_averages', self.config.get('sma', {}))
        sma_short = self.calculate_sma(df, ma_config.get('sma_short', ma_config.get('short', 20)))
        sma_long = self.calculate_sma(df, ma_config.get('sma_long', ma_config.get('long', 50)))

        if len(sma_short) < 2 or len(sma_long) < 2:
            return 'unknown'

        current_short = sma_short.iloc[-1]
        current_long = sma_long.iloc[-1]
        prev_short = sma_short.iloc[-2]
        prev_long = sma_long.iloc[-2]

        if current_short > current_long and prev_short > prev_long:
            return 'uptrend'
        elif current_short < current_long and prev_short < prev_long:
            return 'downtrend'
        else:
            return 'sideways'

    def get_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators and add to dataframe

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with all indicators added
        """
        result = df.copy()

        try:
            # RSI
            result['rsi'] = self.calculate_rsi(df)

            # MACD
            result['macd'], result['macd_signal'], result['macd_hist'] = self.calculate_macd(df)

            # Moving Averages
            ma_config = self.config.get('moving_averages', self.config.get('sma', {}))
            result['sma_short'] = self.calculate_sma(df, ma_config.get('sma_short', ma_config.get('short', 20)))
            result['sma_long'] = self.calculate_sma(df, ma_config.get('sma_long', ma_config.get('long', 50)))
            ema_config = self.config.get('moving_averages', self.config.get('ema', {}))
            result['ema_short'] = self.calculate_ema(df, ema_config.get('ema_short', ema_config.get('short', 12)))
            result['ema_long'] = self.calculate_ema(df, ema_config.get('ema_long', ema_config.get('long', 26)))

            # Bollinger Bands
            result['bb_upper'], result['bb_middle'], result['bb_lower'] = self.calculate_bollinger_bands(df)

            # ATR
            result['atr'] = self.calculate_atr(df)

            # Stochastic
            result['stoch_k'], result['stoch_d'] = self.calculate_stochastic(df)

            # Volume indicators
            vol_indicators = self.calculate_volume_indicators(df)
            result['volume_sma'] = vol_indicators['volume_sma']
            result['volume_ratio'] = vol_indicators['volume_ratio']
            result['obv'] = vol_indicators['obv']

            # Trend
            result['trend'] = self.analyze_trend(df)

            logger.info(f"Calculated {len(result.columns) - 6} technical indicators")
            return result

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return result

    def get_market_summary(self, df: pd.DataFrame) -> Dict:
        """
        Get a summary of current market conditions

        Args:
            df: DataFrame with indicators

        Returns:
            Dict with market summary
        """
        if df.empty or len(df) < 2:
            return {}

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        return {
            'price': latest['close'],
            'change_percent': ((latest['close'] - prev['close']) / prev['close']) * 100,
            'rsi': latest.get('rsi', None),
            'rsi_signal': self._interpret_rsi(latest.get('rsi', 50)),
            'macd_signal': 'bullish' if latest.get('macd', 0) > latest.get('macd_signal', 0) else 'bearish',
            'trend': latest.get('trend', 'unknown'),
            'volume_ratio': latest.get('volume_ratio', 1.0),
            'volatility': latest.get('atr', 0),
            'bollinger_position': self._interpret_bollinger(latest)
        }

    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI value"""
        if pd.isna(rsi):
            return 'unknown'
        if rsi > self.config['rsi']['overbought']:
            return 'overbought'
        elif rsi < self.config['rsi']['oversold']:
            return 'oversold'
        else:
            return 'neutral'

    def _interpret_bollinger(self, row: pd.Series) -> str:
        """Interpret position relative to Bollinger Bands"""
        if pd.isna(row.get('bb_upper')) or pd.isna(row.get('bb_lower')):
            return 'unknown'

        price = row['close']
        if price > row['bb_upper']:
            return 'above_upper'
        elif price < row['bb_lower']:
            return 'below_lower'
        else:
            return 'within_bands'
