"""
Trading Bot - Main Orchestrator
Coordinates all components and executes the trading strategy
"""

import asyncio
import yaml
import os
import sys

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
        self.risk_manager = RiskManager(self.config.get('risk', {}))

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
        self.ml_optimizer = MLOptimizer(self.trade_db)
        self.learning_engine = AdaptiveLearningEngine(
            self.trade_db,
            self.perf_analyzer,
            self.ml_optimizer,
            learning_config
        )

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

    def _parse_trading_mode(self, mode_str: str) -> TradingMode:
        """Parse trading mode string to TradingMode enum"""
        mode_map = {
            'paper': TradingMode.PAPER,
            'testnet': TradingMode.TESTNET,
            'live': TradingMode.LIVE
        }
        return mode_map.get(mode_str, TradingMode.PAPER)
    
    def _send_telegram_notification(self, coro):
        """Helper pour envoyer une notification Telegram de manière synchrone"""
        if not self.telegram:
            return
        try:
            # Créer une nouvelle event loop si nécessaire
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Exécuter la coroutine
            loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

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

            # Enhance confidence with ML
            ml_enhanced_confidence = self.learning_engine.get_ml_enhanced_signal_confidence(
                signal_result, market_conditions
            )
            signal_result['ml_enhanced_confidence'] = ml_enhanced_confidence
            signal_result['original_confidence'] = signal_result['confidence']
            signal_result['confidence'] = ml_enhanced_confidence

            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price': df['close'].iloc[-1],
                'signal': signal_result,
                'market': market_summary,
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
        if not analysis or 'signal' not in analysis:
            return

        symbol = analysis['symbol']
        signal = analysis['signal']
        price = analysis['price']

        # Check if we can open a position
        can_open, reason = self.risk_manager.can_open_position(symbol)

        # BUY signal
        # If a SHORT is open for this symbol, close it on BUY
        if signal['action'] == 'BUY' and symbol in self.risk_manager.positions:
            existing = self.risk_manager.positions[symbol]
            if existing.side == 'short':
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
            # Calculate position parameters
            atr = analysis['dataframe']['atr'].iloc[-1] if 'atr' in analysis['dataframe'].columns else None
            stop_loss = self.risk_manager.calculate_stop_loss(price, 'long', atr)
            take_profit = self.risk_manager.calculate_take_profit(price, stop_loss, 'long')

            # Calculate position size
            quantity = self.risk_manager.calculate_position_size(
                capital=self.capital,
                risk_percent=self.config['risk']['stop_loss_percent'],
                entry_price=price,
                stop_loss=stop_loss
            )

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

                position = self.risk_manager.open_position(
                    symbol=symbol,
                    side='long',
                    entry_price=actual_price,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit
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
            # Calculate position parameters for short
            atr = analysis['dataframe']['atr'].iloc[-1] if 'atr' in analysis['dataframe'].columns else None
            stop_loss = self.risk_manager.calculate_stop_loss(price, 'short', atr)
            take_profit = self.risk_manager.calculate_take_profit(price, stop_loss, 'short')

            quantity = self.risk_manager.calculate_position_size(
                capital=self.capital,
                risk_percent=self.config['risk']['stop_loss_percent'],
                entry_price=price,
                stop_loss=stop_loss
            )

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
                position = self.risk_manager.open_position(
                    symbol=symbol,
                    side='short',
                    entry_price=actual_price,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit
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

        # Update positions
        closed = self.risk_manager.update_positions(prices)

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
        if self.telegram_commands:
            try:
                await self.telegram_commands.start()
                logger.info("Telegram commands started")
            except Exception as e:
                logger.error(f"Failed to start Telegram commands: {e}")

        # Print learning system status
        learning_params = self.learning_engine.get_current_strategy_params()
        effective_min_conf = self.signal_generator.config.get('min_confidence', learning_params['min_confidence'])
        effective_weights = self.signal_generator.config.get('weights', learning_params['weights'])
        print(f"{Fore.MAGENTA}Learning System: {'ENABLED' if learning_params['learning_enabled'] else 'DISABLED'}{Style.RESET_ALL}")
        print(f"Current Weights: {effective_weights}")
        print(f"Min Confidence (effective): {effective_min_conf}\n")

        if os.getenv('FORCE_LEARNING', '0') == '1':
            print(f"{Fore.MAGENTA}FORCE_LEARNING active - learning cycle will run immediately if conditions allow.{Style.RESET_ALL}\n")

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

                # Analyze all symbols
                analyses = []
                for symbol in self.symbols:
                    analysis = self.analyze_symbol(symbol)
                    if analysis:
                        analyses.append(analysis)
                        # Execute signal if confidence is high enough
                        if analysis['signal']['action'] != 'HOLD':
                            self.execute_signal(analysis)

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
            
            # Calculer le PnL du jour
            from datetime import datetime
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_trades = [
                t for t in self.trade_db.get_trades(limit=100)
                if t.get('exit_time') and datetime.fromisoformat(t['exit_time']) >= today_start
            ]
            today_pnl = sum(t.get('pnl', 0) for t in today_trades)
            
            return {
                'balance': self.capital,
                'open_positions': portfolio.get('open_positions', 0),
                'max_positions': self.config.get('risk', {}).get('max_open_positions', 3),
                'daily_trades': portfolio.get('daily_trades', 0),
                'unrealized_pnl': portfolio.get('unrealized_pnl', 0),
                'total_pnl': portfolio.get('total_pnl', 0),
                'total_pnl_percent': (portfolio.get('total_pnl', 0) / self.capital * 100) if self.capital > 0 else 0,
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
