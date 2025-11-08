"""
ML System Diagnostic & Test Script
Automated testing and verification of the machine learning system
"""

import sys
import os
sys.path.append('src')

from ml_optimizer import MLOptimizer
from learning_engine import AdaptiveLearningEngine
from performance_analyzer import PerformanceAnalyzer
from trade_database import TradeDatabase
import yaml
from datetime import datetime
import json


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {text}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {text}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {text}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {text}")


def test_database_connection():
    """Test 1: Database Connection"""
    print_header("TEST 1: Database Connection")

    try:
        db = TradeDatabase()
        stats = db.get_performance_stats(days=30)
        print_success(f"Database connected successfully")
        print_info(f"Total trades in DB: {stats['total_trades']}")

        if stats['total_trades'] < 50:
            print_warning(f"Low trade count for ML training (need >= 50)")
            return db, False
        else:
            print_success(f"Sufficient data for ML training")
            return db, True

    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return None, False


def test_model_loading(db):
    """Test 2: ML Model Loading"""
    print_header("TEST 2: ML Model Loading")

    try:
        ml = MLOptimizer(db)

        # Check if model files exist
        model_files = [f for f in os.listdir('models') if f.endswith('.pkl')]
        if not model_files:
            print_warning("No saved models found")
            return ml, False

        print_info(f"Found {len(model_files)} model file(s)")

        # Try to load latest model
        if ml.load_model():
            print_success(f"Model loaded: version {ml.model_version}")
            print_info(f"Features: {len(ml.feature_names)}")
            print_info(f"Model type: {type(ml.model).__name__}")
            return ml, True
        else:
            print_error("Failed to load model")
            return ml, False

    except Exception as e:
        print_error(f"Model loading error: {e}")
        return None, False


def test_ml_prediction(ml):
    """Test 3: ML Prediction"""
    print_header("TEST 3: ML Prediction Functionality")

    if ml is None or ml.model is None:
        print_error("Cannot test prediction - model not loaded")
        return False

    try:
        # Create test market conditions
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

        print_success("Prediction successful")
        print_info(f"Success probability: {prediction['success_probability']:.3f}")
        print_info(f"Confidence: {prediction['confidence']:.3f}")
        print_info(f"Recommendation: {prediction['ml_recommendation']}")

        # Validate prediction output
        required_keys = ['success_probability', 'confidence', 'prediction', 'ml_recommendation']
        if all(key in prediction for key in required_keys):
            print_success("Prediction output structure valid")
            return True
        else:
            print_error("Prediction output missing required keys")
            return False

    except Exception as e:
        print_error(f"Prediction failed: {e}")
        return False


def test_feature_importance(ml):
    """Test 4: Feature Importance Analysis"""
    print_header("TEST 4: Feature Importance Analysis")

    if ml is None or ml.model is None:
        print_error("Cannot analyze features - model not loaded")
        return False

    try:
        insights = ml.get_feature_insights()

        print_success("Feature importance calculated")
        print_info(f"Total features: {insights['total_features']}")
        print_info(f"Most important: {insights['most_important_feature']}")

        print(f"\n{Colors.BOLD}Top 5 Features:{Colors.RESET}")
        for i, (feature, importance) in enumerate(list(insights['top_10_features'].items())[:5], 1):
            print(f"  {i}. {feature:20s}: {importance:.4f}")

        return True

    except Exception as e:
        print_error(f"Feature analysis failed: {e}")
        return False


def test_learning_engine(db, ml):
    """Test 5: Learning Engine"""
    print_header("TEST 5: Adaptive Learning Engine")

    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        analyzer = PerformanceAnalyzer(db)
        engine = AdaptiveLearningEngine(db, analyzer, ml, config)

        print_success("Learning engine initialized")
        print_info(f"Learning enabled: {engine.learning_enabled}")
        print_info(f"Learning interval: {engine.learning_interval_hours}h")
        print_info(f"Min trades required: {engine.min_trades_for_learning}")
        print_info(f"Adaptation mode: {engine.adaptation_aggressiveness}")

        # Check if learning should be triggered
        should_learn = engine.should_trigger_learning()
        if should_learn:
            print_success("System ready for learning cycle")
        else:
            print_warning("Learning cycle not triggered (interval or data requirements)")

        # Get current strategy params
        params = engine.get_current_strategy_params()
        print_info(f"Current min confidence: {params['min_confidence']:.3f}")

        return engine, True

    except Exception as e:
        print_error(f"Learning engine initialization failed: {e}")
        return None, False


def test_signal_enhancement(engine, ml):
    """Test 6: Signal Enhancement"""
    print_header("TEST 6: ML Signal Enhancement")

    if engine is None or ml is None or ml.model is None:
        print_error("Cannot test enhancement - components not ready")
        return False

    try:
        # Test signal
        test_signal = {
            'action': 'BUY',
            'confidence': 0.70,
            'reason': 'Test signal'
        }

        # Test market conditions
        test_market = {
            'rsi': 58.0,
            'macd': 0.003,
            'macd_signal': 0.002,
            'macd_hist': 0.001,
            'atr': 45.0,
            'sma_short': 42500,
            'sma_long': 42000,
            'bb_upper': 43000,
            'bb_middle': 42500,
            'bb_lower': 42000,
            'close': 42700,
            'volume_ratio': 1.6,
            'trend': 'uptrend',
            'signal_confidence': 0.70
        }

        enhanced = engine.get_ml_enhanced_signal_confidence(test_signal, test_market)

        print_success("Signal enhancement successful")
        print_info(f"Original confidence: {test_signal['confidence']:.3f}")
        print_info(f"ML enhanced: {enhanced:.3f}")

        change = enhanced - test_signal['confidence']
        if abs(change) > 0.001:
            if change > 0:
                print_success(f"ML increased confidence by {change:.3f}")
            else:
                print_warning(f"ML decreased confidence by {abs(change):.3f}")
        else:
            print_info("ML made minimal adjustment")

        return True

    except Exception as e:
        print_error(f"Signal enhancement failed: {e}")
        return False


def test_model_performance(db):
    """Test 7: Model Performance Metrics"""
    print_header("TEST 7: Model Performance Metrics")

    try:
        # Query model performance from database
        conn = db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT model_name, model_version, accuracy, precision_score, recall,
                   f1_score, auc_score, training_samples, timestamp
            FROM model_performance
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

        if row:
            print_success("Latest model performance found")
            print_info(f"Model: {row[0]} v{row[1]}")
            print_info(f"Timestamp: {row[8]}")
            print(f"\n{Colors.BOLD}Performance Metrics:{Colors.RESET}")
            print(f"  Accuracy:  {row[2]:.3f} {'[OK]' if row[2] > 0.60 else '[LOW]'}")
            print(f"  Precision: {row[3]:.3f} {'[OK]' if row[3] > 0.55 else '[LOW]'}")
            print(f"  Recall:    {row[4]:.3f} {'[OK]' if row[4] > 0.50 else '[LOW]'}")
            print(f"  F1 Score:  {row[5]:.3f} {'[OK]' if row[5] > 0.55 else '[LOW]'}")
            print(f"  AUC Score: {row[6]:.3f} {'[OK]' if row[6] > 0.65 else '[LOW]'}")
            print_info(f"Training samples: {row[7]}")

            # Overall assessment
            if row[2] > 0.65 and row[6] > 0.70:
                print_success("Model performance: GOOD")
                return True
            elif row[2] > 0.55:
                print_warning("Model performance: ACCEPTABLE")
                return True
            else:
                print_warning("Model performance: NEEDS IMPROVEMENT")
                return False
        else:
            print_warning("No model performance metrics found in database")
            return False

    except Exception as e:
        print_error(f"Failed to retrieve model performance: {e}")
        return False


def test_training_data_quality(db):
    """Test 8: Training Data Quality"""
    print_header("TEST 8: Training Data Quality")

    try:
        trades = db.get_trades_for_ml(min_trades=10)

        print_success(f"Retrieved {len(trades)} trades for ML")

        if len(trades) == 0:
            print_error("No training data available")
            return False

        # Check data completeness
        sample = trades[0]
        required_fields = ['rsi', 'macd', 'macd_signal', 'macd_hist', 'atr',
                          'sma_short', 'sma_long', 'volume_ratio', 'trend', 'pnl']

        missing_fields = [field for field in required_fields if sample.get(field) is None]

        if missing_fields:
            print_warning(f"Missing fields in data: {', '.join(missing_fields)}")
        else:
            print_success("All required fields present")

        # Analyze data distribution
        winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        losing_trades = len(trades) - winning_trades
        win_rate = (winning_trades / len(trades)) * 100 if trades else 0

        print_info(f"Winning trades: {winning_trades}")
        print_info(f"Losing trades: {losing_trades}")
        print_info(f"Win rate: {win_rate:.1f}%")

        # Check for data balance
        if 30 <= win_rate <= 70:
            print_success("Data reasonably balanced")
            return True
        else:
            print_warning(f"Data imbalanced (win rate: {win_rate:.1f}%)")
            return True  # Still usable, just warning

    except Exception as e:
        print_error(f"Data quality check failed: {e}")
        return False


def run_full_diagnostic():
    """Run all diagnostic tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("      TRADING BOT - ML SYSTEM DIAGNOSTIC SUITE")
    print("             Comprehensive System Test")
    print("=" * 70)
    print(f"{Colors.RESET}")

    results = {}

    # Test 1: Database
    db, results['database'] = test_database_connection()

    if not db:
        print_error("\nCritical: Cannot proceed without database connection")
        return

    # Test 2: Model Loading
    ml, results['model_loading'] = test_model_loading(db)

    # Test 3: Prediction
    results['prediction'] = test_ml_prediction(ml)

    # Test 4: Feature Importance
    results['features'] = test_feature_importance(ml)

    # Test 5: Learning Engine
    engine, results['learning_engine'] = test_learning_engine(db, ml)

    # Test 6: Signal Enhancement
    results['signal_enhancement'] = test_signal_enhancement(engine, ml)

    # Test 7: Model Performance
    results['model_performance'] = test_model_performance(db)

    # Test 8: Data Quality
    results['data_quality'] = test_training_data_quality(db)

    # Summary
    print_header("DIAGNOSTIC SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests

    print(f"\n{Colors.BOLD}Test Results:{Colors.RESET}")
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name.replace('_', ' ').title():30s}: {status}")

    print(f"\n{Colors.BOLD}Overall:{Colors.RESET}")
    print(f"  Total Tests:  {total_tests}")
    print(f"  Passed:       {Colors.GREEN}{passed_tests}{Colors.RESET}")
    print(f"  Failed:       {Colors.RED}{failed_tests}{Colors.RESET}")

    success_rate = (passed_tests / total_tests) * 100

    print(f"\n{Colors.BOLD}Success Rate: ", end='')
    if success_rate == 100:
        print(f"{Colors.GREEN}{success_rate:.0f}%{Colors.RESET}")
        print(f"\n{Colors.GREEN}{Colors.BOLD}[OK] ALL SYSTEMS OPERATIONAL{Colors.RESET}")
    elif success_rate >= 75:
        print(f"{Colors.YELLOW}{success_rate:.0f}%{Colors.RESET}")
        print(f"\n{Colors.YELLOW}{Colors.BOLD}[WARN] SYSTEM OPERATIONAL WITH WARNINGS{Colors.RESET}")
    else:
        print(f"{Colors.RED}{success_rate:.0f}%{Colors.RESET}")
        print(f"\n{Colors.RED}{Colors.BOLD}[FAIL] SYSTEM REQUIRES ATTENTION{Colors.RESET}")

    print(f"\n{Colors.BLUE}Diagnostic completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")

    return results


if __name__ == "__main__":
    try:
        results = run_full_diagnostic()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Diagnostic interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n\n{Colors.RED}Diagnostic failed with error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
