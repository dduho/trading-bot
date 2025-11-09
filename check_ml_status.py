#!/usr/bin/env python3
"""
Script pour vérifier l'état du système ML
"""
import sys
sys.path.append('src')

from ml_optimizer import MLOptimizer
from learning_engine import AdaptiveLearningEngine
from performance_analyzer import PerformanceAnalyzer
from trade_database import TradeDatabase
import yaml
import os

print("=" * 70)
print("  VÉRIFICATION DU SYSTÈME MACHINE LEARNING")
print("=" * 70)

# Charger la config
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

db = TradeDatabase()

# 1. Vérifier le ML Optimizer
print("\n🤖 ML Optimizer:")
ml = MLOptimizer(db)

# Tenter de charger le modèle
if ml.model is None:
    print("   ⏳ Tentative de chargement du modèle...")
    if ml.load_model():
        print(f"   ✓ Modèle chargé avec succès")
    else:
        print("   ✗ Échec du chargement")

if ml.model is not None:
    print(f"   ✓ Modèle: {ml.model_version}")
    print(f"   ✓ Type: {type(ml.model).__name__}")
    print(f"   ✓ Features: {len(ml.feature_names)}")
    
    # Lister les fichiers de modèles disponibles
    import os
    model_files = [f for f in os.listdir('models') if f.endswith('.pkl')]
    print(f"   ✓ Modèles disponibles: {len(model_files)}")
else:
    print("   ✗ Aucun modèle chargé")

# 2. Vérifier les données d'entraînement
print("\n📊 Données d'entraînement:")
trades = db.get_trades_for_ml(min_trades=50)
print(f"   Trades disponibles: {len(trades)}")
print(f"   Minimum requis: 50")
if len(trades) >= 50:
    print(f"   ✓ Suffisant pour l'entraînement")
else:
    print(f"   ✗ Insuffisant ({len(trades)}/50)")

# 3. Vérifier le Learning Engine
print("\n🧠 Adaptive Learning Engine:")
analyzer = PerformanceAnalyzer(db)
engine = AdaptiveLearningEngine(db, analyzer, ml, config)

print(f"   Learning activé: {engine.learning_enabled}")
print(f"   Intervalle: {engine.learning_interval_hours}h")
print(f"   Min trades: {engine.min_trades_for_learning}")
print(f"   Mode: {engine.adaptation_aggressiveness}")
print(f"   Auto-apply: {config.get('learning', {}).get('auto_apply_adaptations', False)}")

# 4. Vérifier si un cycle d'apprentissage devrait être déclenché
should_learn = engine.should_trigger_learning()
print(f"\n📚 Cycle d'apprentissage:")
print(f"   Doit se déclencher: {'✓ Oui' if should_learn else '✗ Non'}")

if not should_learn:
    stats = db.get_performance_stats(days=30)
    if stats['total_trades'] < engine.min_trades_for_learning:
        print(f"   Raison: Pas assez de trades ({stats['total_trades']}/{engine.min_trades_for_learning})")
    else:
        print(f"   Raison: Intervalle de temps non atteint")

# 5. Tester une prédiction
print("\n🎯 Test de prédiction ML:")
if ml.model is not None:
    test_conditions = {
        'rsi': 55.0,
        'macd': 0.002,
        'macd_signal': 0.001,
        'macd_hist': 0.001,
        'atr': 50.0,
        'sma_short': 42000,
        'sma_long': 41800,
        'bb_upper': 42500,
        'bb_middle': 42000,
        'bb_lower': 41500,
        'close': 42100,
        'volume_ratio': 1.3,
        'trend': 'uptrend',
        'signal_confidence': 0.7
    }
    
    prediction = ml.predict_trade_success(test_conditions)
    print(f"   Probabilité de succès: {prediction['success_probability']:.1%}")
    print(f"   Confiance: {prediction['confidence']:.1%}")
    print(f"   Recommandation: {prediction['ml_recommendation']}")
    print(f"   ✓ Prédiction fonctionnelle")
else:
    print(f"   ✗ Impossible de tester - modèle non chargé")

# 6. Vérifier l'enhancement des signaux
print("\n📡 Signal Enhancement:")
if engine.ml_optimizer and engine.ml_optimizer.model:
    test_signal = {'action': 'BUY', 'confidence': 0.70, 'reason': 'Test'}
    test_market = {
        'rsi': 58.0, 'macd': 0.003, 'macd_signal': 0.002, 'macd_hist': 0.001,
        'atr': 45.0, 'sma_short': 42500, 'sma_long': 42000, 'bb_upper': 43000,
        'bb_middle': 42500, 'bb_lower': 42000, 'close': 42700, 'volume_ratio': 1.6,
        'trend': 'uptrend', 'signal_confidence': 0.70
    }
    enhanced = engine.get_ml_enhanced_signal_confidence(test_signal, test_market)
    change = enhanced - test_signal['confidence']
    print(f"   Confiance originale: {test_signal['confidence']:.1%}")
    print(f"   Confiance ML: {enhanced:.1%}")
    print(f"   Ajustement: {change:+.1%}")
    print(f"   ✓ Enhancement fonctionnel")
else:
    print(f"   ✗ Enhancement non disponible")

# 7. Vérifier les feature importances
print("\n🎲 Feature Importance:")
if ml.model is not None:
    insights = ml.get_feature_insights()
    print(f"   Feature la plus importante: {insights['most_important_feature']}")
    print(f"   Top 3 features:")
    for i, (feature, importance) in enumerate(list(insights['top_10_features'].items())[:3], 1):
        print(f"      {i}. {feature}: {importance:.4f}")
    print(f"   ✓ Feature analysis disponible")

# 8. Configuration ML dans config.yaml
print("\n⚙️  Configuration ML (config.yaml):")
ml_config = config.get('learning', {})
print(f"   Learning enabled: {ml_config.get('enabled', False)}")
print(f"   Interval: {ml_config.get('learning_interval_hours', 'N/A')}h")
print(f"   Auto-apply: {ml_config.get('auto_apply_adaptations', False)}")
print(f"   Model type: {ml_config.get('ml_model', {}).get('type', 'N/A')}")
print(f"   Min accuracy: {ml_config.get('ml_model', {}).get('min_accuracy_threshold', 'N/A')}")

# 9. Dernière performance du modèle
print("\n📈 Dernière performance enregistrée:")
cursor = db.conn.cursor()
cursor.execute("""
    SELECT accuracy, precision_score, recall, f1_score, auc_score, 
           training_samples, timestamp
    FROM model_performance
    ORDER BY timestamp DESC
    LIMIT 1
""")
perf = cursor.fetchone()
if perf:
    print(f"   Accuracy: {perf[0]:.1%}")
    print(f"   Precision: {perf[1]:.1%}")
    print(f"   Recall: {perf[2]:.1%}")
    print(f"   F1 Score: {perf[3]:.1%}")
    print(f"   AUC: {perf[4]:.2f}")
    print(f"   Training samples: {perf[5]}")
    print(f"   Date: {perf[6]}")
else:
    print("   ✗ Aucune performance enregistrée")

db.conn.close()

print("\n" + "=" * 70)
print("STATUT GLOBAL ML:")
if ml.model and len(trades) >= 50 and engine.learning_enabled:
    print("✅ SYSTÈME ML OPÉRATIONNEL")
elif ml.model and engine.learning_enabled:
    print("⚠️  SYSTÈME ML ACTIF - En attente de plus de données")
else:
    print("❌ SYSTÈME ML INACTIF")
print("=" * 70)
