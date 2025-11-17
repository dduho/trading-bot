"""
Risk Management Module
Manages position sizing, stop loss, take profit, and overall risk
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Position:
    """Represents a trading position"""

    def __init__(self, symbol: str, side: str, entry_price: float,
                 quantity: float, stop_loss: float = None,
                 take_profit: float = None):
        self.symbol = symbol
        self.side = side  # 'long' or 'short'
        self.entry_price = entry_price
        self.quantity = quantity
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.entry_time = datetime.now()
        self.exit_price = None
        self.exit_time = None
        self.pnl = 0
        self.status = 'open'  # 'open', 'closed'
        self.trade_id = None  # Database trade ID for learning system

    def update_pnl(self, current_price: float) -> float:
        """Calculate current profit/loss"""
        if self.side == 'long':
            self.pnl = (current_price - self.entry_price) * self.quantity
        else:  # short
            self.pnl = (self.entry_price - current_price) * self.quantity
        return self.pnl

    def check_stop_loss(self, current_price: float) -> bool:
        """Check if stop loss is hit"""
        if not self.stop_loss:
            return False

        if self.side == 'long' and current_price <= self.stop_loss:
            return True
        elif self.side == 'short' and current_price >= self.stop_loss:
            return True
        return False

    def check_take_profit(self, current_price: float) -> bool:
        """Check if take profit is hit"""
        if not self.take_profit:
            return False

        if self.side == 'long' and current_price >= self.take_profit:
            return True
        elif self.side == 'short' and current_price <= self.take_profit:
            return True
        return False

    def close(self, exit_price: float):
        """Close the position"""
        self.exit_price = exit_price
        self.exit_time = datetime.now()
        self.status = 'closed'
        self.update_pnl(exit_price)

    def to_dict(self) -> Dict:
        """Convert position to dictionary"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'pnl': self.pnl,
            'status': self.status,
            'entry_time': self.entry_time,  # Return datetime object instead of isoformat
            'exit_time': self.exit_time,
            'trade_id': self.trade_id
        }


class RiskManager:
    """Manages trading risk and position sizing"""

    def __init__(self, config: Dict = None):
        """
        Initialize risk manager

        Args:
            config: Risk management configuration
        """
        self.config = config or self._default_config()
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.daily_pnl = 0
        self.daily_trades = 0
        self.last_reset = datetime.now().date()
        self.last_trade_time: Dict[str, datetime] = {}  # Per-symbol cooldown tracking

    def _default_config(self) -> Dict:
        """Default risk configuration"""
        return {
            'max_position_size_percent': 10,  # Max % of portfolio per position
            'stop_loss_percent': 2.0,
            'take_profit_percent': 5.0,
            'trailing_stop_percent': 1.5,
            'max_open_positions': 3,
            'max_daily_trades': 10,
            'max_daily_loss_percent': 5.0,
            'risk_reward_ratio': 2.0  # Min risk/reward ratio
        }

    def reset_daily_stats(self):
        """Reset daily statistics"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_pnl = 0
            self.daily_trades = 0
            self.last_reset = today
            logger.info("Daily statistics reset")

    def calculate_position_size(self, capital: float, risk_percent: float,
                                entry_price: float, stop_loss: float) -> float:
        """
        Calculate position size based on risk

        Args:
            capital: Total capital available
            risk_percent: Percentage of capital to risk
            entry_price: Entry price
            stop_loss: Stop loss price

        Returns:
            Position size (quantity)
        """
        # Maximum position size based on config
        max_position_value = capital * (self.config['max_position_size_percent'] / 100)

        # Risk-based position sizing
        risk_amount = capital * (risk_percent / 100)
        price_diff = abs(entry_price - stop_loss)

        if price_diff == 0:
            logger.warning("Stop loss equals entry price, using max position size")
            return max_position_value / entry_price

        risk_based_quantity = risk_amount / price_diff

        # Take the smaller of max position and risk-based
        risk_based_value = risk_based_quantity * entry_price
        if risk_based_value > max_position_value:
            quantity = max_position_value / entry_price
        else:
            quantity = risk_based_quantity

        logger.info(f"Calculated position size: {quantity:.4f} (value: ${quantity * entry_price:.2f})")
        return quantity

    def calculate_stop_loss(self, entry_price: float, side: str,
                           atr: float = None) -> float:
        """
        Calculate stop loss price

        Args:
            entry_price: Entry price
            side: 'long' or 'short'
            atr: Average True Range (optional, for volatility-based stops)

        Returns:
            Stop loss price
        """
        if atr and atr > 0:
            # ATR-based stop loss (2x ATR)
            stop_distance = 2 * atr
        else:
            # Percentage-based stop loss
            stop_distance = entry_price * (self.config['stop_loss_percent'] / 100)

        if side == 'long':
            stop_loss = entry_price - stop_distance
        else:  # short
            stop_loss = entry_price + stop_distance

        return stop_loss

    def calculate_take_profit(self, entry_price: float, stop_loss: float,
                             side: str) -> float:
        """
        Calculate take profit based on risk/reward ratio

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'

        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * self.config['risk_reward_ratio']

        if side == 'long':
            take_profit = entry_price + reward
        else:  # short
            take_profit = entry_price - reward

        return take_profit

    def can_open_position(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if a new position can be opened

        Returns:
            Tuple of (can_open, reason)
        """
        self.reset_daily_stats()

        # Check if position already exists
        if symbol in self.positions:
            return False, f"Position already open for {symbol}"

        # Cooldown check
        cooldown = self.config.get('cooldown_seconds')
        if cooldown and symbol in self.last_trade_time:
            elapsed = (datetime.now() - self.last_trade_time[symbol]).total_seconds()
            if elapsed < cooldown:
                return False, f"Cooldown active ({int(cooldown - elapsed)}s remaining)"

        # Check max open positions
        if len(self.positions) >= self.config['max_open_positions']:
            return False, f"Maximum open positions reached ({self.config['max_open_positions']})"

        # Check daily trade limit
        if self.daily_trades >= self.config['max_daily_trades']:
            return False, f"Daily trade limit reached ({self.config['max_daily_trades']})"

        # Check daily loss limit (DÉSACTIVÉ en phase d'apprentissage paper trading)
        # max_daily_loss = self.config['max_daily_loss_percent']
        # if self.daily_pnl < 0 and abs(self.daily_pnl) >= max_daily_loss:
        #     return False, f"Daily loss limit reached ({max_daily_loss}%)"

        return True, "OK"

    def open_position(self, symbol: str, side: str, entry_price: float,
                     quantity: float, stop_loss: float = None,
                     take_profit: float = None) -> Optional[Position]:
        """
        Open a new position

        Returns:
            Position object if successful, None otherwise
        """
        can_open, reason = self.can_open_position(symbol)
        if not can_open:
            logger.warning(f"Cannot open position: {reason}")
            return None

        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.positions[symbol] = position
        self.daily_trades += 1
        self.last_trade_time[symbol] = datetime.now()

        logger.info(f"Opened {side} position: {symbol} @ {entry_price} (qty: {quantity})")
        return position

    def close_position(self, symbol: str, exit_price: float, reason: str = "") -> Optional[Position]:
        """
        Close an existing position

        Returns:
            Closed position object if successful
        """
        if symbol not in self.positions:
            logger.warning(f"No open position for {symbol}")
            return None

        position = self.positions[symbol]
        position.close(exit_price)

        self.daily_pnl += position.pnl
        self.closed_positions.append(position)
        del self.positions[symbol]
        # Record last trade action time for cooldown logic
        self.last_trade_time[symbol] = datetime.now()

        logger.info(f"Closed position: {symbol} @ {exit_price} | PnL: ${position.pnl:.2f} | Reason: {reason}")
        return position

    def update_positions(self, prices: Dict[str, float]) -> List[Dict]:
        """
        Update all positions and check stop loss/take profit

        Args:
            prices: Dict of {symbol: current_price}

        Returns:
            List of closed positions
        """
        closed = []

        for symbol, position in list(self.positions.items()):
            if symbol not in prices:
                continue

            current_price = prices[symbol]
            position.update_pnl(current_price)

            # Check stop loss
            if position.check_stop_loss(current_price):
                closed_pos = self.close_position(symbol, current_price, "Stop Loss Hit")
                if closed_pos:
                    closed.append(closed_pos.to_dict())

            # Check take profit
            elif position.check_take_profit(current_price):
                closed_pos = self.close_position(symbol, current_price, "Take Profit Hit")
                if closed_pos:
                    closed.append(closed_pos.to_dict())

        return closed

    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        return [pos.to_dict() for pos in self.positions.values()]

    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict:
        """
        Get portfolio summary

        Args:
            current_prices: Dict of current prices

        Returns:
            Portfolio summary
        """
        total_pnl = self.daily_pnl

        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.update_pnl(current_prices[symbol])
                total_pnl += position.pnl

        return {
            'open_positions': len(self.positions),
            'daily_trades': self.daily_trades,
            'daily_pnl': self.daily_pnl,
            'unrealized_pnl': sum(pos.pnl for pos in self.positions.values()),
            'total_pnl': total_pnl,
            'positions': self.get_open_positions()
        }

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.closed_positions:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }

        total_trades = len(self.closed_positions)
        winning_trades = [p for p in self.closed_positions if p.pnl > 0]
        losing_trades = [p for p in self.closed_positions if p.pnl < 0]

        total_wins = sum(p.pnl for p in winning_trades)
        total_losses = abs(sum(p.pnl for p in losing_trades))

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': sum(p.pnl for p in self.closed_positions),
            'avg_win': total_wins / len(winning_trades) if winning_trades else 0,
            'avg_loss': total_losses / len(losing_trades) if losing_trades else 0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else 0,
            'largest_win': max([p.pnl for p in self.closed_positions]),
            'largest_loss': min([p.pnl for p in self.closed_positions])
        }
