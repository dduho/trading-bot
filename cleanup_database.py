"""
Database Cleanup Script - Clean up phantom and stuck positions
"""

import sys
sys.path.insert(0, 'src')

from trade_database import TradeDatabase
from datetime import datetime

def main():
    db = TradeDatabase()
    
    print("\n" + "="*60)
    print("DATABASE CLEANUP - PHANTOM POSITIONS")
    print("="*60 + "\n")
    
    # Get all open positions
    open_positions = db.get_trade_history(limit=200, status='open')
    
    print(f"Found {len(open_positions)} open positions in database\n")
    
    if not open_positions:
        print("✅ No open positions to clean up")
        return
    
    # Check for stuck positions (>24h old)
    now = datetime.now()
    stuck_positions = []
    
    for pos in open_positions:
        entry_time = datetime.fromisoformat(pos['entry_time'])
        age_hours = (now - entry_time).total_seconds() / 3600
        
        if age_hours > 24:
            stuck_positions.append({
                'id': pos['id'],
                'symbol': pos['symbol'],
                'side': pos['side'],
                'entry_time': pos['entry_time'],
                'age_hours': age_hours
            })
    
    if stuck_positions:
        print(f"⚠️  Found {len(stuck_positions)} stuck positions (>24h old):\n")
        
        for pos in stuck_positions:
            print(f"  ID {pos['id']}: {pos['symbol']:12} {pos['side']:5} - {pos['age_hours']:.1f}h old")
        
        print(f"\n🧹 Cleaning up {len(stuck_positions)} stuck positions...")
        
        for pos in stuck_positions:
            # Close at breakeven (entry price)
            trade = db.get_trade_with_conditions(pos['id'])
            if trade:
                db.update_trade(pos['id'], {
                    'status': 'closed',
                    'exit_price': trade['entry_price'],
                    'exit_time': now,
                    'pnl': 0,
                    'pnl_percent': 0,
                    'exit_reason': 'Cleanup: Stuck position >24h',
                    'duration_minutes': pos['age_hours'] * 60
                })
                print(f"  ✓ Closed {pos['symbol']}")
        
        print(f"\n✅ Cleanup complete - {len(stuck_positions)} positions closed")
    else:
        print("✅ No stuck positions found")
    
    # Show remaining open positions
    open_positions = db.get_trade_history(limit=100, status='open')
    print(f"\n📊 Remaining open positions: {len(open_positions)}")
    
    if open_positions:
        print("\nCurrent open positions:")
        for pos in open_positions:
            entry_time = datetime.fromisoformat(pos['entry_time'])
            age_hours = (now - entry_time).total_seconds() / 3600
            print(f"  {pos['symbol']:12} {pos['side']:5} - {age_hours:.1f}h old - Entry: ${pos['entry_price']:.4f}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
