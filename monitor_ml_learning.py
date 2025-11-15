#!/usr/bin/env python3
"""
Monitor en temps réel de l'activité ML du bot
Affiche les cycles d'apprentissage, les adaptations et les performances
"""
import sys
sys.path.append('src')

from src.trade_database import TradeDatabase
from datetime import datetime, timedelta
import time

def print_header():
    print("\n" + "=" * 70)
    print("  MONITEUR D'APPRENTISSAGE ML EN TEMPS RÉEL")
    print("=" * 70)

def get_ml_activity(db):
    """Récupère l'activité ML récente"""
    cursor = db.conn.cursor()
    
    # Événements d'apprentissage récents
    cursor.execute("""
        SELECT event_type, description, timestamp, impact_metric
        FROM learning_events
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    events = cursor.fetchall()
    
    # Performance du modèle
    cursor.execute("""
        SELECT model_name, model_version, accuracy, auc_score, 
               training_samples, timestamp
        FROM model_performance
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    models = cursor.fetchall()
    
    # Statistiques des trades
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
               AVG(CASE WHEN pnl > 0 THEN pnl ELSE NULL END) as avg_win,
               AVG(CASE WHEN pnl < 0 THEN pnl ELSE NULL END) as avg_loss
        FROM trades
        WHERE UPPER(status) = 'CLOSED'
          AND entry_time >= datetime('now', '-24 hours')
    """)
    recent_stats = cursor.fetchone()
    
    return {
        'events': events,
        'models': models,
        'recent_stats': recent_stats
    }

def display_activity(activity):
    """Affiche l'activité ML"""
    print(f"\n⏰ Mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Événements récents
    events = activity['events']
    if events:
        print(f"\n📚 Derniers événements d'apprentissage ({len(events)}):")
        for event in events[:5]:
            event_type, description, timestamp, impact = event
            impact_str = f" (impact: {impact:.3f})" if impact else ""
            print(f"   [{timestamp}] {event_type}: {description}{impact_str}")
    else:
        print(f"\n📚 Aucun événement d'apprentissage enregistré")
    
    # Modèles
    models = activity['models']
    if models:
        print(f"\n🤖 Modèles ML ({len(models)}):")
        for model in models[:3]:
            name, version, accuracy, auc, samples, timestamp = model
            print(f"   [{timestamp}] {name} v{version}")
            print(f"      Accuracy: {accuracy:.1%} | AUC: {auc:.2f} | Samples: {samples}")
    else:
        print(f"\n🤖 Aucun modèle ML enregistré")
    
    # Stats récentes
    stats = activity['recent_stats']
    if stats and stats[0] > 0:
        total, wins, avg_win, avg_loss = stats
        win_rate = (wins / total * 100) if total > 0 else 0
        print(f"\n📊 Performance dernières 24h:")
        print(f"   Trades: {total} | Win rate: {win_rate:.1f}%")
        if avg_win:
            print(f"   Gain moyen: {avg_win:.2f} USDT | Perte moyenne: {avg_loss:.2f} USDT")
    else:
        print(f"\n📊 Aucun trade dans les dernières 24h")

def monitor_continuous(interval_seconds=60):
    """Monitoring continu"""
    db = TradeDatabase()
    
    try:
        print_header()
        print(f"\n🔄 Mode: Monitoring continu (rafraîchissement toutes les {interval_seconds}s)")
        print("   Appuyez sur Ctrl+C pour arrêter\n")
        
        iteration = 0
        while True:
            iteration += 1
            
            if iteration > 1:
                # Effacer l'écran (compatible multi-plateforme)
                print("\n" + "─" * 70)
            
            activity = get_ml_activity(db)
            display_activity(activity)
            
            print(f"\n⏳ Prochaine mise à jour dans {interval_seconds}s... (Itération {iteration})")
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring arrêté par l'utilisateur")
    finally:
        db.conn.close()

def monitor_once():
    """Affichage unique"""
    db = TradeDatabase()
    
    try:
        print_header()
        activity = get_ml_activity(db)
        display_activity(activity)
        print("\n" + "=" * 70)
    finally:
        db.conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor ML learning activity")
    parser.add_argument('--continuous', '-c', action='store_true',
                       help='Continuous monitoring mode')
    parser.add_argument('--interval', '-i', type=int, default=60,
                       help='Refresh interval in seconds (default: 60)')
    
    args = parser.parse_args()
    
    if args.continuous:
        monitor_continuous(args.interval)
    else:
        monitor_once()
