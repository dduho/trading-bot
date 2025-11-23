import sys
sys.path.append('src')
from src.trade_database import TradeDatabase

db = TradeDatabase()

# Analyser les trades
trades = db.get_trade_history(limit=1000, status='closed')
losses = [t for t in trades if t.get('pnl', 0) < 0]
winners = [t for t in trades if t.get('pnl', 0) > 0]

losses.sort(key=lambda x: x.get('pnl', 0))

print('TOP 10 PIRES PERTES:')
for i, t in enumerate(losses[:10], 1):
    dur = t.get('duration_minutes', 0)
    print(f'{i}. {t["symbol"]} {t["side"]}: {t.get("pnl", 0):.2f}$ ({dur:.0f}min)')

print()
print('ANALYSE DES SORTIES:')
stop_loss_exits = sum(1 for t in losses if 'stop' in str(t.get('exit_reason', '')).lower())
signal_exits = sum(1 for t in losses if 'signal' in str(t.get('exit_reason', '')).lower())
print(f'Stop loss: {stop_loss_exits}/{len(losses)} ({stop_loss_exits/len(losses)*100:.1f}%)')
print(f'Signal: {signal_exits}/{len(losses)} ({signal_exits/len(losses)*100:.1f}%)')

# Duree moyenne
avg_loss_dur = sum(t.get('duration_minutes', 0) for t in losses) / len(losses) if losses else 0
avg_win_dur = sum(t.get('duration_minutes', 0) for t in winners) / len(winners) if winners else 0
print(f'Avg loss duration: {avg_loss_dur:.1f}min')
print(f'Avg win duration: {avg_win_dur:.1f}min')

# Par symbole
print()
print('WIN RATE PAR SYMBOLE:')
symbols = set(t['symbol'] for t in trades)
for sym in sorted(symbols):
    sym_trades = [t for t in trades if t['symbol'] == sym]
    sym_wins = sum(1 for t in sym_trades if t.get('pnl', 0) > 0)
    wr = sym_wins / len(sym_trades) * 100 if sym_trades else 0
    print(f'{sym}: {wr:.1f}% ({sym_wins}/{len(sym_trades)})')
