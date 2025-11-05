"""
Market Data Module
Handles connection to exchanges and real-time data streaming
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class MarketDataFeed:
    """Connects to exchanges and provides market data"""

    def __init__(self, exchange_name: str = 'binance', testnet: bool = True):
        """
        Initialize market data feed

        Args:
            exchange_name: Name of the exchange (binance, coinbase, kraken, etc.)
            testnet: Use testnet/paper trading if available
        """
        self.exchange_name = exchange_name
        self.testnet = testnet
        self.exchange = self._initialize_exchange()

    def _initialize_exchange(self):
        """Initialize the exchange connection"""
        try:
            exchange_class = getattr(ccxt, self.exchange_name)
            exchange = exchange_class({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',  # spot, future, margin
                }
            })

            if self.testnet and hasattr(exchange, 'set_sandbox_mode'):
                exchange.set_sandbox_mode(True)
                logger.info(f"Connected to {self.exchange_name} TESTNET")
            else:
                logger.info(f"Connected to {self.exchange_name}")

            return exchange

        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise

    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data for a symbol

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')

        Returns:
            Dict with ticker information
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'timestamp': ticker['timestamp'],
                'datetime': ticker['datetime'],
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'change': ticker.get('percentage', 0)
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}

    def get_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> pd.DataFrame:
        """
        Get OHLCV (candlestick) data

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)

            logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df

        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get order book data

        Args:
            symbol: Trading pair
            limit: Depth of order book

        Returns:
            Dict with bids and asks
        """
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            return {
                'bids': orderbook['bids'][:limit],
                'asks': orderbook['asks'][:limit],
                'timestamp': orderbook['timestamp']
            }
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return {'bids': [], 'asks': [], 'timestamp': None}

    def get_available_symbols(self) -> List[str]:
        """Get list of available trading pairs"""
        try:
            markets = self.exchange.load_markets()
            return [symbol for symbol in markets.keys() if '/USDT' in symbol or '/USD' in symbol]
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return []

    async def stream_ticker_async(self, symbol: str, callback, interval: float = 1.0):
        """
        Stream real-time ticker data

        Args:
            symbol: Trading pair
            callback: Function to call with each update
            interval: Update interval in seconds
        """
        logger.info(f"Starting ticker stream for {symbol} (interval: {interval}s)")

        while True:
            try:
                ticker = self.get_ticker(symbol)
                if ticker:
                    await callback(ticker)
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in ticker stream: {e}")
                await asyncio.sleep(5)  # Wait before retry

    def get_balance(self) -> Dict:
        """Get account balance (requires API keys)"""
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {}


class DataAggregator:
    """Aggregates data from multiple sources"""

    def __init__(self):
        self.feeds = {}

    def add_feed(self, name: str, feed: MarketDataFeed):
        """Add a data feed"""
        self.feeds[name] = feed

    def get_multi_timeframe_data(self, symbol: str, timeframes: List[str]) -> Dict[str, pd.DataFrame]:
        """Get data for multiple timeframes"""
        data = {}
        for tf in timeframes:
            if self.feeds:
                feed = list(self.feeds.values())[0]
                data[tf] = feed.get_ohlcv(symbol, tf)
        return data
