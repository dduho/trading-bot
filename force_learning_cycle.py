#!/usr/bin/env python3
"""
Script pour forcer un cycle d'apprentissage ML immédiat
Permet de tester et valider que le système d'apprentissage continu fonctionne
"""
import sys
sys.path.append('src')

from src.trade_database import TradeDatabase
from src.performance_analyzer import PerformanceAnalyzer
from src.ml_optimizer import MLOptimizer
from src.learning_engine import AdaptiveLearningEngine
import yaml
import os
from datetime import datetime

print("=" * 70)
print("  FORCER UN CYCLE D'APPRENTISSAGE ML")
print("=" * 70)

# Charger la config
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Initialiser les composants
db = TradeDatabase()
analyzer = PerformanceAnalyzer(db)
ml = MLOptimizer(db)

# Charger le modèle existant
if ml.model is None:
    print("\n⏳ Chargement du modèle existant...")
    ml.load_model()

learning_config = config.get('learning', {})
engine = AdaptiveLearningEngine(db, analyzer, ml, learning_config)

print(f"\n📊 Configuration actuelle:")
print(f"   Learning enabled: {engine.learning_enabled}")
print(f"   Intervalle: {engine.learning_interval_hours}h")
print(f"   Min trades: {engine.min_trades_for_learning}")
print(f"   Mode: {engine.adaptation_aggressiveness}")

# Vérifier les données
stats = db.get_performance_stats(days=30)
print(f"\n📈 Données disponibles:")
print(f"   Total trades: {stats['total_trades']}")
print(f"   Win rate: {stats['win_rate']*100:.1f}%")

if stats['total_trades'] < engine.min_trades_for_learning:
    print(f"\n⚠️  ATTENTION: Seulement {stats['total_trades']} trades disponibles")
    print(f"   Minimum requis: {engine.min_trades_for_learning}")
    print(f"\n   Forçage du cycle quand même...")

# Forcer le cycle d'apprentissage
print(f"\n🚀 Démarrage du cycle d'apprentissage...")
print(f"   Timestamp: {datetime.now()}")

try:
    # Forcer last_learning_update à None pour permettre le cycle
    engine.last_learning_update = None
    
    # Exécuter le cycle
    result = engine.execute_learning_cycle()
    
    print(f"\n✅ Cycle d'apprentissage terminé!")
    print(f"\n📊 Résultats:")
    
    if 'error' in result:
        print(f"   ❌ Erreur: {result['error']}")
    else:
        print(f"   ✓ ML Model trained: {result.get('ml_model_trained', False)}")
        print(f"   ✓ Strategy adapted: {result.get('strategy_adapted', False)}")
        print(f"   ✓ Adaptations applied: {result.get('adaptations_applied', False)}")
        
        if 'model_metrics' in result:
            metrics = result['model_metrics']
            print(f"\n🤖 Métriques du modèle:")
            print(f"   Accuracy: {metrics.get('accuracy', 0):.1%}")
            print(f"   Precision: {metrics.get('precision', 0):.1%}")
            print(f"   Recall: {metrics.get('recall', 0):.1%}")
            print(f"   F1 Score: {metrics.get('f1_score', 0):.1%}")
            print(f"   AUC: {metrics.get('auc_score', 0):.2f}")
        
        if 'adaptations' in result:
            print(f"\n🔧 Adaptations proposées:")
            for key, value in result['adaptations'].items():
                print(f"   {key}: {value}")
        
        if 'learning_summary' in result:
            print(f"\n📝 Résumé:")
            print(f"   {result['learning_summary']}")

except Exception as e:
    print(f"\n❌ Erreur lors du cycle d'apprentissage:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()

# Vérifier l'état après apprentissage
print(f"\n📊 État après apprentissage:")
cursor = db.conn.cursor()
cursor.execute("""
    SELECT COUNT(*) FROM learning_events
""")
event_count = cursor.fetchone()[0]
print(f"   Événements d'apprentissage enregistrés: {event_count}")

cursor.execute("""
    SELECT model_name, accuracy, auc_score, timestamp
    FROM model_performance
    ORDER BY timestamp DESC
    LIMIT 1
""")
latest_model = cursor.fetchone()
if latest_model:
    print(f"\n🤖 Dernier modèle:")
    print(f"   Nom: {latest_model[0]}")
    print(f"   Accuracy: {latest_model[1]:.1%}")
    print(f"   AUC: {latest_model[2]:.2f}")
    print(f"   Date: {latest_model[3]}")

db.conn.close()

print("\n" + "=" * 70)
print("✅ Script terminé")
print("=" * 70)
