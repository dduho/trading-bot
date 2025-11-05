#!/usr/bin/env python3
"""
Quick start script for the trading bot
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from trading_bot import main

if __name__ == "__main__":
    main()
