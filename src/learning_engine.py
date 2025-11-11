"""
Adaptive Learning Engine - Orchestrates continuous learning and strategy adaptation
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


class AdaptiveLearningEngine:
    """
    Central learning engine that coordinates all learning components.
    Continuously analyzes performance, learns from mistakes, and adapts strategy.
    """

    def __init__(self, db, performance_analyzer, ml_optimizer, config: Dict[str, Any]):
        """
        Initialize learning engine.

        Args:
            db: TradeDatabase instance
            performance_analyzer: PerformanceAnalyzer instance
            ml_optimizer: MLOptimizer instance
            config: Configuration dictionary
        """
        self.db = db
        self.analyzer = performance_analyzer
        self.ml_optimizer = ml_optimizer
        self.config = config

        # Learning state
        self.learning_enabled = True
        self.last_learning_update = None
        self.last_learning_time = None  # Alias pour compatibility
        self.learning_interval_hours = config.get('learning_interval_hours', 24)
        self.min_trades_for_learning = config.get('min_trades_for_learning', 50)
        self.adaptation_aggressiveness = config.get('adaptation_aggressiveness', 'moderate')  # conservative, moderate, aggressive

        # Current optimized parameters
        self.current_weights = config.get('strategy', {}).get('weights', {})
        self.current_min_confidence = config.get('strategy', {}).get('min_confidence', 0.6)

        # Learning history
        self.learning_history = []

        logger.info(f"Adaptive Learning Engine initialized - Learning interval: {self.learning_interval_hours}h")

    def should_trigger_learning(self) -> bool:
        """
        Determine if it's time to trigger a learning cycle.

        Returns:
            True if learning should be triggered
        """
        if not self.learning_enabled:
            return False

        # Forced trigger via ENV (FORCE_LEARNING=1) bypasses checks once per process start
        if os.getenv('FORCE_LEARNING', '0') == '1' and self.last_learning_update is None:
            logger.info("Force learning trigger requested by environment variable FORCE_LEARNING=1")
            return True

        # Check if enough time has passed
        if self.last_learning_update is None:
            # Skip initial learning cycle if we don't have enough trades yet
            stats = self.db.get_performance_stats(days=7)
            if stats['total_trades'] < self.min_trades_for_learning:
                logger.info(
                    f"Skipping initial learning cycle - only {stats['total_trades']} trades (< {self.min_trades_for_learning})"
                )
                # Mark a timestamp so we wait full interval before next attempt
                self.last_learning_update = datetime.now()
                self.last_learning_time = self.last_learning_update  # Sync alias
                return False
            return True

        time_since_last = datetime.now() - self.last_learning_update
        if time_since_last < timedelta(hours=self.learning_interval_hours):
            return False

        # Check if we have enough new trades
        stats = self.db.get_performance_stats(days=7)
        if stats['total_trades'] < self.min_trades_for_learning:
            logger.info(f"Not enough trades for learning: {stats['total_trades']} < {self.min_trades_for_learning}")
            return False

        return True

    def execute_learning_cycle(self) -> Dict[str, Any]:
        """
        Execute a complete learning cycle:
        1. Analyze performance
        2. Identify learning opportunities
        3. Train/update ML model
        4. Optimize strategy parameters
        5. Apply adaptations

        Returns:
            Dictionary with learning results
        """
        start_time = datetime.now()  # Track cycle duration

        logger.info("=" * 60)
        logger.info("STARTING LEARNING CYCLE")
        logger.info("=" * 60)

        results = {
            'timestamp': start_time.isoformat(),
            'success': False,
            'adaptations': [],
            'performance_analysis': {},
            'ml_training': {},
            'errors': [],
            'duration': 0,
            'trades_analyzed': 0
        }

        try:
            # Step 1: Analyze current performance
            logger.info("Step 1: Analyzing performance...")
            performance = self.analyzer.analyze_indicator_performance()
            opportunities = self.analyzer.identify_learning_opportunities()

            # Get number of trades analyzed
            stats = self.db.get_performance_stats(days=7)
            results['trades_analyzed'] = stats.get('total_trades', 0)

            results['performance_analysis'] = {
                'indicator_performance': performance,
                'learning_opportunities': opportunities,
                'opportunity_count': len(opportunities)
            }

            # Step 2: Train/update ML model
            logger.info("Step 2: Training ML model...")
            ml_results = self.ml_optimizer.train_model(model_type='random_forest')

            if ml_results.get('success'):
                results['ml_training'] = ml_results
                self.ml_optimizer.save_model()
                logger.info(f"ML model trained - Accuracy: {ml_results['metrics']['accuracy']:.3f}")
            else:
                logger.warning(f"ML training failed: {ml_results.get('error')}")
                results['errors'].append(f"ML training: {ml_results.get('error')}")

            # Step 3: Calculate optimal weights
            logger.info("Step 3: Optimizing strategy weights...")
            optimal_weights = self._calculate_optimal_weights(performance, ml_results)

            # Step 4: Decide on adaptations
            logger.info("Step 4: Determining adaptations...")
            adaptations = self._determine_adaptations(
                opportunities,
                optimal_weights,
                ml_results
            )

            results['adaptations'] = adaptations

            # Step 5: Apply adaptations (if not in simulation mode)
            if adaptations and self.config.get('auto_apply_adaptations', False):
                logger.info("Step 5: Applying adaptations...")
                self._apply_adaptations(adaptations)
                results['adaptations_applied'] = True
            else:
                logger.info("Step 5: Adaptations calculated but not auto-applied")
                results['adaptations_applied'] = False

            # Record learning event
            self._record_learning_event(results)

            # Calculate cycle duration
            end_time = datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()
            results['duration'] = duration_seconds

            self.last_learning_update = end_time
            self.last_learning_time = self.last_learning_update  # Sync alias
            results['success'] = True

            logger.info(f"LEARNING CYCLE COMPLETED SUCCESSFULLY (duration: {duration_seconds:.1f}s)")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error in learning cycle: {e}", exc_info=True)
            results['errors'].append(str(e))

        return results

    def _calculate_optimal_weights(self, performance: Dict, ml_results: Dict) -> Dict[str, float]:
        """
        Calculate optimal indicator weights combining performance analysis and ML insights.

        Args:
            performance: Performance analysis results
            ml_results: ML training results

        Returns:
            Optimal weights dictionary
        """
        # Get weights from performance analyzer
        perf_weights = self.analyzer.calculate_optimal_weights()

        # Get weights from ML feature importance
        ml_weights = self.ml_optimizer.optimize_strategy_weights() if ml_results.get('success') else {}

        # Combine both approaches (weighted average)
        if ml_weights:
            combined_weights = {}
            for indicator in perf_weights.keys():
                perf_w = perf_weights.get(indicator, 0.2)
                ml_w = ml_weights.get(indicator, 0.2)

                # Weight ML more heavily if model is accurate
                ml_accuracy = ml_results.get('metrics', {}).get('accuracy', 0.5)
                if ml_accuracy > 0.65:
                    combined_weights[indicator] = 0.3 * perf_w + 0.7 * ml_w
                else:
                    combined_weights[indicator] = 0.6 * perf_w + 0.4 * ml_w

            # Normalize
            total = sum(combined_weights.values())
            if total > 0:
                combined_weights = {k: v / total for k, v in combined_weights.items()}

            return combined_weights
        else:
            return perf_weights

    def _determine_adaptations(self, opportunities: List[Dict],
                               optimal_weights: Dict[str, float],
                               ml_results: Dict) -> List[Dict[str, Any]]:
        """
        Determine what adaptations should be made based on learning.

        Args:
            opportunities: Learning opportunities identified
            optimal_weights: Calculated optimal weights
            ml_results: ML training results

        Returns:
            List of adaptation actions
        """
        adaptations = []

        # Check if weights should be updated
        weight_changes = self._calculate_weight_changes(optimal_weights)
        if weight_changes['should_update']:
            adaptations.append({
                'type': 'update_weights',
                'priority': 'high',
                'current_weights': self.current_weights,
                'new_weights': optimal_weights,
                'changes': weight_changes['changes'],
                'reason': 'Optimized based on performance analysis and ML feature importance'
            })

        # Check if confidence threshold should be adjusted
        confidence_adjustment = self._calculate_confidence_adjustment(opportunities, ml_results)
        if confidence_adjustment['should_adjust']:
            adaptations.append({
                'type': 'adjust_confidence',
                'priority': 'medium',
                'current_value': self.current_min_confidence,
                'new_value': confidence_adjustment['new_value'],
                'reason': confidence_adjustment['reason']
            })

        # Process specific learning opportunities
        for opp in opportunities:
            if opp['severity'] == 'high':
                adaptation = self._opportunity_to_adaptation(opp)
                if adaptation:
                    adaptations.append(adaptation)

        logger.info(f"Determined {len(adaptations)} potential adaptations")
        return adaptations

    def _calculate_weight_changes(self, optimal_weights: Dict[str, float]) -> Dict[str, Any]:
        """Calculate if and how much weights should change."""
        changes = {}
        significant_change = False

        # Determine threshold based on aggressiveness
        thresholds = {
            'conservative': 0.10,  # 10% change
            'moderate': 0.05,      # 5% change
            'aggressive': 0.02     # 2% change
        }
        threshold = thresholds.get(self.adaptation_aggressiveness, 0.05)

        for indicator, new_weight in optimal_weights.items():
            current_weight = self.current_weights.get(indicator, 0.2)
            change = new_weight - current_weight
            change_percent = abs(change / current_weight) if current_weight > 0 else 0

            if change_percent > threshold:
                significant_change = True
                changes[indicator] = {
                    'current': current_weight,
                    'new': new_weight,
                    'change': change,
                    'change_percent': change_percent
                }

        return {
            'should_update': significant_change,
            'changes': changes
        }

    def _calculate_confidence_adjustment(self, opportunities: List[Dict],
                                        ml_results: Dict) -> Dict[str, Any]:
        """Calculate if minimum confidence threshold should be adjusted."""
        current_conf = self.current_min_confidence

        # Check for low win rate opportunity
        low_win_rate = any(opp['type'] == 'low_win_rate' for opp in opportunities)

        # Check ML model accuracy
        ml_accuracy = ml_results.get('metrics', {}).get('accuracy', 0.5) if ml_results.get('success') else 0.5

        new_conf = current_conf

        # If win rate is low, increase threshold (be more selective)
        if low_win_rate:
            if self.adaptation_aggressiveness == 'aggressive':
                new_conf = min(0.75, current_conf + 0.05)
            elif self.adaptation_aggressiveness == 'moderate':
                new_conf = min(0.70, current_conf + 0.03)
            else:  # conservative
                new_conf = min(0.65, current_conf + 0.02)

            return {
                'should_adjust': True,
                'new_value': new_conf,
                'reason': 'Win rate is below target - increasing selectivity'
            }

        # If ML model is highly accurate and performing well, can be slightly more aggressive
        if ml_accuracy > 0.75:
            stats = self.db.get_performance_stats(days=14)
            if stats.get('win_rate', 0) > 0.60:
                new_conf = max(0.50, current_conf - 0.02)
                return {
                    'should_adjust': True,
                    'new_value': new_conf,
                    'reason': 'High ML accuracy and good win rate - can be more aggressive'
                }

        return {
            'should_adjust': False,
            'new_value': current_conf,
            'reason': 'No adjustment needed'
        }

    def _opportunity_to_adaptation(self, opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a learning opportunity into an adaptation action."""
        opp_type = opportunity['type']

        if opp_type == 'indicator_optimization':
            return {
                'type': 'adjust_indicator_weight',
                'priority': 'medium',
                'indicator': opportunity['indicator'],
                'action': opportunity['action'],
                'reason': opportunity['recommendation']
            }

        elif opp_type == 'low_profit_factor':
            return {
                'type': 'adjust_risk_reward',
                'priority': 'high',
                'current_value': opportunity['current_value'],
                'target_value': opportunity['target_value'],
                'reason': opportunity['recommendation']
            }

        return None

    def _apply_adaptations(self, adaptations: List[Dict[str, Any]]):
        """
        Apply adaptations to the strategy configuration.

        Args:
            adaptations: List of adaptations to apply
        """
        for adaptation in adaptations:
            try:
                if adaptation['type'] == 'update_weights':
                    self._apply_weight_update(adaptation)
                elif adaptation['type'] == 'adjust_confidence':
                    self._apply_confidence_adjustment(adaptation)
                elif adaptation['type'] == 'adjust_indicator_weight':
                    self._apply_single_weight_adjustment(adaptation)

                logger.info(f"Applied adaptation: {adaptation['type']}")

            except Exception as e:
                logger.error(f"Error applying adaptation {adaptation['type']}: {e}")

    def _apply_weight_update(self, adaptation: Dict[str, Any]):
        """Apply indicator weight updates."""
        old_weights = self.current_weights.copy()
        new_weights = adaptation['new_weights']

        self.current_weights = new_weights

        # Record the change
        self.db.insert_learning_event(
            event_type='weight_update',
            description=f"Updated indicator weights based on performance analysis",
            params_before=old_weights,
            params_after=new_weights,
            reason=adaptation['reason'],
            impact=0.0  # Will be measured in future trades
        )

    def _apply_confidence_adjustment(self, adaptation: Dict[str, Any]):
        """Apply confidence threshold adjustment."""
        old_value = self.current_min_confidence
        new_value = adaptation['new_value']

        self.current_min_confidence = new_value

        self.db.insert_learning_event(
            event_type='confidence_adjustment',
            description=f"Adjusted minimum confidence from {old_value:.2f} to {new_value:.2f}",
            params_before={'min_confidence': old_value},
            params_after={'min_confidence': new_value},
            reason=adaptation['reason'],
            impact=abs(new_value - old_value)
        )

    def _apply_single_weight_adjustment(self, adaptation: Dict[str, Any]):
        """Apply single indicator weight adjustment."""
        indicator = adaptation['indicator']
        # Adjust weight slightly based on recommendation
        # This is a simplified version - could be more sophisticated

        logger.info(f"Adjustment recommended for {indicator}: {adaptation['reason']}")

    def _record_learning_event(self, results: Dict[str, Any]):
        """Record the learning cycle in history."""
        event = {
            'timestamp': results['timestamp'],
            'success': results['success'],
            'adaptations_count': len(results.get('adaptations', [])),
            'ml_accuracy': results.get('ml_training', {}).get('metrics', {}).get('accuracy'),
            'opportunities_identified': results.get('performance_analysis', {}).get('opportunity_count', 0)
        }

        self.learning_history.append(event)

        # Keep only last 100 learning events
        if len(self.learning_history) > 100:
            self.learning_history = self.learning_history[-100:]

    def get_ml_enhanced_signal_confidence(self, signal: Dict[str, Any],
                                         market_conditions: Dict[str, Any]) -> float:
        """
        Enhance signal confidence using ML prediction.

        Args:
            signal: Original signal from signal generator
            market_conditions: Current market indicators

        Returns:
            ML-enhanced confidence score
        """
        original_confidence = signal.get('confidence', 0.5)

        # Get ML prediction
        ml_prediction = self.ml_optimizer.predict_trade_success(market_conditions)

        if ml_prediction.get('prediction') == 'unknown':
            # Model not ready, use original confidence
            return original_confidence

        ml_success_prob = ml_prediction['success_probability']

        # Combine original confidence with ML prediction
        # Give more weight to ML if it's confident
        ml_confidence = ml_prediction['confidence']

        if ml_confidence > 0.7:
            # High ML confidence - weight it heavily
            enhanced_confidence = 0.4 * original_confidence + 0.6 * ml_success_prob
        elif ml_confidence > 0.6:
            # Medium ML confidence - balanced weight
            enhanced_confidence = 0.6 * original_confidence + 0.4 * ml_success_prob
        else:
            # Low ML confidence - prefer original
            enhanced_confidence = 0.8 * original_confidence + 0.2 * ml_success_prob

        logger.debug(f"Enhanced confidence: {original_confidence:.3f} -> {enhanced_confidence:.3f} (ML: {ml_success_prob:.3f})")

        return enhanced_confidence

    def get_current_strategy_params(self) -> Dict[str, Any]:
        """
        Get current optimized strategy parameters.

        Returns:
            Dictionary with current parameters
        """
        return {
            'weights': self.current_weights,
            'min_confidence': self.current_min_confidence,
            'learning_enabled': self.learning_enabled,
            'last_update': self.last_learning_update.isoformat() if self.last_learning_update else None
        }

    def generate_learning_report(self) -> str:
        """
        Generate a human-readable learning report.

        Returns:
            Formatted report string
        """
        report = "\n" + "=" * 60 + "\n"
        report += "ADAPTIVE LEARNING SYSTEM REPORT\n"
        report += "=" * 60 + "\n\n"

        report += f"Learning Status: {'ENABLED' if self.learning_enabled else 'DISABLED'}\n"
        report += f"Last Update: {self.last_learning_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_learning_update else 'Never'}\n"
        report += f"Learning Cycles Completed: {len(self.learning_history)}\n\n"

        report += "Current Strategy Parameters:\n"
        report += f"  Minimum Confidence: {self.current_min_confidence:.2f}\n"
        report += "  Indicator Weights:\n"
        for indicator, weight in self.current_weights.items():
            report += f"    {indicator}: {weight:.3f}\n"

        if self.learning_history:
            recent = self.learning_history[-1]
            report += f"\nMost Recent Learning Cycle:\n"
            report += f"  Timestamp: {recent['timestamp']}\n"
            report += f"  Success: {recent['success']}\n"
            report += f"  Adaptations: {recent['adaptations_count']}\n"
            if recent.get('ml_accuracy'):
                report += f"  ML Accuracy: {recent['ml_accuracy']:.3f}\n"

        report += "\n" + "=" * 60 + "\n"

        return report

    def enable_learning(self):
        """Enable adaptive learning."""
        self.learning_enabled = True
        logger.info("Adaptive learning ENABLED")

    def disable_learning(self):
        """Disable adaptive learning."""
        self.learning_enabled = False
        logger.info("Adaptive learning DISABLED")
