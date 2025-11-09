# Adaptive Learning System for Trading Bot 🧠

## Overview

The trading bot now features an **Adaptive Learning System** that continuously learns from its trading experiences and optimizes its strategy using machine learning. The bot can analyze its successes and failures, identify patterns, and automatically adjust its decision-making to improve performance over time.

## Key Features

### 1. Trade History Database 📊
- **Persistent Storage**: All trades are stored in an SQLite database with complete market context
- **Market Conditions**: Records technical indicators, market trends, and signal details at entry time
- **Performance Tracking**: Tracks P&L, win rate, profit factor, and other key metrics
- **Learning Events**: Records when and why the bot adapts its strategy

**Database Location**: `data/trading_history.db`

### 2. Performance Analysis 📈
The system analyzes:
- **Indicator Performance**: Which indicators are most predictive of winning trades
- **Optimal Ranges**: Best RSI levels, MACD conditions, volume patterns, etc.
- **Pattern Recognition**: Identifies market conditions that lead to success/failure
- **Learning Opportunities**: Automatically spots areas for improvement

### 3. Machine Learning Optimization 🤖
- **Random Forest Classifier**: Predicts probability of trade success
- **Feature Importance**: Identifies which market conditions matter most
- **Signal Enhancement**: Combines traditional signals with ML predictions
- **Continuous Training**: Model retrains as new data becomes available

**Model Storage**: `models/`

### 4. Adaptive Strategy Adjustment 🎯
The bot can automatically adjust:
- **Indicator Weights**: Optimizes the importance of RSI, MACD, MA, Volume, Trend
- **Confidence Thresholds**: Adjusts how selective the bot is with trades
- **Risk Parameters**: Modifies stop loss, take profit based on performance
- **Entry Criteria**: Tightens or loosens trade entry requirements

## How It Works

### Learning Cycle

The bot runs a learning cycle every 24 hours (configurable):

```
1. Performance Analysis
   └─> Analyze winning vs losing trades
   └─> Identify successful patterns
   └─> Calculate optimal indicator weights

2. Machine Learning
   └─> Train ML model on historical trades
   └─> Predict success probability for future trades
   └─> Extract feature importance

3. Strategy Optimization
   └─> Combine analysis + ML insights
   └─> Calculate optimal parameters
   └─> Identify necessary adaptations

4. Adaptation (if auto_apply_adaptations = true)
   └─> Update indicator weights
   └─> Adjust confidence threshold
   └─> Record learning event
```

### ML-Enhanced Trading Signals

Every trading signal is enhanced with ML:

```
Original Signal Confidence: 65%
ML Success Prediction: 78%
─────────────────────────────
Enhanced Confidence: 72%  ← Used for trading decisions
```

The system intelligently combines:
- Traditional technical analysis
- Machine learning predictions
- ML confidence level

## Configuration

Edit `config.yaml` to customize learning behavior:

```yaml
learning:
  enabled: true
  learning_interval_hours: 24        # Learning cycle frequency
  min_trades_for_learning: 50        # Min trades needed to start
  adaptation_aggressiveness: moderate # conservative/moderate/aggressive
  auto_apply_adaptations: false      # Manual review recommended initially

  ml_model:
    type: random_forest              # or gradient_boosting
    retrain_interval_hours: 168      # Weekly retraining
    min_accuracy_threshold: 0.60     # Min accuracy to use predictions

  target_metrics:
    win_rate: 0.55
    profit_factor: 2.0
    sharpe_ratio: 1.5
```

### Adaptation Aggressiveness

- **Conservative**: Only adapts when changes are significant (>10% weight change)
- **Moderate**: Adapts with moderate changes (>5% weight change)  ← Recommended
- **Aggressive**: Adapts quickly with small changes (>2% weight change)

### Auto-Apply Adaptations

- `false` (Recommended): Bot calculates optimal parameters but waits for manual approval
- `true` (Advanced): Bot automatically applies learned improvements

## Database Schema

### Tables

1. **trades**: Complete trade history with entry/exit prices, P&L, duration
2. **trade_conditions**: Market indicators at time of trade entry
3. **strategy_performance**: Performance snapshots over time
4. **model_performance**: ML model accuracy and metrics
5. **learning_events**: History of strategy adaptations

### Example Queries

```python
from src.trade_database import TradeDatabase

db = TradeDatabase()

# Get winning trades for analysis
winning_trades = db.get_winning_trades(limit=100)

# Get recent performance stats
stats = db.get_performance_stats(days=30)
print(f"Win Rate: {stats['win_rate']:.1%}")
print(f"Profit Factor: {stats['profit_factor']:.2f}")

# Get trades ready for ML training
ml_data = db.get_trades_for_ml(min_trades=50)
```

## New Components

### 1. TradeDatabase (`src/trade_database.py`)
Manages all data persistence and queries.

### 2. PerformanceAnalyzer (`src/performance_analyzer.py`)
Analyzes trading patterns and generates insights.

```python
from src.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(db)

# Analyze indicator performance
perf = analyzer.analyze_indicator_performance()

# Get learning opportunities
opportunities = analyzer.identify_learning_opportunities()

# Calculate optimal weights
weights = analyzer.calculate_optimal_weights()
```

### 3. MLOptimizer (`src/ml_optimizer.py`)
Machine learning model training and prediction.

```python
from src.ml_optimizer import MLOptimizer

ml = MLOptimizer(db)

# Train model
results = ml.train_model(model_type='random_forest')
print(f"Accuracy: {results['metrics']['accuracy']:.3f}")

# Predict trade success
prediction = ml.predict_trade_success(market_conditions)
print(f"Success Probability: {prediction['success_probability']:.2%}")

# Save/load model
ml.save_model()
ml.load_model()
```

### 4. AdaptiveLearningEngine (`src/learning_engine.py`)
Orchestrates the entire learning system.

```python
from src.learning_engine import AdaptiveLearningEngine

engine = AdaptiveLearningEngine(db, analyzer, ml_optimizer, config)

# Trigger learning cycle
results = engine.execute_learning_cycle()

# Get ML-enhanced signal
enhanced_confidence = engine.get_ml_enhanced_signal_confidence(
    signal, market_conditions
)

# Get current parameters
params = engine.get_current_strategy_params()
```

## Monitoring Learning Progress

### View Learning Reports

The bot automatically prints learning reports:

```
============================================================
ADAPTIVE LEARNING SYSTEM REPORT
============================================================
Learning Status: ENABLED
Last Update: 2025-11-05 14:30:00
Learning Cycles Completed: 5

Current Strategy Parameters:
  Minimum Confidence: 0.62
  Indicator Weights:
    rsi: 0.280
    macd: 0.240
    moving_averages: 0.270
    volume: 0.130
    trend: 0.080

Most Recent Learning Cycle:
  Timestamp: 2025-11-05 14:30:00
  Success: True
  Adaptations: 2
  ML Accuracy: 0.735
============================================================
```

### View Performance Reports

```
============================================================
TRADING BOT PERFORMANCE REPORT (Last 30 Days)
============================================================

Overall Performance:
  Total Trades: 87
  Win Rate: 58.62%
  Total P&L: $1,234.56
  Profit Factor: 2.15
  Average Win: $42.30
  Average Loss: $18.50

Learning Opportunities:
  1. [HIGH] low_profit_factor
     Profit factor is low. Winning trades are not large enough.

  2. [MEDIUM] indicator_optimization
     High volume confirms good trades - increase weight
============================================================
```

## Best Practices

### 1. Start with Paper Trading
- Collect at least 50-100 trades before relying on ML
- Let the model prove itself before going live

### 2. Monitor Learning Events
```python
# View learning history
cursor = db.conn.cursor()
cursor.execute("""
    SELECT * FROM learning_events
    ORDER BY timestamp DESC
    LIMIT 10
""")
for event in cursor.fetchall():
    print(dict(event))
```

### 3. Review Adaptations Manually
- Keep `auto_apply_adaptations: false` initially
- Review suggested changes before applying
- Understand why the bot wants to change

### 4. Track Model Accuracy
```python
# View model performance over time
cursor.execute("""
    SELECT model_version, accuracy, timestamp
    FROM model_performance
    ORDER BY timestamp DESC
""")
```

### 5. Backup Your Data
```bash
# Backup database regularly
cp data/trading_history.db data/backups/trading_history_$(date +%Y%m%d).db

# Backup models
cp -r models/ models_backup_$(date +%Y%m%d)/
```

## Troubleshooting

### Not Enough Data
```
WARNING: Only 23 trades available, need 50 for ML training
```
**Solution**: Continue trading to collect more data. ML features will activate automatically.

### Low Model Accuracy
```
ML model accuracy: 0.52 (below threshold 0.60)
```
**Solution**:
- Collect more diverse trading data
- Review if market conditions are very random/choppy
- Adjust `min_accuracy_threshold` if needed

### Learning Cycle Errors
Check logs for specific errors:
```bash
tail -f trading_bot.log | grep -i "learning"
```

## Advanced Usage

### Manual Learning Trigger
```python
# Force learning cycle
if bot.learning_engine.learning_enabled:
    results = bot.learning_engine.execute_learning_cycle()
```

### Custom Model Training
```python
# Train with custom parameters
from sklearn.ensemble import RandomForestClassifier

ml_optimizer.model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=10
)
ml_optimizer.train_model()
```

### Export Data for Analysis
```python
import pandas as pd

# Export trades to CSV
trades = db.get_trades_for_ml()
df = pd.DataFrame(trades)
df.to_csv('trades_export.csv', index=False)

# Analyze in Jupyter notebook
# ...
```

## Performance Metrics Explained

- **Win Rate**: Percentage of profitable trades (target: >55%)
- **Profit Factor**: Total wins / Total losses (target: >2.0)
- **Sharpe Ratio**: Risk-adjusted returns (target: >1.5)
- **Average Win/Loss**: Average profit per winning/losing trade
- **Max Drawdown**: Largest peak-to-trough decline

## Future Enhancements

Potential additions to the learning system:
- Deep learning models (LSTM, Transformers)
- Reinforcement learning for optimal policy
- Multi-timeframe analysis
- Sentiment analysis integration
- Portfolio-level optimization
- Market regime detection
- Automated hyperparameter tuning

## Support & Questions

If you have questions about the learning system:
1. Check the logs: `trading_bot.log`
2. Review database: Use SQLite browser on `data/trading_history.db`
3. Check model files: `models/` directory

## Disclaimer

The learning system is designed to help improve trading performance, but:
- Past performance doesn't guarantee future results
- Always test thoroughly in paper trading first
- Monitor the bot's decisions carefully
- Machine learning can overfit to historical data
- Market conditions change and models may need retraining

**Always trade responsibly and never risk more than you can afford to lose.**
