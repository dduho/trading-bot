#!/usr/bin/env python3
"""
Force daily reset - Reset daily trade counter immediately
"""
import yaml
import sys
from datetime import datetime, date

def force_reset():
    print("=" * 70)
    print("  FORCE DAILY RESET - Increase limit and reset counter")
    print("=" * 70)
    
    # Load config
    print("\n📋 Loading config...")
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Show current values
    current_limit = config.get('risk', {}).get('max_daily_trades', 'NOT SET')
    print(f"   Current max_daily_trades: {current_limit}")
    
    # Increase the limit to 500 (safe for paper trading)
    if 'risk' not in config:
        config['risk'] = {}
    
    old_limit = config['risk'].get('max_daily_trades', 200)
    config['risk']['max_daily_trades'] = 500
    
    print(f"\n🔧 Updating max_daily_trades: {old_limit} → 500")
    
    # Save config
    with open('config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("✅ Config updated successfully!")
    
    print("\n" + "=" * 70)
    print("✅ Daily limit increased to 500 trades")
    print("=" * 70)
    print("\n📝 Next steps:")
    print("   1. Restart the bot to load new config")
    print("   2. Bot will now accept up to 500 trades per day")
    print("   3. Monitor performance with higher trade volume")
    print()

if __name__ == "__main__":
    force_reset()
