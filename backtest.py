#!/usr/bin/env python3
"""
Backtesting script for the trading strategy
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from market_data import MarketDataFeed
from technical_analysis import TechnicalAnalyzer
from signal_generator import SignalGenerator
from risk_manager import RiskManager


def backtest(symbol='BTC/USDT', timeframe='1h', days=30):
    """
    Run backtest on historical data

    Args:
        symbol: Trading pair
        timeframe: Timeframe for analysis
        days: Number of days to backtest
    """
    print(f"\n{'='*80}")
    print(f"BACKTESTING: {symbol} ({timeframe}) - Last {days} days")
    print(f"{'='*80}\n")

    # Initialize components
    market_feed = MarketDataFeed('binance', testnet=False)
    analyzer = TechnicalAnalyzer()
    signal_gen = SignalGenerator()
    risk_mgr = RiskManager()

    # Get historical data
    limit = days * 24 if timeframe == '1h' else days * 24 * 60  # Approximate
    df = market_feed.get_ohlcv(symbol, timeframe, limit=min(limit, 1000))

    if df.empty:
        print("No data available for backtesting")
        return

    print(f"Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}\n")

    # Calculate indicators
    df_indicators = analyzer.get_all_indicators(df)

    # Simulate trading
    capital = 10000
    trades = []

    for i in range(50, len(df_indicators)):  # Start after indicators warm up
        window = df_indicators.iloc[:i+1]
        signal = signal_gen.generate_signal(window)
        price = window['close'].iloc[-1]
        timestamp = window.index[-1]

        # Execute signals
        if signal['action'] == 'BUY' and signal['confidence'] >= 0.6:
            can_open, _ = risk_mgr.can_open_position(symbol)
            if can_open:
                stop_loss = risk_mgr.calculate_stop_loss(price, 'long')
                take_profit = risk_mgr.calculate_take_profit(price, stop_loss, 'long')
                quantity = risk_mgr.calculate_position_size(capital, 2.0, price, stop_loss)

                position = risk_mgr.open_position(
                    symbol, 'long', price, quantity, stop_loss, take_profit
                )
                if position:
                    print(f"[{timestamp}] BUY @ ${price:.2f} (confidence: {signal['confidence']:.1%})")

        elif signal['action'] == 'SELL' and symbol in risk_mgr.positions:
            closed = risk_mgr.close_position(symbol, price, "Sell Signal")
            if closed:
                trades.append(closed.to_dict())
                capital += closed.pnl
                print(f"[{timestamp}] SELL @ ${price:.2f} | PnL: ${closed.pnl:.2f}")

        # Update positions
        risk_mgr.update_positions({symbol: price})

    # Close any remaining positions
    if symbol in risk_mgr.positions:
        final_price = df_indicators['close'].iloc[-1]
        closed = risk_mgr.close_position(symbol, final_price, "Backtest End")
        if closed:
            trades.append(closed.to_dict())
            capital += closed.pnl

    # Print results
    print(f"\n{'='*80}")
    print("BACKTEST RESULTS")
    print(f"{'='*80}\n")

    stats = risk_mgr.get_performance_stats()

    print(f"Initial Capital:  ${10000:.2f}")
    print(f"Final Capital:    ${capital:.2f}")
    print(f"Total Return:     ${capital - 10000:.2f} ({(capital - 10000) / 10000 * 100:.2f}%)")
    print(f"\nTotal Trades:     {stats['total_trades']}")
    print(f"Winning Trades:   {stats['winning_trades']}")
    print(f"Losing Trades:    {stats['losing_trades']}")
    print(f"Win Rate:         {stats['win_rate']:.1f}%")
    print(f"Average Win:      ${stats['avg_win']:.2f}")
    print(f"Average Loss:     ${stats['avg_loss']:.2f}")
    print(f"Profit Factor:    {stats['profit_factor']:.2f}")
    print(f"Largest Win:      ${stats['largest_win']:.2f}")
    print(f"Largest Loss:     ${stats['largest_loss']:.2f}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Run backtest
    backtest(symbol='BTC/USDT', timeframe='1h', days=30)
