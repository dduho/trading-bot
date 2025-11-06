import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('data/trading_history.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"📊 Tables dans la base de données: {[t[0] for t in tables]}\n")

# Check trades
cursor.execute("SELECT COUNT(*) FROM trades")
trade_count = cursor.fetchone()[0]
print(f"💰 Nombre total de trades: {trade_count}")

if trade_count > 0:
    # Vérifier les colonnes de la table
    cursor.execute("PRAGMA table_info(trades)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"  Colonnes de la table 'trades': {columns}\n")
    
    # Utiliser la première colonne de date disponible
    date_col = 'entry_time' if 'entry_time' in columns else 'id'
    cursor.execute(f"SELECT * FROM trades ORDER BY {date_col} DESC LIMIT 10")
    trades = cursor.fetchall()
    print("🔍 Derniers trades:")
    for trade in trades:
        print(f"  - {trade}")
else:
    print("  ⚠️  Aucun trade trouvé\n")

# Check signals if table exists
try:
    cursor.execute("SELECT COUNT(*) FROM signals WHERE timestamp > datetime('now', '-1 hour')")
    signal_count = cursor.fetchone()[0]
    print(f"\n📡 Signaux générés (dernière heure): {signal_count}")
    
    cursor.execute("""
        SELECT symbol, signal_type, confidence, timestamp 
        FROM signals 
        ORDER BY timestamp DESC 
        LIMIT 10
    """)
    signals = cursor.fetchall()
    if signals:
        print("\n🎯 Derniers signaux:")
        for sig in signals:
            print(f"  - {sig[0]}: {sig[1]} (confiance: {sig[2]:.2f}%) à {sig[3]}")
except:
    print("\n⚠️  Pas de table 'signals'")

# Check learning cycles
try:
    cursor.execute("SELECT COUNT(*) FROM learning_cycles")
    cycle_count = cursor.fetchone()[0]
    print(f"\n🤖 Cycles d'apprentissage exécutés: {cycle_count}")
    
    if cycle_count > 0:
        cursor.execute("SELECT * FROM learning_cycles ORDER BY timestamp DESC LIMIT 3")
        cycles = cursor.fetchall()
        print("\n📚 Derniers cycles:")
        for cycle in cycles:
            print(f"  - {cycle}")
except:
    print("\n⚠️  Pas de table 'learning_cycles'")

conn.close()
print("\n✅ Analyse terminée")
