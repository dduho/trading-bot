"""
Trading Bot - Main Orchestrator
Coordinates all components and executes the trading strategy
"""

import asyncio
import yaml
import os
import sys
import threading

# Fix encoding pour Windows - SIMPLIFIE
if sys.platform == 'win32':
    # Ignorer les erreurs d'encodage plutôt que de crasher
    import warnings
    warnings.filterwarnings('ignore', category=UnicodeWarning)

from datetime import datetime
from typing import Dict, List
import logging
from colorama import Fore, Style, init

from market_data import MarketDataFeed
from technical_analysis import TechnicalAnalyzer
from signal_generator import SignalGenerator, Signal
from risk_manager import RiskManager
from order_executor import OrderExecutor, TradingMode
from trade_database import TradeDatabase
from performance_analyzer import PerformanceAnalyzer
from ml_optimizer import MLOptimizer
from learning_engine import AdaptiveLearningEngine
from telegram_notifier import TelegramNotifier
from telegram_commands import TelegramCommandHandler

# Initialize colorama for colored output
init(autoreset=True)

# Setup logging - SIMPLIFIE
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log', encoding='utf-8', errors='ignore'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot that orchestrates all components"""

    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize trading bot

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.running = False
        self.start_time = datetime.now()  # Pour calcul uptime

        # Get trading mode from environment
        mode_str = os.getenv('TRADING_MODE', 'paper').lower()
        self.trading_mode = self._parse_trading_mode(mode_str)

        # Get API credentials
        api_key = os.getenv('API_KEY')
        api_secret = os.getenv('API_SECRET')

        # Initialize market data feed
        exchange_name = os.getenv('EXCHANGE', 'binance')
        self.market_feed = MarketDataFeed(
            exchange_name=exchange_name,
            api_key=api_key,
            api_secret=api_secret,
            testnet=(self.trading_mode == TradingMode.TESTNET),
            trading_mode=mode_str
        )

        # Initialize order executor
        self.executor = OrderExecutor(
            exchange=self.market_feed.exchange,
            mode=self.trading_mode
        )

        # Initialize analysis components
        self.analyzer = TechnicalAnalyzer(self.config.get('indicators', {}))
        self.signal_generator = SignalGenerator(self.config.get('strategy', {}))
        self.risk_manager = RiskManager(
            self.config.get('risk', {}),
            trading_mode=self.trading_mode.value
        )

        # Initialize learning system
        learning_config = self.config.get('learning', {
            'enabled': True,
            'learning_interval_hours': 24,
            'min_trades_for_learning': 50,
            'adaptation_aggressiveness': 'moderate',
            'auto_apply_adaptations': False
        })
        # Ensure learning engine sees the same strategy parameters used by SignalGenerator
        # so it reports consistent min_confidence and weights
        if 'strategy' in self.config:
            learning_config = {**learning_config, 'strategy': self.config.get('strategy', {})}

        self.trade_db = TradeDatabase()
        self.perf_analyzer = PerformanceAnalyzer(self.trade_db)
        self.ml_optimizer = MLOptimizer(self.trade_db, config=self.config)
        self.learning_engine = AdaptiveLearningEngine(
            self.trade_db,
            self.perf_analyzer,
            self.ml_optimizer,
            learning_config
        )

        # Initialize Intelligent Filter (reduce bad trades)
        from intelligent_filter import IntelligentFilter
        self.intelligent_filter = IntelligentFilter(self.trade_db, self.config)
        logger.info("🧠 Intelligent Filter initialized - Quality-focused trading ACTIVE")

        # Initialize Enhanced Strategy (improved win rate through better analysis)
        from enhanced_strategy import EnhancedStrategy
        self.enhanced_strategy = EnhancedStrategy(self.config)
        logger.info("🚀 Enhanced Strategy initialized - Advanced market analysis ACTIVE")

        # Initialize Professional Strategy (world-class trading system)
        from professional_strategy import ProfessionalStrategy
        self.professional_strategy = ProfessionalStrategy(self.config, market_feed=self.market_feed)
        logger.info("⭐ Professional Strategy initialized - Multi-timeframe analysis enabled!")

        # Initialize Ranging Strategy (for sideways/choppy markets)
        from ranging_strategy import RangingStrategy
        self.ranging_strategy = RangingStrategy(self.config)
        logger.info("🔄 Ranging Strategy initialized - Mean reversion mode ready!")

        # Initialize Autonomous Watchdog (self-healing system)
        try:
            from autonomous_watchdog import AutonomousWatchdog
            self.watchdog = AutonomousWatchdog(self.trade_db, self.config, self.risk_manager)
            logger.info("🤖 Autonomous Watchdog enabled - Self-healing mode ACTIVE")
        except Exception as e:
            logger.error(f"Failed to initialize Autonomous Watchdog: {e}")
            self.watchdog = None

        # Initialize Telegram notifications
        try:
            if self.config.get('notifications', {}).get('telegram', {}).get('enabled', False):
                self.telegram = TelegramNotifier(self.config)
                logger.info("Telegram notifications enabled")
            else:
                self.telegram = None
                logger.info("Telegram notifications disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize Telegram notifications: {e}")
            self.telegram = None

        # Event loop dédié pour notifications dans un thread daemon
        self._notification_loop = None
        self._start_notification_loop()

        # Initialize Telegram commands (interactive)
        self.telegram_commands = None
        try:
            if self.config.get('notifications', {}).get('telegram', {}).get('enabled', False):
                self.telegram_commands = TelegramCommandHandler(self.config, self)
                logger.info("Telegram commands handler initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Telegram commands: {e}")

        # Trading state
        self.symbols = self.config.get('symbols', ['BTC/USDT'])
        self.timeframe = os.getenv('TIMEFRAME', '1m')
        # Intervalle de scan rapide pour trading actif (15 secondes)
        self.update_interval = int(os.getenv('UPDATE_INTERVAL', '15'))

        # Get initial capital
        if self.trading_mode == TradingMode.PAPER:
            self.capital = 10000  # Default paper trading capital
        else:
            # Get real balance
            balance = self.executor.get_balance()
            self.capital = balance.get('total', {}).get('USDT', 0)

        self._print_initialization_message()
        logger.info(f"Trading Bot initialized with {len(self.symbols)} symbols in {self.trading_mode.value.upper()} mode")
        
        # Restaurer les positions ouvertes depuis la base de données
        self._restore_open_positions()

    def _restore_open_positions(self):
        """Restore open positions from database on startup"""
        try:
            open_trades = self.trade_db.get_trade_history(limit=100, status='open')

            if open_trades:
                max_positions = self.config.get('risk', {}).get('max_open_positions', 3)

                # CRITICAL FIX: Respect max_open_positions limit when restoring
                if len(open_trades) > max_positions:
                    logger.warning(f"⚠️ Found {len(open_trades)} open positions in DB, but max is {max_positions}")
                    logger.warning(f"   Will close excess positions to respect risk limits")

                    # Sort by entry_time (keep oldest positions)
                    open_trades_sorted = sorted(open_trades, key=lambda x: x['entry_time'])

                    # Close excess positions
                    for i, trade in enumerate(open_trades_sorted):
                        if i >= max_positions:
                            # Mark as closed in DB
                            logger.info(f"   Closing excess position: {trade['symbol']}")
                            try:
                                self.trade_db.update_trade(trade['id'], {
                                    'status': 'closed',
                                    'exit_reason': 'Excess position cleanup (max_open_positions exceeded)',
                                    'exit_time': datetime.now()
                                })
                            except Exception as e:
                                logger.error(f"   Failed to close {trade['symbol']}: {e}")

                    # Keep only first max_positions
                    open_trades = open_trades_sorted[:max_positions]

                logger.info(f"🔄 Restoring {len(open_trades)} open positions from database...")

                for trade in open_trades:
                    # Recréer l'objet Position
                    from risk_manager import Position
                    position = Position(
                        symbol=trade['symbol'],
                        side=trade['side'],
                        entry_price=trade['entry_price'],
                        quantity=trade['quantity'],
                        stop_loss=trade.get('stop_loss'),
                        take_profit=trade.get('take_profit')
                    )
                    position.trade_id = trade['id']
                    position.entry_time = datetime.fromisoformat(trade['entry_time'])

                    # Ajouter au risk manager
                    self.risk_manager.positions[trade['symbol']] = position

                logger.info(f"✅ Restored {len(open_trades)} positions: {list(self.risk_manager.positions.keys())}")
            else:
                logger.info("ℹ️  No open positions to restore")

        except Exception as e:
            logger.error(f"❌ Error restoring positions: {e}", exc_info=True)

    def _parse_trading_mode(self, mode_str: str) -> TradingMode:
        """Parse trading mode string to TradingMode enum"""
        mode_map = {
            'paper': TradingMode.PAPER,
            'testnet': TradingMode.TESTNET,
            'live': TradingMode.LIVE
        }
        return mode_map.get(mode_str, TradingMode.PAPER)
    
    def _start_notification_loop(self):
        """Démarrer un event loop dédié pour les notifications dans un thread daemon"""
        def run_loop():
            try:
                self._notification_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._notification_loop)
                logger.info("📡 Notification event loop started in daemon thread")
                self._notification_loop.run_forever()
            except Exception as e:
                logger.error(f"Notification loop error: {e}", exc_info=True)
        
        thread = threading.Thread(target=run_loop, daemon=True, name="notification-loop")
        thread.start()
        # Attendre que le loop soit prêt
        import time
        time.sleep(0.1)
    
    def _send_telegram_notification(self, coro):
        """Helper pour envoyer une notification Telegram de manière synchrone"""
        if not self.telegram or not self._notification_loop:
            return
        
        try:
            logger.info("📤 Tentative d'envoi notification Telegram...")
            
            # Soumettre la coroutine au loop dédié
            future = asyncio.run_coroutine_threadsafe(coro, self._notification_loop)
            
            # Attendre max 5 secondes
            future.result(timeout=5)
            logger.info("✅ Notification Telegram envoyée avec succès")
            
        except TimeoutError:
            logger.warning("⚠️ Notification Telegram timeout (>5s)")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram notification: {e}", exc_info=True)

    def _print_initialization_message(self):
        """Print initialization message with warnings"""
        if self.trading_mode == TradingMode.LIVE:
            print(f"\n{Fore.RED}{'='*80}")
            print(f"⚠️  WARNING: LIVE TRADING MODE - REAL MONEY AT RISK! ⚠️")
            print(f"{'='*80}{Style.RESET_ALL}\n")
            print(f"{Fore.YELLOW}This bot will execute REAL trades with REAL money!")
            print(f"Make sure you understand the risks and have tested your strategy.")
            print(f"Capital available: ${self.capital:.2f} USDT{Style.RESET_ALL}\n")
        elif self.trading_mode == TradingMode.TESTNET:
            print(f"\n{Fore.CYAN}{'='*80}")
            print(f"📝 TESTNET MODE - Using exchange testnet/sandbox")
            print(f"{'='*80}{Style.RESET_ALL}\n")
            print(f"This mode uses the exchange's testnet with fake money.")
            print(f"Orders are real API calls but with test funds.\n")
        else:
            print(f"\n{Fore.GREEN}{'='*80}")
            print(f"📝 PAPER TRADING MODE - Simulation only")
            print(f"{'='*80}{Style.RESET_ALL}\n")
            print(f"This is a safe simulation mode. No real orders will be executed.")
            print(f"Starting capital: ${self.capital:.2f} USDT\n")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.warning(f"Could not load config: {e}. Using defaults.")
            return {}

    def _timeframe_to_seconds(self, timeframe: str) -> int:
        """Convert timeframe to seconds"""
        mapping = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        return mapping.get(timeframe, 60)

    def analyze_symbol(self, symbol: str) -> Dict:
        """
        Analyze a symbol and generate trading signal

        Args:
            symbol: Trading pair to analyze

        Returns:
            Analysis results with signal
        """
        try:
            # Get market data
            df = self.market_feed.get_ohlcv(symbol, self.timeframe, limit=100)
            if df.empty:
                logger.warning(f"No data for {symbol}")
                return {}

            # Calculate technical indicators
            df_with_indicators = self.analyzer.get_all_indicators(df)

            # Analyze market regime (trending/ranging/transitional)
            market_regime = self.enhanced_strategy.analyze_market_regime(df_with_indicators)

            # Generate trading signal
            signal_result = self.signal_generator.generate_signal(df_with_indicators)

            # Get market summary
            market_summary = self.analyzer.get_market_summary(df_with_indicators)

            # Enhance signal with ML prediction if available
            latest_row = df_with_indicators.iloc[-1]
            market_conditions = {
                'rsi': latest_row.get('rsi'),
                'macd': latest_row.get('macd'),
                'macd_signal': latest_row.get('macd_signal'),
                'macd_hist': latest_row.get('macd_hist'),
                'sma_short': latest_row.get('sma_short'),
                'sma_long': latest_row.get('sma_long'),
                'ema_short': latest_row.get('ema_short'),
                'ema_long': latest_row.get('ema_long'),
                'bb_upper': latest_row.get('bb_upper'),
                'bb_middle': latest_row.get('bb_middle'),
                'bb_lower': latest_row.get('bb_lower'),
                'atr': latest_row.get('atr'),
                'volume': latest_row.get('volume'),
                'volume_ratio': latest_row.get('volume_ratio'),
                'trend': market_summary.get('trend'),
                'signal_confidence': signal_result.get('confidence'),
                'close': latest_row.get('close')
            }

            # Enhance confidence with ML (DÉSACTIVÉ en phase apprentissage)
            # Le ML avec win rate < 40% prédit toujours échec et bloque les trades
            # On réactive quand le ML devient fiable (win rate > 40%)
            stats = self.trade_db.get_performance_stats(days=7)
            win_rate = stats.get('win_rate', 0)

            if win_rate > 0.40:
                # ML fiable → Utilise enhancement
                ml_enhanced_confidence = self.learning_engine.get_ml_enhanced_signal_confidence(
                    signal_result, market_conditions
                )
                signal_result['ml_enhanced_confidence'] = ml_enhanced_confidence
                signal_result['original_confidence'] = signal_result['confidence']
                signal_result['confidence'] = ml_enhanced_confidence
                logger.debug(f"ML enhancement: {signal_result['original_confidence']:.2%} → {ml_enhanced_confidence:.2%}")
            else:
                # ML pas fiable → Garde confidence originale
                signal_result['ml_enhanced_confidence'] = signal_result['confidence']
                signal_result['original_confidence'] = signal_result['confidence']
                logger.debug(f"ML enhancement DISABLED (WR {win_rate:.1%} < 40%) - using original confidence")

            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price': df['close'].iloc[-1],
                'signal': signal_result,
                'market': market_summary,
                'market_regime': market_regime,
                'dataframe': df_with_indicators,
                'market_conditions': market_conditions
            }

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {}

    def execute_signal(self, analysis: Dict):
        """
        Execute trading signal (with real orders if not in paper mode)

        Args:
            analysis: Analysis results from analyze_symbol
        """
        logger.info(f"✅ DEBUG: execute_signal CALLED - analysis={bool(analysis)}, has_signal={'signal' in analysis if analysis else False}")

        if not analysis or 'signal' not in analysis:
            logger.warning(f"⚠️ DEBUG: execute_signal RETURNING EARLY - analysis={bool(analysis)}")
            return

        symbol = analysis['symbol']
        signal = analysis['signal']
        price = analysis['price']

        logger.info(f"📊 DEBUG: execute_signal processing {symbol} {signal['action']} (confidence: {signal['confidence']:.2%})")

        # Intelligent Filter: Skip low-quality setups
        should_trade, filter_reason = self.intelligent_filter.should_take_trade(
            signal,
            analysis.get('market_conditions', {}),
            symbol
        )
        if not should_trade:
            logger.info(f"🧠 FILTERED OUT: {symbol} - {filter_reason}")
            return

        # Enhanced Strategy: Regime-based filtering
        market_regime = analysis.get('market_regime', {})
        df = analysis.get('dataframe')
        should_trade_regime, regime_reason = self.enhanced_strategy.should_take_trade(
            signal, df, market_regime
        )
        if not should_trade_regime:
            logger.info(f"🎯 REGIME FILTER: {symbol} - {regime_reason}")
            return

        # ADAPTIVE STRATEGY: Auto-detect market regime and use appropriate strategy
        # Detect if market is trending or ranging
        regime_type = self.ranging_strategy.analyze_market_regime(df) if df is not None else 'unknown'
        use_ranging_strategy = regime_type in ['ranging', 'choppy']  # Store for later use in stops calculation

        if use_ranging_strategy:
            # Use RANGING strategy for sideways/choppy markets
            logger.info(f"🔄 Market regime: {regime_type.upper()} - Using Ranging Strategy (mean reversion)")

            # Check if ranging strategy approves this trade
            indicators = analysis.get('indicators', {})
            if signal['action'] == 'BUY':
                should_enter, reason, _ = self.ranging_strategy.should_enter_long(df, indicators)
            elif signal['action'] == 'SELL':
                should_enter, reason, _ = self.ranging_strategy.should_enter_short(df, indicators)
            else:
                should_enter = False
                reason = "HOLD signal - no ranging entry"

            logger.info(f"🔄 RANGING FILTER: {symbol} - {'✅ APPROVED' if should_enter else '⛔ REJECTED'}: {reason}")
            if not should_enter:
                return

        else:
            # Use PROFESSIONAL strategy for trending markets
            logger.info(f"📈 Market regime: {regime_type.upper()} - Using Professional Strategy (trend following)")
            should_trade_pro, pro_reasoning = self.professional_strategy.should_take_trade(
                signal['action'], df, market_regime, symbol=symbol
            )
            # ALWAYS log the PRO FILTER decision (accept OR reject)
            logger.info(f"⭐ PRO FILTER: {symbol} - {pro_reasoning}")
            if not should_trade_pro:
                return

        # Check if we can open a position
        market_context = analysis.get('market_conditions', {}) or {}
        can_open, reason = self.risk_manager.can_open_position(
            symbol,
            market_context=market_context,
            current_equity=self.capital,
            current_price=price
        )
        logger.info(f"🔓 DEBUG: can_open={can_open}, reason={reason}")

        # BUY signal
        # If a SHORT is open for this symbol, close it on BUY
        if signal['action'] == 'BUY' and symbol in self.risk_manager.positions:
            existing = self.risk_manager.positions[symbol]
            if existing.side == 'short':
                # PROFIT PROTECTION: Don't close profitable SHORT positions too early
                # For SHORT: profit when price goes DOWN
                current_pnl_pct = (existing.entry_price - price) / existing.entry_price * 100
                min_profit_to_close = 4.0  # Don't close until at least 4% profit

                if current_pnl_pct > 0 and current_pnl_pct < min_profit_to_close:
                    logger.info(f"🔒 Keeping {symbol} SHORT open - only {current_pnl_pct:.2f}% profit (target: {min_profit_to_close}%)")
                    return

                # Buy to cover
                order = None
                order_type = self.config.get('execution', {}).get('order_type', 'market')
                if order_type == 'market':
                    order = self.executor.create_market_order(symbol, 'buy', existing.quantity)
                else:
                    order = self.executor.create_limit_order(symbol, 'buy', existing.quantity, price)

                if order:
                    actual_price = order.get('price', price)
                    closed = self.risk_manager.close_position(symbol, actual_price, "Signal: BUY (close short)")
                    if closed:
                        self._print_close(symbol, actual_price, closed.pnl, "BUY Signal (close short)")

                        if hasattr(existing, 'trade_id'):
                            duration_minutes = (datetime.now() - closed.entry_time).total_seconds() / 60
                            pnl_percent = (closed.pnl / (closed.entry_price * closed.quantity)) * 100 if closed.entry_price * closed.quantity != 0 else 0
                            self.trade_db.update_trade(existing.trade_id, {
                                'exit_price': actual_price,
                                'exit_time': datetime.now(),
                                'pnl': closed.pnl,
                                'pnl_percent': pnl_percent,
                                'status': 'closed',
                                'exit_reason': 'Signal: BUY (close short)',
                                'duration_minutes': duration_minutes
                            })
                return

        if signal['action'] == 'BUY' and can_open:
            # Calculate position parameters based on active strategy
            if use_ranging_strategy:
                # RANGING: Use Bollinger Bands for stops (mean reversion)
                stop_loss, take_profit = self.ranging_strategy.calculate_ranging_stops(df, 'long', price)
            else:
                # PROFESSIONAL: Use market structure for stops (trend following)
                market_structure = self.professional_strategy.analyze_market_structure(df)
                stop_loss, take_profit = self.professional_strategy.calculate_professional_stops(
                    df, 'long', price, market_structure
                )

            # Calculate position size with intelligent sizing based on setup quality
            base_quantity = self.risk_manager.calculate_position_size(
                capital=self.capital,
                risk_percent=self.config['risk']['stop_loss_percent'],
                entry_price=price,
                stop_loss=stop_loss
            )

            # Apply size multiplier from professional strategy (bigger size for better setups)
            size_multiplier = getattr(self.professional_strategy, 'last_size_multiplier', 1.0)
            quantity = base_quantity * size_multiplier
            logger.info(f"📏 Position sizing: base={base_quantity:.6f}, multiplier={size_multiplier:.1f}x, final={quantity:.6f}")

            # Validate order before execution
            is_valid, error_msg = self.executor.validate_order(symbol, 'buy', quantity, price)
            if not is_valid:
                logger.warning(f"Order validation failed: {error_msg}")
                return

            # Execute the BUY order
            order = None
            order_type = self.config.get('execution', {}).get('order_type', 'market')

            if order_type == 'market':
                order = self.executor.create_market_order(symbol, 'buy', quantity)
            else:  # limit order
                order = self.executor.create_limit_order(symbol, 'buy', quantity, price)

            if order:
                # Order executed successfully - track position
                actual_price = order.get('price', price)

                # Position metadata for smarter risk controls
                expected_rr = abs(take_profit - actual_price) / abs(actual_price - stop_loss) if stop_loss and take_profit else None
                position_meta = {
                    **market_context,
                    'expected_rr': expected_rr,
                    'trend_bias': market_regime.get('trend') if market_regime else None,
                    'atr': market_context.get('atr'),
                    'max_duration_minutes': self.config.get('risk', {}).get('max_position_duration_minutes')
                }

                position = self.risk_manager.open_position(
                    symbol=symbol,
                    side='long',
                    entry_price=actual_price,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    meta=position_meta,
                    current_equity=self.capital
                )

                if position:
                    self._print_trade(
                        "BUY",
                        symbol,
                        actual_price,
                        quantity,
                        signal['confidence'],
                        signal['reason'],
                        stop_loss,
                        take_profit
                    )

                    # Record trade in database for learning
                    trade_id = self.trade_db.insert_trade({
                        'symbol': symbol,
                        'side': 'long',
                        'entry_price': actual_price,
                        'quantity': quantity,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'entry_time': datetime.now(),
                        'status': 'open',
                        'trading_mode': self.trading_mode.value
                    })

                    # Record market conditions at entry
                    if 'market_conditions' in analysis:
                        conditions = analysis['market_conditions'].copy()
                        conditions['timestamp'] = datetime.now()
                        conditions['signal_reason'] = signal['reason']
                        self.trade_db.insert_trade_conditions(trade_id, conditions)

                    # Store trade_id in position for later updates
                    position.trade_id = trade_id

                    # Send Telegram notification for position opened
                    if self.telegram:
                        self._send_telegram_notification(
                            self.telegram.send_trade_notification(
                                action='OPEN',
                                symbol=symbol,
                                side='BUY',
                                entry_price=actual_price,
                                quantity=quantity,
                                position_value=actual_price * quantity,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                signal_data={
                                    'confidence': signal['confidence'],
                                    'action': signal['action'],
                                    'rsi': analysis.get('market_conditions', {}).get('rsi'),
                                    'macd': analysis.get('market_conditions', {}).get('macd'),
                                    'ema': analysis.get('market_conditions', {}).get('ema_short'),
                                    'sma': analysis.get('market_conditions', {}).get('sma_short'),
                                    'volume_change': analysis.get('market_conditions', {}).get('volume_ratio', 0) * 100 - 100
                                },
                                portfolio_info=self._get_portfolio_info()
                            )
                        )

                    # Place stop loss and take profit orders (if not paper mode)
                    if self.trading_mode != TradingMode.PAPER:
                        # Stop loss order
                        self.executor.create_stop_loss_order(symbol, 'sell', quantity, stop_loss)

                        # Take profit order (limit sell)
                        self.executor.create_limit_order(symbol, 'sell', quantity, take_profit)

            else:
                logger.error(f"Failed to execute BUY order for {symbol}")

        # SELL signal - close existing LONG; maintain SHORTs (opened on SELL)
        elif signal['action'] == 'SELL' and symbol in self.risk_manager.positions:
            position = self.risk_manager.positions[symbol]

            # If we are LONG, SELL to close. If already SHORT, maintain position on SELL.
            if position.side == 'short':
                logger.info(f"Maintaining existing SHORT on {symbol}; SELL signal reaffirmed.")
                return

            # PROFIT PROTECTION: Don't close profitable positions too early
            # Calculate current PnL %
            current_pnl_pct = (price - position.entry_price) / position.entry_price * 100
            min_profit_to_close = 4.0  # Don't close until at least 4% profit

            if current_pnl_pct > 0 and current_pnl_pct < min_profit_to_close:
                logger.info(f"🔒 Keeping {symbol} LONG open - only {current_pnl_pct:.2f}% profit (target: {min_profit_to_close}%)")
                return

            # Execute the SELL order to close LONG
            order = None
            order_type = self.config.get('execution', {}).get('order_type', 'market')

            if order_type == 'market':
                order = self.executor.create_market_order(symbol, 'sell', position.quantity)
            else:  # limit order
                order = self.executor.create_limit_order(symbol, 'sell', position.quantity, price)

            if order:
                actual_price = order.get('price', price)

                # Cancel any open stop/tp orders for this symbol
                if self.trading_mode != TradingMode.PAPER:
                    open_orders = self.executor.get_open_orders(symbol)
                    for open_order in open_orders:
                        self.executor.cancel_order(open_order['id'], symbol)

                # Close position tracking
                closed = self.risk_manager.close_position(symbol, actual_price, "Signal: SELL (close long)")
                if closed:
                    self._print_close(symbol, actual_price, closed.pnl, "SELL Signal (close long)")

                    # Update trade in database
                    if hasattr(position, 'trade_id'):
                        duration_minutes = (datetime.now() - closed.entry_time).total_seconds() / 60
                        denom = (closed.entry_price * closed.quantity)
                        pnl_percent = (closed.pnl / denom * 100) if denom else 0

                        self.trade_db.update_trade(position.trade_id, {
                            'exit_price': actual_price,
                            'exit_time': datetime.now(),
                            'pnl': closed.pnl,
                            'pnl_percent': pnl_percent,
                            'status': 'closed',
                            'exit_reason': 'Signal: SELL (close long)',
                            'duration_minutes': duration_minutes
                        })

                        # Send Telegram notification for position closed
                        if self.telegram:
                            self._send_telegram_notification(
                                self.telegram.send_trade_notification(
                                    action='CLOSE',
                                    symbol=symbol,
                                    side='SELL',
                                    entry_price=closed.entry_price,
                                    exit_price=actual_price,
                                    quantity=closed.quantity,
                                    pnl=closed.pnl,
                                    pnl_percent=pnl_percent,
                                    duration=self._format_duration(duration_minutes),
                                    reason='Signal: SELL (close long)',
                                    portfolio_info=self._get_portfolio_info()
                                )
                            )
            else:
                logger.error(f"Failed to execute SELL order for {symbol}")

        # If SELL and no position open, open SHORT (paper synthetic)
        elif signal['action'] == 'SELL' and can_open:
            # Calculate position parameters based on active strategy
            if use_ranging_strategy:
                # RANGING: Use Bollinger Bands for stops (mean reversion)
                stop_loss, take_profit = self.ranging_strategy.calculate_ranging_stops(df, 'short', price)
            else:
                # PROFESSIONAL: Use market structure for stops (trend following)
                market_structure = self.professional_strategy.analyze_market_structure(df)
                stop_loss, take_profit = self.professional_strategy.calculate_professional_stops(
                    df, 'short', price, market_structure
                )

            # Calculate position size with intelligent sizing
            base_quantity = self.risk_manager.calculate_position_size(
                capital=self.capital,
                risk_percent=self.config['risk']['stop_loss_percent'],
                entry_price=price,
                stop_loss=stop_loss
            )

            # Apply size multiplier from professional strategy
            size_multiplier = getattr(self.professional_strategy, 'last_size_multiplier', 1.0)
            quantity = base_quantity * size_multiplier
            logger.info(f"📏 Position sizing: base={base_quantity:.6f}, multiplier={size_multiplier:.1f}x, final={quantity:.6f}")

            is_valid, error_msg = self.executor.validate_order(symbol, 'sell', quantity, price)
            if not is_valid:
                logger.warning(f"Order validation failed (short): {error_msg}")
                return

            order = None
            order_type = self.config.get('execution', {}).get('order_type', 'market')
            if order_type == 'market':
                order = self.executor.create_market_order(symbol, 'sell', quantity)
            else:
                order = self.executor.create_limit_order(symbol, 'sell', quantity, price)

            if order:
                actual_price = order.get('price', price)

                expected_rr = abs(take_profit - actual_price) / abs(actual_price - stop_loss) if stop_loss and take_profit else None
                position_meta = {
                    **market_context,
                    'expected_rr': expected_rr,
                    'trend_bias': market_regime.get('trend') if market_regime else None,
                    'atr': market_context.get('atr'),
                    'max_duration_minutes': self.config.get('risk', {}).get('max_position_duration_minutes')
                }

                position = self.risk_manager.open_position(
                    symbol=symbol,
                    side='short',
                    entry_price=actual_price,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    meta=position_meta,
                    current_equity=self.capital
                )

                if position:
                    self._print_trade(
                        "SELL",
                        symbol,
                        actual_price,
                        quantity,
                        signal['confidence'],
                        signal['reason'],
                        stop_loss,
                        take_profit
                    )

                    trade_id = self.trade_db.insert_trade({
                        'symbol': symbol,
                        'side': 'short',
                        'entry_price': actual_price,
                        'quantity': quantity,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'entry_time': datetime.now(),
                        'status': 'open',
                        'trading_mode': self.trading_mode.value
                    })

                    if 'market_conditions' in analysis:
                        conditions = analysis['market_conditions'].copy()
                        conditions['timestamp'] = datetime.now()
                        conditions['signal_reason'] = signal['reason']
                        self.trade_db.insert_trade_conditions(trade_id, conditions)

                    position.trade_id = trade_id
                    
                    # Send Telegram notification for SHORT position opened
                    if self.telegram:
                        self._send_telegram_notification(
                            self.telegram.send_trade_notification(
                                action='OPEN',
                                symbol=symbol,
                                side='SELL',
                                entry_price=actual_price,
                                quantity=quantity,
                                position_value=actual_price * quantity,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                signal_data={
                                    'confidence': signal['confidence'],
                                    'action': signal['action'],
                                    'rsi': analysis.get('market_conditions', {}).get('rsi'),
                                    'macd': analysis.get('market_conditions', {}).get('macd'),
                                    'ema': analysis.get('market_conditions', {}).get('ema_short'),
                                    'sma': analysis.get('market_conditions', {}).get('sma_short'),
                                    'volume_change': analysis.get('market_conditions', {}).get('volume_ratio', 0) * 100 - 100
                                },
                                portfolio_info=self._get_portfolio_info()
                            )
                        )
            else:
                logger.error(f"Failed to execute SHORT SELL order for {symbol}")

    def update_positions(self):
        """Update all open positions and check stops"""
        if not self.risk_manager.positions:
            return

        # Get current prices
        prices = {}
        for symbol in self.risk_manager.positions.keys():
            ticker = self.market_feed.get_ticker(symbol)
            if ticker:
                prices[symbol] = ticker['last']

        # Update positions with stored context for ATR/trend-aware trailing
        contexts = {sym: pos.meta for sym, pos in self.risk_manager.positions.items()}
        closed = self.risk_manager.update_positions(prices, contexts)

        # Print closed positions and update database
        for pos in closed:
            self._print_close(
                pos['symbol'],
                pos['exit_price'],
                pos['pnl'],
                "Stop/Target Hit"
            )

            # Update trade in database
            if 'trade_id' in pos:
                duration_minutes = (datetime.now() - pos['entry_time']).total_seconds() / 60
                pnl_percent = (pos['pnl'] / (pos['entry_price'] * pos['quantity'])) * 100

                self.trade_db.update_trade(pos['trade_id'], {
                    'exit_price': pos['exit_price'],
                    'exit_time': datetime.now(),
                    'pnl': pos['pnl'],
                    'pnl_percent': pnl_percent,
                    'status': 'closed',
                    'exit_reason': 'Stop/Target Hit',
                    'duration_minutes': duration_minutes
                })

                # Send Telegram notification for position closed (SL/TP)
                if self.telegram:
                    self._send_telegram_notification(
                        self.telegram.send_trade_notification(
                            action='CLOSE',
                            symbol=pos['symbol'],
                            side='SELL' if pos['side'] == 'long' else 'BUY',
                            entry_price=pos['entry_price'],
                            exit_price=pos['exit_price'],
                            quantity=pos['quantity'],
                            pnl=pos['pnl'],
                            pnl_percent=pnl_percent,
                            duration=self._format_duration(duration_minutes),
                            reason='Stop/Target Hit',
                            portfolio_info=self._get_portfolio_info()
                        )
                    )

    def _print_trade(self, action: str, symbol: str, price: float,
                    quantity: float, confidence: float, reason: str,
                    stop_loss: float = None, take_profit: float = None):
        """Print trade information with colors"""
        color = Fore.GREEN if action == "BUY" else Fore.RED
        print(f"\n{color}{'='*80}")
        print(f"{action} SIGNAL - {symbol}")
        print(f"{'='*80}{Style.RESET_ALL}")
        print(f"Time:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Price:      ${price:.2f}")
        print(f"Quantity:   {quantity:.6f}")
        print(f"Value:      ${price * quantity:.2f}")
        print(f"Confidence: {confidence:.1%}")
        print(f"Reason:     {reason}")
        if stop_loss:
            print(f"Stop Loss:  ${stop_loss:.2f} ({((stop_loss - price) / price * 100):.2f}%)")
        if take_profit:
            print(f"Take Profit: ${take_profit:.2f} ({((take_profit - price) / price * 100):.2f}%)")
        print(f"{color}{'='*80}{Style.RESET_ALL}\n")

    def _print_close(self, symbol: str, exit_price: float, pnl: float, reason: str):
        """Print position close information"""
        color = Fore.GREEN if pnl > 0 else Fore.RED
        print(f"\n{color}{'='*80}")
        print(f"POSITION CLOSED - {symbol}")
        print(f"{'='*80}{Style.RESET_ALL}")
        print(f"Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Price:    ${exit_price:.2f}")
        print(f"PnL:      ${pnl:.2f}")
        print(f"Reason:   {reason}")
        print(f"{color}{'='*80}{Style.RESET_ALL}\n")

    def _print_status(self, analyses: List[Dict]):
        """Print bot status"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"TRADING BOT STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}{Style.RESET_ALL}")

        # Portfolio summary
        current_prices = {a['symbol']: a['price'] for a in analyses if a}
        portfolio = self.risk_manager.get_portfolio_summary(current_prices)

        print(f"\nPortfolio:")
        print(f"  Open Positions: {portfolio['open_positions']}")
        print(f"  Daily Trades:   {portfolio['daily_trades']}")
        print(f"  Unrealized PnL: ${portfolio['unrealized_pnl']:.2f}")
        print(f"  Daily PnL:      ${portfolio['daily_pnl']:.2f}")
        print(f"  Total PnL:      ${portfolio['total_pnl']:.2f}")

        # Market analysis for each symbol
        print(f"\nMarket Analysis:")
        for analysis in analyses:
            if not analysis:
                continue

            symbol = analysis['symbol']
            signal = analysis['signal']
            market = analysis.get('market', {})

            color = Fore.GREEN if signal['action'] == 'BUY' else (Fore.RED if signal['action'] == 'SELL' else Fore.YELLOW)

            print(f"\n  {symbol}:")
            print(f"    Price:      ${analysis['price']:.2f}")
            print(f"    Signal:     {color}{signal['action']}{Style.RESET_ALL} (confidence: {signal['confidence']:.1%})")
            print(f"    RSI:        {market.get('rsi', 'N/A')}")
            print(f"    Trend:      {market.get('trend', 'N/A')}")
            print(f"    Reason:     {signal.get('reason', 'N/A')}")

        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    async def run_loop(self):
        """Main trading loop"""
        logger.info("Starting trading bot...")
        print(f"{Fore.GREEN}Trading Bot Started!{Style.RESET_ALL}")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Update Interval: {self.update_interval}s\n")

        # Start Telegram command handler
        # TEMPORARILY DISABLED: Causing webhook conflict - bot blocked for 6 days
        # TODO: Fix telegram commands to work without polling (use webhook or disable)
        # if self.telegram_commands:
        #     try:
        #         await self.telegram_commands.start()
        #         logger.info("Telegram commands started")
        #     except Exception as e:
        #         logger.error(f"Failed to start Telegram commands: {e}")

        # Print learning system status
        learning_params = self.learning_engine.get_current_strategy_params()
        effective_min_conf = self.signal_generator.config.get('min_confidence', learning_params['min_confidence'])
        effective_weights = self.signal_generator.config.get('weights', learning_params['weights'])
        print(f"{Fore.MAGENTA}Learning System: {'ENABLED' if learning_params['learning_enabled'] else 'DISABLED'}{Style.RESET_ALL}")
        print(f"Current Weights: {effective_weights}")
        print(f"Min Confidence (effective): {effective_min_conf}\n")

        if os.getenv('FORCE_LEARNING', '0') == '1':
            print(f"{Fore.MAGENTA}FORCE_LEARNING active - learning cycle will run immediately if conditions allow.{Style.RESET_ALL}\n")

        # Print symbol performance summary
        if hasattr(self, 'intelligent_filter') and self.intelligent_filter:
            symbol_summary = self.intelligent_filter.get_symbol_performance_summary()
            logger.info(f"\n{symbol_summary}\n")

        # Send startup notification via Telegram
        if self.telegram:
            try:
                learning_status = "Activé (cycles toutes les 2h)" if learning_params['learning_enabled'] else "Désactivé"
                await self.telegram.send_info_notification(
                    f"🤖 *Bot Démarré avec Succès*\n\n"
                    f"*Mode:* {self.trading_mode.value.upper()}\n"
                    f"*Symboles:* {', '.join(self.symbols)}\n"
                    f"*Timeframe:* {self.timeframe}\n"
                    f"*Scan toutes les:* {self.update_interval}s\n"
                    f"*ML Learning:* {learning_status}\n"
                    f"*Notifications:* Activées\n\n"
                    f"Portfolio: ${self.capital:.2f} USDT"
                )
            except Exception as e:
                logger.error(f"Failed to send startup notification: {e}")

        iteration = 0
        while self.running:
            try:
                iteration += 1

                # CRITICAL: Force daily reset check every iteration
                # Prevents stuck daily_trades counter from blocking all trading
                self.risk_manager.reset_daily_stats()

                # Check if learning cycle should be triggered
                if self.learning_engine.should_trigger_learning():
                    logger.info(f"\n{Fore.MAGENTA}{'='*80}")
                    logger.info("Triggering Learning Cycle...")
                    logger.info(f"{'='*80}{Style.RESET_ALL}\n")

                    learning_results = self.learning_engine.execute_learning_cycle()

                    if learning_results['success']:
                        logger.info(f"\n{Fore.GREEN}Learning cycle completed successfully!{Style.RESET_ALL}")
                        logger.info(f"Adaptations identified: {len(learning_results.get('adaptations', []))}")

                        # Print learning report
                        report = self.learning_engine.generate_learning_report()
                        print(report)

                        # Print performance report
                        perf_report = self.perf_analyzer.generate_performance_report()
                        print(perf_report)

                        # Print symbol performance summary
                        if hasattr(self, 'intelligent_filter') and self.intelligent_filter:
                            symbol_summary = self.intelligent_filter.get_symbol_performance_summary()
                            logger.info(f"\n{symbol_summary}\n")

                        # Send Telegram notification for learning cycle
                        if self.telegram:
                            self._send_telegram_notification(
                                self.telegram.send_learning_notification(
                                    duration=learning_results.get('duration', 0),
                                    trades_analyzed=learning_results.get('trades_analyzed', 0),
                                    model_metrics=learning_results.get('model_metrics', {}),
                                    weight_changes=learning_results.get('weight_changes', {}),
                                    adaptations=learning_results.get('adaptations', []),
                                    performance=learning_results.get('performance_stats', {})
                                )
                            )
                    else:
                        logger.warning(f"Learning cycle had errors: {learning_results.get('errors')}")

                # OPTIMIZED: Analyze all 15 symbols in parallel with concurrent.futures
                analyses = []
                from concurrent.futures import ThreadPoolExecutor, as_completed

                # SMART PRIORITIZATION: Analyze best performers first
                # Get symbol performance to prioritize analysis
                symbol_priorities = []
                try:
                    if hasattr(self, 'symbol_selector') and self.symbol_selector:
                        for symbol in self.symbols:
                            perf = self.symbol_selector.get_symbol_performance(symbol)
                            win_rate = perf.get('win_rate', 50)
                            total_trades = perf.get('total_trades', 0)
                            # Priority: good win rate + experience
                            priority = win_rate * (1 + min(total_trades / 100, 1))
                            symbol_priorities.append((symbol, priority))
                        # Sort by priority (best first)
                        symbol_priorities.sort(key=lambda x: x[1], reverse=True)
                        prioritized_symbols = [s[0] for s in symbol_priorities]
                        logger.info(f"📊 Symbol priority order: {', '.join([f'{s}({p:.0f})' for s, p in symbol_priorities[:5]])}")
                    else:
                        prioritized_symbols = self.symbols
                except Exception as e:
                    logger.warning(f"Could not prioritize symbols: {e}")
                    prioritized_symbols = self.symbols

                # Use ThreadPoolExecutor to analyze symbols in parallel
                # With 1.9GB RAM, we can easily handle 5 concurrent analyses
                with ThreadPoolExecutor(max_workers=5, thread_name_prefix="analyzer") as executor:
                    # Submit all symbol analyses (prioritized order)
                    future_to_symbol = {
                        executor.submit(self.analyze_symbol, symbol): symbol
                        for symbol in prioritized_symbols
                    }

                    # Process results as they complete (faster symbols finish first)
                    for future in as_completed(future_to_symbol):
                        symbol = future_to_symbol[future]
                        try:
                            analysis = future.result(timeout=10)  # 10s timeout per symbol
                            if analysis:
                                analyses.append(analysis)
                                # Execute signal if confidence is high enough
                                logger.info(f"🔍 DEBUG: {symbol} action={analysis['signal']['action']} conf={analysis['signal']['confidence']:.2%}")
                                if analysis['signal']['action'] != 'HOLD':
                                    logger.info(f"🚀 DEBUG: Calling execute_signal for {symbol} {analysis['signal']['action']}")
                                    self.execute_signal(analysis)
                                else:
                                    logger.info(f"⏸️ DEBUG: Skipping {symbol} - action is HOLD")
                        except Exception as e:
                            logger.error(f"Error analyzing {symbol}: {e}")

                # Update existing positions
                self.update_positions()

                # Per-iteration concise status line (open positions, daily trades, unrealized PnL, ML readiness)
                try:
                    current_prices = {a['symbol']: a['price'] for a in analyses if a}
                    portfolio = self.risk_manager.get_portfolio_summary(current_prices)
                    perf_stats = self.trade_db.get_performance_stats(days=30)
                    ml_needed = getattr(self.learning_engine, 'min_trades_for_learning', 30)
                    print(
                        f"Status: open={portfolio['open_positions']} | daily_trades={portfolio['daily_trades']} | "
                        f"unrealizedPnL=${portfolio['unrealized_pnl']:.2f} | closed_trades={perf_stats['total_trades']}/{ml_needed} for ML"
                    )

                    # Also print a compact per-symbol signal snapshot to show evolution
                    if analyses:
                        snapshots = []
                        for a in analyses:
                            sig = a['signal']
                            snapshots.append(
                                f"{a['symbol']}: {sig['action']} {sig['confidence']:.0%}"
                            )
                        print("Signals: " + " | ".join(snapshots))

                    # Periodic performance report every 100 trades
                    if perf_stats['total_trades'] > 0 and perf_stats['total_trades'] % 100 == 0:
                        try:
                            print("\n=== Performance Snapshot (every 100 trades) ===")
                            perf_report = self.perf_analyzer.generate_performance_report()
                            print(perf_report)
                        except Exception:
                            pass
                except Exception as _:
                    # Non-fatal
                    pass

                # Print status every 10 iterations
                if iteration % 10 == 0:
                    self._print_status(analyses)

                # Run autonomous watchdog health check (every 30 min)
                if self.watchdog and self.watchdog.should_run_check():
                    logger.info("🤖 Running autonomous health check...")
                    health_report = self.watchdog.health_check()

                    if not health_report['healthy']:
                        logger.warning(f"⚠️ Health issues detected: {len(health_report['issues'])} problems")
                        logger.warning(self.watchdog.get_status_report())

                        # Send Telegram notification if issues detected
                        if self.telegram and (health_report['issues'] or health_report['fixes_applied']):
                            self._send_telegram_notification(
                                self.telegram.send_info_notification(
                                    f"🤖 *Watchdog Alert*\n\n{self.watchdog.get_status_report()}"
                                )
                            )
                    else:
                        logger.info("✅ Autonomous health check: All systems healthy")

                # Wait for next update
                logger.info(f"✓ Iteration {iteration} complete, waiting {self.update_interval}s for next update...")
                print(f"\n{Fore.CYAN}⏱️  Waiting {self.update_interval}s until next market scan...{Style.RESET_ALL}")
                await asyncio.sleep(self.update_interval)
                logger.info(f"⏰ Woke up from sleep, starting iteration {iteration + 1}")

            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                # Send shutdown notification
                if self.telegram:
                    try:
                        await self.telegram.send_info_notification(
                            "🛑 *Bot Arrêté Manuellement*\n\n"
                            f"Arrêt demandé par l'utilisateur (Ctrl+C)\n"
                            f"Itérations complétées: {iteration}"
                        )
                    except Exception:
                        pass
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                # Send error notification
                if self.telegram:
                    try:
                        await self.telegram.send_error_notification(
                            module='TradingBot.run_loop',
                            error_type=type(e).__name__,
                            error_message=str(e),
                            severity='critical',
                            context={'iteration': iteration}
                        )
                    except Exception:
                        pass
                await asyncio.sleep(5)

        logger.info(f"⚠️ LOOP ENDED - Trading bot stopped - self.running = {self.running}")

    def start(self):
        """Start the trading bot"""
        self.running = True
        try:
            asyncio.run(self.run_loop())
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.stop()

    def stop(self):
        """Stop the trading bot"""
        self.running = False
        
        # Stop Telegram command handler
        if self.telegram_commands:
            self._send_telegram_notification(
                self.telegram_commands.stop()
            )
        
        # Stop notification loop
        if self._notification_loop:
            try:
                self._notification_loop.call_soon_threadsafe(self._notification_loop.stop)
                logger.info("Notification loop stopped")
            except Exception as e:
                logger.warning(f"Error stopping notification loop: {e}")
        
        print(f"\n{Fore.YELLOW}Trading Bot Stopped{Style.RESET_ALL}")

        # Print final statistics
        stats = self.risk_manager.get_performance_stats()
        if stats['total_trades'] > 0:
            print(f"\n{Fore.CYAN}Performance Statistics:{Style.RESET_ALL}")
            print(f"  Total Trades:    {stats['total_trades']}")
            print(f"  Winning Trades:  {stats['winning_trades']}")
            print(f"  Losing Trades:   {stats['losing_trades']}")
            print(f"  Win Rate:        {stats['win_rate']:.1f}%")
            print(f"  Total PnL:       ${stats['total_pnl']:.2f}")
            print(f"  Avg Win:         ${stats['avg_win']:.2f}")
            print(f"  Avg Loss:        ${stats['avg_loss']:.2f}")
            print(f"  Profit Factor:   {stats['profit_factor']:.2f}")

            # Save performance snapshot to database
            try:
                self.trade_db.insert_strategy_performance({
                    'strategy_name': self.config.get('strategy', {}).get('name', 'Multi-Indicator Strategy'),
                    'total_trades': stats['total_trades'],
                    'winning_trades': stats['winning_trades'],
                    'losing_trades': stats['losing_trades'],
                    'win_rate': stats['win_rate'] / 100,
                    'total_pnl': stats['total_pnl'],
                    'avg_win': stats['avg_win'],
                    'avg_loss': stats['avg_loss'],
                    'profit_factor': stats['profit_factor'],
                    'sharpe_ratio': 0.0,  # Could be calculated if we track returns
                    'max_drawdown': 0.0,  # Could be calculated if we track equity curve
                    'config': self.config
                })
                logger.info("Performance snapshot saved to database")
            except Exception as e:
                logger.error(f"Error saving performance snapshot: {e}")

        # Close database connection
        try:
            self.trade_db.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")

    def _get_portfolio_info(self) -> Dict:
        """Get current portfolio information for notifications"""
        try:
            current_prices = {}
            for symbol in self.symbols:
                ticker = self.market_feed.get_ticker(symbol)
                if ticker:
                    current_prices[symbol] = ticker['last']
            
            portfolio = self.risk_manager.get_portfolio_summary(current_prices)
            
            # Calculer le capital disponible (capital initial + PnL réalisé - positions ouvertes)
            # En paper mode, utiliser le balance du executor
            if self.trading_mode == TradingMode.PAPER:
                paper_balance = self.executor.get_balance()
                # En paper mode, get_balance() retourne directement {'USDT': 10000, 'SOL': -1.2, ...}
                available_balance = paper_balance.get('USDT', self.capital)
            else:
                # En mode réel, récupérer le vrai solde
                real_balance = self.executor.get_balance()
                available_balance = real_balance.get('free', {}).get('USDT', self.capital)
            
            # Calculer le PnL du jour
            from datetime import datetime
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            all_trades = self.trade_db.get_trade_history(limit=1000)
            today_trades = [
                t for t in all_trades
                if t.get('exit_time') and datetime.fromisoformat(t['exit_time']) >= today_start
            ]
            today_pnl = sum(t.get('pnl', 0) for t in today_trades)
            
            # Calculer le PnL total réalisé
            closed_trades = [t for t in all_trades if t.get('exit_time')]
            total_realized_pnl = sum(t.get('pnl', 0) for t in closed_trades)
            
            # Nombre de positions ouvertes depuis risk_manager
            open_positions_count = len(self.risk_manager.positions)
            
            return {
                'balance': available_balance,
                'open_positions': open_positions_count,
                'max_positions': self.config.get('risk', {}).get('max_open_positions', 3),
                'daily_trades': portfolio.get('daily_trades', 0),
                'unrealized_pnl': portfolio.get('unrealized_pnl', 0),
                'total_pnl': total_realized_pnl + portfolio.get('unrealized_pnl', 0),
                'total_pnl_percent': ((total_realized_pnl + portfolio.get('unrealized_pnl', 0)) / self.capital * 100) if self.capital > 0 else 0,
                'today_pnl': today_pnl,
                'today_pnl_percent': (today_pnl / self.capital * 100) if self.capital > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting portfolio info: {e}")
            return {
                'balance': self.capital,
                'open_positions': 0,
                'max_positions': 3,
                'daily_trades': 0,
                'unrealized_pnl': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0,
                'today_pnl': 0,
                'today_pnl_percent': 0
            }

    def _format_duration(self, minutes: float) -> str:
        """Format duration in minutes to human-readable string"""
        if minutes < 60:
            return f"{int(minutes)}min"
        elif minutes < 1440:  # Less than 24 hours
            hours = int(minutes / 60)
            mins = int(minutes % 60)
            return f"{hours}h {mins}min"
        else:
            days = int(minutes / 1440)
            hours = int((minutes % 1440) / 60)
            return f"{days}j {hours}h"


def main():
    """Main entry point"""
    from dotenv import load_dotenv
    from safety_checks import pre_flight_check, emergency_stop_info
    import sys
    
    # Fix encoding for Windows
    if sys.platform == 'win32':
        import codecs
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    load_dotenv()

    print(f"{Fore.CYAN}")
    print("=" * 67)
    print("                    TRADING BOT v1.0                           ")
    print("              Real-time Market Analysis System                 ")
    print("=" * 67)
    print(f"{Style.RESET_ALL}\n")

    # Initialize bot
    bot = TradingBot()

    # Get trading mode
    trading_mode = os.getenv('TRADING_MODE', 'paper').lower()

    # Perform safety checks
    if not pre_flight_check(trading_mode, bot.config, bot.market_feed.exchange):
        print(f"\n{Fore.RED}❌ Bot startup cancelled by user or failed safety checks.{Style.RESET_ALL}\n")
        sys.exit(0)

    # Show emergency stop info for live/testnet
    if trading_mode in ['live', 'testnet']:
        emergency_stop_info()

    try:
        bot.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        bot.stop()


if __name__ == "__main__":
    main()
