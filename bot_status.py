#!/usr/bin/env python3
"""
Script pour afficher le statut actuel du bot de trading
"""
import sys
sys.path.append('src')

from trade_database import TradeDatabase
from datetime import datetime

db = TradeDatabase()

print("=" * 70)
print("  STATUT DU TRADING BOT")
print("=" * 70)

# Statistiques générales
stats_30d = db.get_performance_stats(days=30)
print(f"\n📊 Statistiques (30 derniers jours):")
print(f"   Total trades: {stats_30d['total_trades']}")
print(f"   Win rate: {stats_30d['win_rate']*100:.1f}%")
print(f"   Trades gagnants: {stats_30d['winning_trades']}")
print(f"   Trades perdants: {stats_30d['losing_trades']}")
print(f"   PnL total: {stats_30d['total_pnl']:.2f} USDT")
if stats_30d['profit_factor']:
    print(f"   Profit factor: {stats_30d['profit_factor']:.2f}")

# Statistiques dernières 24h
stats_1d = db.get_performance_stats(days=1)
print(f"\n📈 Dernières 24 heures:")
print(f"   Nouveaux trades: {stats_1d['total_trades']}")
if stats_1d['total_trades'] > 0:
    print(f"   Win rate: {stats_1d['win_rate']*100:.1f}%")
    print(f"   PnL: {stats_1d['total_pnl']:.2f} USDT")

# Trades en cours
cursor = db.conn.cursor()
cursor.execute("SELECT COUNT(*) FROM trades WHERE UPPER(status) = 'OPEN'")
open_trades = cursor.fetchone()[0]
print(f"\n💼 Trades actifs: {open_trades}")

if open_trades > 0:
    cursor.execute("""
        SELECT symbol, side, entry_price, entry_time 
        FROM trades 
        WHERE UPPER(status) = 'OPEN'
        ORDER BY entry_time DESC
    """)
    print("\n   Positions ouvertes:")
    for row in cursor.fetchall():
        print(f"   - {row[0]} {row[1]} @ {row[2]} (depuis {row[3]})")

# Derniers trades
print(f"\n🕒 Derniers 5 trades:")
cursor.execute("""
    SELECT symbol, side, pnl, pnl_percent, exit_time, exit_reason
    FROM trades 
    WHERE UPPER(status) = 'CLOSED'
    ORDER BY exit_time DESC
    LIMIT 5
""")
trades = cursor.fetchall()
if trades:
    for row in trades:
        pnl_sign = "+" if row[2] > 0 else ""
        print(f"   {row[0]} {row[1]}: {pnl_sign}{row[2]:.2f} USDT ({pnl_sign}{row[3]:.2f}%) - {row[4]} [{row[5]}]")
else:
    print("   Aucun trade fermé récemment")

# Modèle ML
cursor.execute("""
    SELECT model_name, accuracy, auc_score, training_samples, timestamp
    FROM model_performance
    ORDER BY timestamp DESC
    LIMIT 1
""")
model = cursor.fetchone()
if model:
    print(f"\n🤖 Modèle ML:")
    print(f"   Type: {model[0]}")
    print(f"   Accuracy: {model[1]*100:.1f}%")
    print(f"   AUC: {model[2]:.2f}")
    print(f"   Training samples: {model[3]}")
    print(f"   Dernière mise à jour: {model[4]}")

db.conn.close()

print("\n" + "=" * 70)
print(f"Statut généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
