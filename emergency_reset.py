#!/usr/bin/env python3
"""
Emergency reset script - Force daily reset and fix config issues
"""
import yaml
from datetime import date
from src.trade_database import TradeDatabase

def emergency_reset():
    print("=" * 70)
    print("  EMERGENCY RESET - Force Daily Stats Reset")
    print("=" * 70)
    
    # 1. Load config
    print("\n📋 Loading config...")
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # 2. Fix missing 'strategy' key in config if needed
    if 'strategy' not in config:
        print("⚠️ WARNING: 'strategy' key missing in config.yaml")
        print("🔧 Adding default strategy configuration...")
        config['strategy'] = {
            'min_confidence': 3.0,
            'max_confidence': 15.0,
            'position_size_percent': 3.0,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 4.0
        }
        
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print("✅ Config updated with strategy section")
    
    # 3. Check database stats
    print("\n📊 Checking database stats...")
    db = TradeDatabase()
    
    # Get recent trades (last 1000)
    recent_trades = db.get_recent_trades(limit=1000, status=None)
    
    # Get today's trades
    today_str = date.today().isoformat()
    today_trades = [t for t in recent_trades if t.get('entry_time', '').startswith(today_str)]
    
    print(f"   Today ({today_str}): {len(today_trades)} trades")
    print(f"   Recent trades in DB: {len(recent_trades)} trades")
    
    # 4. Get open positions
    open_positions = db.get_open_positions()
    print(f"   Open positions: {len(open_positions)}")
    
    # 5. Check risk_manager state file
    print("\n🔍 Checking risk_manager state...")
    try:
        from src.risk_manager import RiskManager
        rm = RiskManager()
        
        print(f"   Current daily trades counter: {rm.daily_trades}")
        print(f"   Last reset date: {rm.last_reset_date}")
        print(f"   Current date: {date.today()}")
        
        # Force reset
        print("\n🔧 FORCING DAILY RESET...")
        rm.reset_daily_stats()
        
        print(f"   ✅ Daily trades counter after reset: {rm.daily_trades}")
        print(f"   ✅ Last reset date after reset: {rm.last_reset_date}")
        
    except Exception as e:
        print(f"   ❌ Error with RiskManager: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Emergency reset complete!")
    print("=" * 70)
    print("\n📝 Next steps:")
    print("   1. Restart the bot")
    print("   2. Monitor for new trades")
    print("   3. Check that daily limit is no longer blocking trades")
    print()

if __name__ == "__main__":
    emergency_reset()
