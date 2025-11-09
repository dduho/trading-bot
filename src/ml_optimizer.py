"""
ML Optimizer - Machine Learning system for strategy optimization
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from typing import Dict, List, Any, Tuple, Optional
import logging
import pickle
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MLOptimizer:
    """
    Machine Learning optimizer for trading strategy.
    Uses historical trade data to predict success probability and optimize parameters.
    """

    def __init__(self, db, model_dir: str = "models"):
        """
        Initialize ML optimizer.

        Args:
            db: TradeDatabase instance
            model_dir: Directory to save/load models
        """
        self.db = db
        self.model_dir = model_dir
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_version = datetime.now().strftime("%Y%m%d_%H%M%S")

        os.makedirs(model_dir, exist_ok=True)
        logger.info("ML Optimizer initialized")

    def prepare_training_data(self, min_trades: int = 50) -> Tuple[Optional[pd.DataFrame], Optional[pd.Series]]:
        """
        Prepare training data from historical trades.

        Args:
            min_trades: Minimum number of trades required for training

        Returns:
            Tuple of (features_df, labels_series) or (None, None) if insufficient data
        """
        trades = self.db.get_trades_for_ml(min_trades=min_trades)

        if len(trades) < min_trades:
            logger.warning(f"Insufficient trades for ML training: {len(trades)} < {min_trades}")
            return None, None

        # Convert to DataFrame
        df = pd.DataFrame(trades)

        # Create features from market conditions
        features = []
        labels = []

        for _, trade in df.iterrows():
            # Skip if missing critical data
            if pd.isna(trade.get('rsi')) or pd.isna(trade.get('macd')):
                continue

            feature_dict = {
                # Technical indicators
                'rsi': trade.get('rsi', 50),
                'macd': trade.get('macd', 0),
                'macd_signal': trade.get('macd_signal', 0),
                'macd_hist': trade.get('macd_hist', 0),
                'atr': trade.get('atr', 0),

                # Moving averages
                'sma_short': trade.get('sma_short', 0),
                'sma_long': trade.get('sma_long', 0),
                'ma_crossover': (trade.get('sma_short', 0) - trade.get('sma_long', 0)),

                # Bollinger Bands
                'bb_position': self._calculate_bb_position(
                    trade.get('close', 0),
                    trade.get('bb_upper', 0),
                    trade.get('bb_middle', 0),
                    trade.get('bb_lower', 0)
                ),

                # Volume
                'volume_ratio': trade.get('volume_ratio', 1.0),

                # Trend encoding
                'trend_uptrend': 1 if trade.get('trend') == 'uptrend' else 0,
                'trend_downtrend': 1 if trade.get('trend') == 'downtrend' else 0,
                'trend_sideways': 1 if trade.get('trend') == 'sideways' else 0,

                # Signal metadata
                'signal_confidence': trade.get('signal_confidence', 0.5),

                # Derived features
                'rsi_oversold': 1 if trade.get('rsi', 50) < 30 else 0,
                'rsi_overbought': 1 if trade.get('rsi', 50) > 70 else 0,
                'macd_bullish': 1 if trade.get('macd_hist', 0) > 0 else 0,
                'high_volume': 1 if trade.get('volume_ratio', 1) > 1.5 else 0,
            }

            features.append(feature_dict)

            # Label: 1 if profitable trade, 0 if loss
            label = 1 if trade.get('pnl', 0) > 0 else 0
            labels.append(label)

        if not features:
            logger.warning("No valid features extracted from trades")
            return None, None

        features_df = pd.DataFrame(features)
        labels_series = pd.Series(labels)

        self.feature_names = list(features_df.columns)

        logger.info(f"Training data prepared: {len(features_df)} samples, {len(self.feature_names)} features")
        return features_df, labels_series

    def _calculate_bb_position(self, price: float, bb_upper: float, bb_middle: float, bb_lower: float) -> float:
        """Calculate relative position within Bollinger Bands."""
        if bb_upper == bb_lower:
            return 0.5

        if price >= bb_upper:
            return 1.0
        elif price <= bb_lower:
            return 0.0
        else:
            return (price - bb_lower) / (bb_upper - bb_lower)

    def train_model(self, model_type: str = 'random_forest') -> Dict[str, Any]:
        """
        Train machine learning model to predict trade success.

        Args:
            model_type: Type of model ('random_forest' or 'gradient_boosting')

        Returns:
            Dictionary with training results and metrics
        """
        # Prepare data
        X, y = self.prepare_training_data(min_trades=50)

        if X is None or y is None:
            return {
                'success': False,
                'error': 'Insufficient training data'
            }

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Initialize model
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        else:
            return {
                'success': False,
                'error': f'Unknown model type: {model_type}'
            }

        # Train
        logger.info(f"Training {model_type} model...")
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'auc_score': roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0
        }

        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='accuracy')
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()

        # Feature importance
        feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

        results = {
            'success': True,
            'model_type': model_type,
            'model_version': self.model_version,
            'metrics': metrics,
            'feature_importance': feature_importance,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_count': len(self.feature_names)
        }

        # Save model performance to database
        self.db.insert_model_performance({
            'model_name': model_type,
            'model_version': self.model_version,
            'accuracy': metrics['accuracy'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1_score': metrics['f1_score'],
            'auc_score': metrics['auc_score'],
            'training_samples': len(X_train),
            'validation_samples': len(X_test),
            'parameters': {'cv_mean': metrics['cv_mean'], 'cv_std': metrics['cv_std']},
            'feature_importance': feature_importance
        })

        logger.info(f"Model trained successfully - Accuracy: {metrics['accuracy']:.3f}, AUC: {metrics['auc_score']:.3f}")
        return results

    def predict_trade_success(self, market_conditions: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict probability of trade success given market conditions.

        Args:
            market_conditions: Dictionary with current market indicators

        Returns:
            Dictionary with prediction probability and confidence
        """
        if self.model is None:
            logger.warning("Model not trained yet, loading from file...")
            if not self.load_model():
                return {
                    'success_probability': 0.5,
                    'confidence': 0.0,
                    'prediction': 'unknown'
                }

        # Create feature vector
        features = {
            'rsi': market_conditions.get('rsi', 50),
            'macd': market_conditions.get('macd', 0),
            'macd_signal': market_conditions.get('macd_signal', 0),
            'macd_hist': market_conditions.get('macd_hist', 0),
            'atr': market_conditions.get('atr', 0),
            'sma_short': market_conditions.get('sma_short', 0),
            'sma_long': market_conditions.get('sma_long', 0),
            'ma_crossover': market_conditions.get('sma_short', 0) - market_conditions.get('sma_long', 0),
            'bb_position': self._calculate_bb_position(
                market_conditions.get('close', 0),
                market_conditions.get('bb_upper', 0),
                market_conditions.get('bb_middle', 0),
                market_conditions.get('bb_lower', 0)
            ),
            'volume_ratio': market_conditions.get('volume_ratio', 1.0),
            'trend_uptrend': 1 if market_conditions.get('trend') == 'uptrend' else 0,
            'trend_downtrend': 1 if market_conditions.get('trend') == 'downtrend' else 0,
            'trend_sideways': 1 if market_conditions.get('trend') == 'sideways' else 0,
            'signal_confidence': market_conditions.get('signal_confidence', 0.5),
            'rsi_oversold': 1 if market_conditions.get('rsi', 50) < 30 else 0,
            'rsi_overbought': 1 if market_conditions.get('rsi', 50) > 70 else 0,
            'macd_bullish': 1 if market_conditions.get('macd_hist', 0) > 0 else 0,
            'high_volume': 1 if market_conditions.get('volume_ratio', 1) > 1.5 else 0,
        }

        # Ensure feature_names are known; align with scaler feature names if needed
        if not self.feature_names and hasattr(self.scaler, 'feature_names_in_'):
            try:
                self.feature_names = list(self.scaler.feature_names_in_)
            except Exception:
                # Fallback: keep current inferred order from features dict
                self.feature_names = list(features.keys())

        # Build a DataFrame with the exact columns used during fitting to avoid warnings
        # Fill missing required columns with 0
        row = {name: features.get(name, 0) for name in self.feature_names}
        X_df = pd.DataFrame([row], columns=self.feature_names)

        # Scale and predict using DataFrame (preserves feature names)
        X_scaled = self.scaler.transform(X_df)
        proba = self.model.predict_proba(X_scaled)[0]

        success_prob = proba[1]  # Probability of class 1 (success)

        if os.getenv('LOG_ML_FEATURES', '0') == '1':
            logger.info(f"ML Predict features: {row} => success_prob={success_prob:.3f} proba={proba}")

        return {
            'success_probability': float(success_prob),
            'failure_probability': float(proba[0]),
            'confidence': float(max(proba)),  # Confidence is max probability
            'prediction': 'success' if success_prob > 0.5 else 'failure',
            'ml_recommendation': 'TAKE_TRADE' if success_prob > 0.6 else 'SKIP_TRADE'
        }

    def optimize_strategy_weights(self, iterations: int = 100) -> Dict[str, float]:
        """
        Use ML insights to optimize indicator weights.

        Args:
            iterations: Number of optimization iterations

        Returns:
            Optimized weights dictionary
        """
        if self.model is None:
            logger.warning("Model not trained, cannot optimize weights")
            return {
                'rsi': 0.25,
                'macd': 0.25,
                'moving_averages': 0.25,
                'volume': 0.15,
                'trend': 0.10
            }

        # Get feature importance
        importance = dict(zip(self.feature_names, self.model.feature_importances_))

        # Map features to indicators
        indicator_importance = {
            'rsi': importance.get('rsi', 0) + importance.get('rsi_oversold', 0) + importance.get('rsi_overbought', 0),
            'macd': importance.get('macd', 0) + importance.get('macd_hist', 0) + importance.get('macd_bullish', 0),
            'moving_averages': importance.get('sma_short', 0) + importance.get('sma_long', 0) + importance.get('ma_crossover', 0),
            'volume': importance.get('volume_ratio', 0) + importance.get('high_volume', 0),
            'trend': importance.get('trend_uptrend', 0) + importance.get('trend_downtrend', 0) + importance.get('trend_sideways', 0)
        }

        # Normalize to sum to 1.0
        total = sum(indicator_importance.values())
        if total > 0:
            optimized_weights = {k: v / total for k, v in indicator_importance.items()}
        else:
            # Fallback to equal weights
            optimized_weights = {k: 0.2 for k in indicator_importance.keys()}

        logger.info(f"Optimized weights based on feature importance: {optimized_weights}")
        return optimized_weights

    def save_model(self, filename: Optional[str] = None) -> str:
        """
        Save trained model and scaler to disk.

        Args:
            filename: Optional custom filename

        Returns:
            Path to saved model
        """
        if self.model is None:
            raise ValueError("No model to save")

        if filename is None:
            filename = f"trading_model_{self.model_version}.pkl"

        filepath = os.path.join(self.model_dir, filename)

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'version': self.model_version,
            'timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        # Save metadata as JSON
        metadata_path = filepath.replace('.pkl', '_metadata.json')
        metadata = {
            'version': self.model_version,
            'timestamp': datetime.now().isoformat(),
            'feature_names': self.feature_names,
            'feature_count': len(self.feature_names)
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved to {filepath}")
        return filepath

    def load_model(self, filename: Optional[str] = None) -> bool:
        """
        Load trained model from disk.

        Args:
            filename: Optional specific model file to load

        Returns:
            True if successful, False otherwise
        """
        if filename is None:
            # Load most recent model
            model_files = [f for f in os.listdir(self.model_dir) if f.endswith('.pkl')]
            if not model_files:
                logger.warning("No saved models found")
                return False
            filename = sorted(model_files)[-1]

        filepath = os.path.join(self.model_dir, filename)

        if not os.path.exists(filepath):
            logger.warning(f"Model file not found: {filepath}")
            return False

        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)

            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.model_version = model_data.get('version', 'unknown')

            logger.info(f"Model loaded from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def get_feature_insights(self) -> Dict[str, Any]:
        """
        Get insights about which features are most predictive.

        Returns:
            Dictionary with feature analysis
        """
        if self.model is None:
            return {'error': 'Model not trained'}

        importance = dict(zip(self.feature_names, self.model.feature_importances_))
        sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        top_features = list(sorted_importance.items())[:10]

        return {
            'feature_importance': sorted_importance,
            'top_10_features': dict(top_features),
            'most_important_feature': top_features[0][0] if top_features else None,
            'total_features': len(self.feature_names)
        }

    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current ML system metrics for display.
        
        Returns:
            Dictionary with current metrics and parameters
        """
        # Get recent trades for metrics calculation
        recent_trades = self.db.get_trades(limit=100)
        closed_trades = [t for t in recent_trades if t.get('exit_time')]
        
        # Calculate basic metrics
        total_trades = len(closed_trades)
        if total_trades > 0:
            winning_trades = len([t for t in closed_trades if t.get('pnl', 0) > 0])
            win_rate = (winning_trades / total_trades * 100)
            
            # Calculate Sharpe ratio (simplified)
            returns = [t.get('pnl_percent', 0) for t in closed_trades]
            if returns and len(returns) > 1:
                sharpe_ratio = (np.mean(returns) / np.std(returns)) if np.std(returns) > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Model accuracy
            accuracy = self.model.score(self.scaler.transform(
                pd.DataFrame([self._extract_features(t) for t in closed_trades])
            ), [1 if t.get('pnl', 0) > 0 else 0 for t in closed_trades]) * 100 if self.model and total_trades > 10 else 0
        else:
            win_rate = 0
            sharpe_ratio = 0
            accuracy = 0
        
        # Get learning cycles count from database
        learning_cycles = 0
        try:
            perf_records = self.db.get_strategy_performance()
            learning_cycles = len(perf_records)
        except:
            pass
        
        # Get current parameters (from database or defaults)
        current_params = {
            'rsi_period': 14,
            'min_confidence': 0.6,
            'stop_loss': 2.0,
            'take_profit': 5.0
        }
        
        # Last learning time
        last_learning = "Jamais"
        if learning_cycles > 0:
            try:
                latest_perf = self.db.get_strategy_performance(limit=1)
                if latest_perf:
                    timestamp = latest_perf[0].get('timestamp')
                    if timestamp:
                        last_learning = datetime.fromisoformat(timestamp).strftime("%d/%m/%Y %H:%M")
            except:
                pass
        
        return {
            'accuracy': accuracy,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'learning_cycles': learning_cycles,
            'rsi_period': current_params['rsi_period'],
            'min_confidence': current_params['min_confidence'],
            'stop_loss': current_params['stop_loss'],
            'take_profit': current_params['take_profit'],
            'last_learning': last_learning
        }

# Added for PowerShell execution
if __name__ == "__main__":
    import os
    os.environ['FORCE_LEARNING'] = '1'
