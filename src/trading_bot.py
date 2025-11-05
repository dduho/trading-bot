"""
Trading Bot - Main Orchestrator
Coordinates all components and executes the trading strategy
"""

import asyncio
import yaml
import os
from datetime import datetime
from typing import Dict, List
import logging
from colorama import Fore, Style, init

from market_data import MarketDataFeed
from technical_analysis import TechnicalAnalyzer
from signal_generator import SignalGenerator, Signal
from risk_manager import RiskManager

# Initialize colorama for colored output
init(autoreset=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
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
        self.capital = 10000  # Default starting capital (paper trading)

        # Initialize components
        self.market_feed = MarketDataFeed(
            exchange_name=os.getenv('EXCHANGE', 'binance'),
            testnet=True
        )
        self.analyzer = TechnicalAnalyzer(self.config.get('indicators', {}))
        self.signal_generator = SignalGenerator(self.config.get('strategy', {}))
        self.risk_manager = RiskManager(self.config.get('risk', {}))

        # Trading state
        self.symbols = self.config.get('symbols', ['BTC/USDT'])
        self.timeframe = os.getenv('TIMEFRAME', '1m')
        self.update_interval = self._timeframe_to_seconds(self.timeframe)

        logger.info(f"Trading Bot initialized with {len(self.symbols)} symbols")

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

            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price': df['close'].iloc[-1],
                'signal': signal_result,
                'market': market_summary,
                'dataframe': df_with_indicators
            }

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {}

    def execute_signal(self, analysis: Dict):
        """
        Execute trading signal

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

            # Open position
            position = self.risk_manager.open_position(
                symbol=symbol,
                side='long',
                entry_price=price,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit
            )

            if position:
                self._print_trade(
                    "BUY",
                    symbol,
                    price,
                    quantity,
                    signal['confidence'],
                    signal['reason'],
                    stop_loss,
                    take_profit
                )

        # SELL signal - close existing position
        elif signal['action'] == 'SELL' and symbol in self.risk_manager.positions:
            closed = self.risk_manager.close_position(symbol, price, "Signal: SELL")
            if closed:
                self._print_close(symbol, price, closed.pnl, "SELL Signal")

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

        # Print closed positions
        for pos in closed:
            self._print_close(
                pos['symbol'],
                pos['exit_price'],
                pos['pnl'],
                "Stop/Target Hit"
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

        iteration = 0
        while self.running:
            try:
                iteration += 1

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

                # Print status every 10 iterations
                if iteration % 10 == 0:
                    self._print_status(analyses)

                # Wait for next update
                await asyncio.sleep(self.update_interval)

            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)

        logger.info("Trading bot stopped")

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


def main():
    """Main entry point"""
    from dotenv import load_dotenv
    load_dotenv()

    print(f"{Fore.CYAN}")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                    TRADING BOT v1.0                           ║")
    print("║              Real-time Market Analysis System                 ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}\n")

    bot = TradingBot()

    try:
        bot.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        bot.stop()


if __name__ == "__main__":
    main()
