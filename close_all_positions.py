#!/usr/bin/env python3
"""
Emergency script to close all open positions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from risk_manager import RiskManager
from market_data import MarketDataFeed
import yaml

load_dotenv()

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize components
market_feed = MarketDataFeed(config)
risk_manager = RiskManager(config, market_feed)

print("=" * 60)
print("   EMERGENCY: CLOSING ALL OPEN POSITIONS")
print("=" * 60)
print()

# Get open positions
open_positions = [p for p in risk_manager.positions.values() if p.status == 'OPEN']

print(f"Found {len(open_positions)} open positions:")
for pos in open_positions:
    print(f"  - {pos.symbol} {pos.side} @ ${pos.entry_price:.4f}")

if not open_positions:
    print("No open positions to close")
    sys.exit(0)

# Confirm
confirm = input(f"\nClose all {len(open_positions)} positions? (yes/no): ")
if confirm.lower() != 'yes':
    print("Cancelled")
    sys.exit(0)

# Close all
print("\nClosing positions...")
for pos in open_positions:
    try:
        # Get current price
        ticker = market_feed.exchange.fetch_ticker(pos.symbol)
        current_price = ticker['last']

        # Force close
        risk_manager.close_position(pos.symbol, current_price, "MANUAL_CLOSE")
        print(f"✓ Closed {pos.symbol}")
    except Exception as e:
        print(f"✗ Error closing {pos.symbol}: {e}")

print(f"\n✅ Done! Closed {len(open_positions)} positions")
