"""
Order Executor Module
Handles real order execution on exchanges (Paper, Testnet, and Live modes)
"""

import ccxt
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading mode options"""
    PAPER = "paper"      # Simulation only - no real orders
    TESTNET = "testnet"  # Exchange testnet - fake money, real API
    LIVE = "live"        # Real trading with real money


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderExecutor:
    """Executes orders on exchanges with support for paper, testnet, and live trading"""

    def __init__(self, exchange: ccxt.Exchange, mode: TradingMode = TradingMode.PAPER):
        """
        Initialize order executor

        Args:
            exchange: CCXT exchange instance
            mode: Trading mode (paper, testnet, or live)
        """
        self.exchange = exchange
        self.mode = mode
        self.paper_balance = {'USDT': 10000}  # Starting paper trading balance
        self.paper_orders = []

        logger.info(f"Order Executor initialized in {mode.value.upper()} mode")

        # Safety check
        if mode == TradingMode.LIVE:
            logger.warning("⚠️  LIVE TRADING MODE ACTIVATED - REAL MONEY AT RISK ⚠️")

    def create_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """
        Create a market order (buy/sell at current market price)

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Amount to trade

        Returns:
            Order information dict
        """
        logger.info(f"Creating {side.upper()} market order: {amount} {symbol}")

        if self.mode == TradingMode.PAPER:
            return self._execute_paper_order(symbol, side, amount, 'market')

        try:
            # Real order execution (testnet or live)
            order = self.exchange.create_market_order(symbol, side, amount)

            logger.info(f"✅ Order executed: {order['id']} - {side} {amount} {symbol} @ {order.get('price', 'market')}")
            return order

        except ccxt.InsufficientFunds as e:
            logger.error(f"❌ Insufficient funds: {e}")
            return None
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ Invalid order: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Order execution failed: {e}")
            return None

    def create_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """
        Create a limit order (buy/sell at specific price)

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Amount to trade
            price: Limit price

        Returns:
            Order information dict
        """
        logger.info(f"Creating {side.upper()} limit order: {amount} {symbol} @ ${price}")

        if self.mode == TradingMode.PAPER:
            return self._execute_paper_order(symbol, side, amount, 'limit', price)

        try:
            order = self.exchange.create_limit_order(symbol, side, amount, price)

            logger.info(f"✅ Limit order placed: {order['id']} - {side} {amount} {symbol} @ ${price}")
            return order

        except Exception as e:
            logger.error(f"❌ Limit order failed: {e}")
            return None

    def create_stop_loss_order(self, symbol: str, side: str, amount: float,
                               stop_price: float) -> Optional[Dict]:
        """
        Create a stop loss order

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Amount to trade
            stop_price: Stop loss trigger price

        Returns:
            Order information dict
        """
        logger.info(f"Creating stop loss order: {amount} {symbol} @ ${stop_price}")

        if self.mode == TradingMode.PAPER:
            return self._execute_paper_order(symbol, side, amount, 'stop_loss', stop_price)

        try:
            # Different exchanges have different methods for stop orders
            if hasattr(self.exchange, 'create_stop_loss_order'):
                order = self.exchange.create_stop_loss_order(symbol, side, amount, stop_price)
            elif hasattr(self.exchange, 'create_order'):
                # Fallback for exchanges that use generic create_order
                order = self.exchange.create_order(
                    symbol, 'stop_loss', side, amount, stop_price
                )
            else:
                logger.warning("Stop loss orders not supported on this exchange")
                return None

            logger.info(f"✅ Stop loss order placed: {order['id']}")
            return order

        except Exception as e:
            logger.error(f"❌ Stop loss order failed: {e}")
            return None

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an open order

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair

        Returns:
            True if successful
        """
        logger.info(f"Cancelling order: {order_id}")

        if self.mode == TradingMode.PAPER:
            self.paper_orders = [o for o in self.paper_orders if o['id'] != order_id]
            return True

        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"✅ Order cancelled: {order_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Order cancellation failed: {e}")
            return False

    def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """
        Get status of an order

        Args:
            order_id: Order ID
            symbol: Trading pair

        Returns:
            Order status dict
        """
        if self.mode == TradingMode.PAPER:
            for order in self.paper_orders:
                if order['id'] == order_id:
                    return order
            return None

        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order

        except Exception as e:
            logger.error(f"❌ Failed to fetch order status: {e}")
            return None

    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """
        Get all open orders

        Args:
            symbol: Trading pair (optional, None for all)

        Returns:
            List of open orders
        """
        if self.mode == TradingMode.PAPER:
            if symbol:
                return [o for o in self.paper_orders if o['symbol'] == symbol and o['status'] == 'open']
            return [o for o in self.paper_orders if o['status'] == 'open']

        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders

        except Exception as e:
            logger.error(f"❌ Failed to fetch open orders: {e}")
            return []

    def get_balance(self, currency: str = None) -> Dict:
        """
        Get account balance

        Args:
            currency: Specific currency (optional)

        Returns:
            Balance dict
        """
        if self.mode == TradingMode.PAPER:
            if currency:
                return {currency: self.paper_balance.get(currency, 0)}
            return self.paper_balance.copy()

        try:
            balance = self.exchange.fetch_balance()

            if currency:
                return {
                    'free': balance['free'].get(currency, 0),
                    'used': balance['used'].get(currency, 0),
                    'total': balance['total'].get(currency, 0)
                }

            return balance

        except Exception as e:
            logger.error(f"❌ Failed to fetch balance: {e}")
            return {}

    def _execute_paper_order(self, symbol: str, side: str, amount: float,
                            order_type: str, price: float = None) -> Dict:
        """
        Execute a simulated paper trading order

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Amount to trade
            order_type: 'market', 'limit', 'stop_loss'
            price: Price for limit/stop orders

        Returns:
            Simulated order dict
        """
        # Generate fake order ID
        order_id = f"PAPER_{int(datetime.now().timestamp() * 1000)}"

        # For paper trading, we need to get current price
        ticker = self.exchange.fetch_ticker(symbol)
        execution_price = price if price and order_type == 'limit' else ticker['last']

        # Calculate cost
        base_currency = symbol.split('/')[0]
        quote_currency = symbol.split('/')[1]

        if side == 'buy':
            cost = amount * execution_price
            # Check if we have enough quote currency
            if self.paper_balance.get(quote_currency, 0) < cost:
                logger.error(f"❌ Insufficient paper balance: need {cost} {quote_currency}")
                return None

            # Update balances
            self.paper_balance[quote_currency] = self.paper_balance.get(quote_currency, 0) - cost
            self.paper_balance[base_currency] = self.paper_balance.get(base_currency, 0) + amount

        else:  # sell
            # Allow synthetic shorts in PAPER mode by permitting negative base balance
            allow_shorts = True
            base_available = self.paper_balance.get(base_currency, 0)
            if base_available < amount and not allow_shorts:
                logger.error(f"❌ Insufficient paper balance: need {amount} {base_currency}")
                return None

            # Update balances (may go negative on base for shorts)
            cost = amount * execution_price
            self.paper_balance[base_currency] = base_available - amount
            self.paper_balance[quote_currency] = self.paper_balance.get(quote_currency, 0) + cost

        # Create order dict
        order = {
            'id': order_id,
            'symbol': symbol,
            'type': order_type,
            'side': side,
            'amount': amount,
            'price': execution_price,
            'cost': amount * execution_price,
            'status': 'closed',  # Paper orders are immediately filled
            'timestamp': int(datetime.now().timestamp() * 1000),
            'datetime': datetime.now().isoformat(),
            'fee': {'cost': 0, 'currency': quote_currency}
        }

        self.paper_orders.append(order)

        logger.info(f"✅ PAPER ORDER executed: {side.upper()} {amount} {symbol} @ ${execution_price}")
        logger.info(f"   Paper balance: {self.paper_balance}")

        return order

    def get_trading_fees(self, symbol: str) -> Dict:
        """
        Get trading fees for a symbol

        Returns:
            Fee information dict
        """
        try:
            if self.mode == TradingMode.PAPER:
                return {'maker': 0.001, 'taker': 0.001}  # 0.1% default

            markets = self.exchange.load_markets()
            if symbol in markets:
                return {
                    'maker': markets[symbol].get('maker', 0.001),
                    'taker': markets[symbol].get('taker', 0.001)
                }
            return {'maker': 0.001, 'taker': 0.001}

        except Exception as e:
            logger.error(f"Failed to fetch fees: {e}")
            return {'maker': 0.001, 'taker': 0.001}

    def validate_order(self, symbol: str, side: str, amount: float, price: float = None) -> tuple:
        """
        Validate order parameters before execution

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            markets = self.exchange.load_markets()

            if symbol not in markets:
                return False, f"Invalid symbol: {symbol}"

            market = markets[symbol]

            # Check minimum amount
            if 'limits' in market and 'amount' in market['limits']:
                min_amount = market['limits']['amount'].get('min', 0)
                if amount < min_amount:
                    return False, f"Amount {amount} below minimum {min_amount}"

            # Check minimum cost
            if price and 'limits' in market and 'cost' in market['limits']:
                min_cost = market['limits']['cost'].get('min', 0)
                if amount * price < min_cost:
                    return False, f"Order cost below minimum {min_cost}"

            # Check balance (for real modes)
            if self.mode != TradingMode.PAPER:
                balance = self.get_balance()
                quote_currency = symbol.split('/')[1]
                base_currency = symbol.split('/')[0]

                if side == 'buy':
                    cost = amount * price if price else amount * self.exchange.fetch_ticker(symbol)['last']
                    available = balance.get('free', {}).get(quote_currency, 0)
                    if available < cost:
                        return False, f"Insufficient {quote_currency}: need {cost}, have {available}"
                else:  # sell
                    available = balance.get('free', {}).get(base_currency, 0)
                    if available < amount:
                        return False, f"Insufficient {base_currency}: need {amount}, have {available}"

            return True, "Valid"

        except Exception as e:
            return False, f"Validation error: {e}"

    def get_mode(self) -> TradingMode:
        """Get current trading mode"""
        return self.mode

    def get_paper_trading_stats(self) -> Dict:
        """Get paper trading statistics"""
        if self.mode != TradingMode.PAPER:
            return {}

        total_trades = len(self.paper_orders)
        total_value = sum(self.paper_balance.values())

        return {
            'mode': 'paper',
            'total_trades': total_trades,
            'balance': self.paper_balance,
            'total_value_usdt': total_value,
            'profit_loss': total_value - 10000,  # Assuming starting with 10000 USDT
            'orders_history': self.paper_orders[-10:]  # Last 10 orders
        }
