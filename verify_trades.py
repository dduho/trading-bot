import sys
sys.path.append('src')
from trade_database import TradeDatabase

db = TradeDatabase()
cursor = db.conn.cursor()

# Vérifier le statut
cursor.execute("SELECT status, COUNT(*) FROM trades GROUP BY status")
print("Status counts:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Tester avec CLOSED
cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED'")
closed_upper = cursor.fetchone()[0]
print(f"\nCLOSED (uppercase): {closed_upper}")

# Tester avec closed
cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'closed'")
closed_lower = cursor.fetchone()[0]
print(f"closed (lowercase): {closed_lower}")

# Get trades for ML
trades = db.get_trades_for_ml(min_trades=10)
print(f"\nget_trades_for_ml() returned: {len(trades)} trades")

db.conn.close()
