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
                 take_profit: float = None,
                 meta: Optional[Dict] = None):
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
        self.meta = meta or {}

        # Analytics/risk metadata
        self.initial_risk = abs(entry_price - stop_loss) if stop_loss else None
        self.atr_at_entry = self.meta.get('atr')
        self.trend_bias = self.meta.get('trend_bias')
        self.expected_rr = self.meta.get('expected_rr')
        self.max_duration_minutes = self.meta.get('max_duration_minutes')
        self.break_even_armed = False

    def update_pnl(self, current_price: float,
                   cost_rate: float = 0.0) -> float:
        """Calculate current profit/loss, accounting for estimated costs"""
        if self.side == 'long':
            raw_pnl = (current_price - self.entry_price) * self.quantity
        else:  # short
            raw_pnl = (self.entry_price - current_price) * self.quantity

        # Apply estimated round-trip cost once (entry + exit)
        notional = self.entry_price * self.quantity
        cost_penalty = notional * (cost_rate / 100)
        self.pnl = raw_pnl - cost_penalty
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

    def close(self, exit_price: float, cost_rate: float = 0.0):
        """Close the position"""
        self.exit_price = exit_price
        self.exit_time = datetime.now()
        self.status = 'closed'
        self.update_pnl(exit_price, cost_rate)

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
            'trade_id': self.trade_id,
            'atr_at_entry': self.atr_at_entry,
            'expected_rr': self.expected_rr,
            'max_duration_minutes': self.max_duration_minutes,
            'break_even_armed': self.break_even_armed
        }


class RiskManager:
    """Manages trading risk and position sizing"""

    def __init__(self, config: Dict = None, trading_mode: str = "paper"):
        """
        Initialize risk manager

        Args:
            config: Risk management configuration
            trading_mode: Trading mode ("paper", "testnet", or "live")
        """
        self.config = config or self._default_config()
        self.trading_mode = trading_mode.lower()
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.daily_pnl = 0
        self.daily_trades = 0
        self.last_reset = datetime.now().date()
        self.last_trade_time: Dict[str, datetime] = {}  # Per-symbol cooldown tracking
        self.last_known_equity: Optional[float] = self.config.get('starting_equity')

        # Cost/volatility controls
        self.trade_cost_percent = self.config.get('trade_cost_percent', 0.0)
        self.slippage_buffer_percent = self.config.get('slippage_buffer_percent', 0.0)
        
        # In paper mode, disable all limits
        if self.trading_mode == "paper":
            logger.info("🎮 PAPER MODE: All trading limits DISABLED for unlimited learning")

    def _default_config(self) -> Dict:
        """Default risk configuration"""
        return {
            'max_position_size_percent': 10,  # Max % of portfolio per position
            'stop_loss_percent': 2.0,
            'take_profit_percent': 5.0,
            'trailing_stop_percent': 1.5,
            'atr_trailing_multiplier': 1.5,  # ATR-based trailing distance
            'break_even_rr': 1.0,  # Move stop to BE after 1R
            'max_risk_per_trade_percent': 1.0,  # Hard cap per trade
            'trade_cost_percent': 0.05,  # Estimated round-trip cost (fees+slippage)
            'slippage_buffer_percent': 0.05,  # Extra buffer in sizing for slippage
            'max_open_positions': 3,
            'max_daily_trades': 10,
            'max_daily_loss_percent': 5.0,
            'max_position_duration_minutes': 720,  # Time stop (12h)
            'risk_reward_ratio': 2.0,  # Min risk/reward ratio
            'correlation_groups': [],  # [["BTC/USDT", "ETH/USDT"]]
            'max_positions_per_group': 1,
            'volatility_cooldown_multiplier': 0.0,  # Extend cooldown when ATR is high
            'volatility_cooldown_atr_threshold_pct': 2.0,  # Apply cooldown only above this ATR%
            'volatility_cooldown_max_extra': 2.0,  # Cap extension to 2x cooldown
            'close_all_on_loss_cut': False,  # If False, keep winners when loss cut hits
            'blocked_hours': []  # ["00:00-02:00"]
        }

    def reset_daily_stats(self):
        """Reset daily statistics"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_pnl = 0
            self.daily_trades = 0
            self.last_reset = today
            logger.info(f"📅 Daily statistics reset - New day: {today}")
        
        # CRITICAL FIX: Also reset if we're past midnight UTC
        # This ensures stats reset even if bot runs continuously
        now = datetime.now()
        if now.hour == 0 and now.minute < 15 and self.daily_trades > 0:
            # We're in the first 15 minutes of a new day and have trades counted
            # Force reset to ensure clean slate
            old_trades = self.daily_trades
            self.daily_pnl = 0
            self.daily_trades = 0
            self.last_reset = today
            logger.warning(f"🔄 FORCE daily reset (was {old_trades} trades) - Midnight passed")

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
        self.last_known_equity = capital

        # Enforce hard cap on risk per trade
        max_risk_pct = self.config.get('max_risk_per_trade_percent', risk_percent)
        effective_risk_pct = min(risk_percent, max_risk_pct)

        # Maximum position size based on config
        max_position_value = capital * (self.config['max_position_size_percent'] / 100)

        # Risk-based position sizing
        risk_amount = capital * (effective_risk_pct / 100)

        if stop_loss is None:
            logger.warning("Stop loss missing, defaulting to max position size cap")
            return max_position_value / entry_price

        # Add slippage buffer to stop distance to avoid oversizing
        price_diff = abs(entry_price - stop_loss)
        if self.slippage_buffer_percent:
            price_diff += entry_price * (self.slippage_buffer_percent / 100)

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

        logger.info(
            f"Calculated position size: {quantity:.4f} (value: ${quantity * entry_price:.2f}) "
            f"| risk {effective_risk_pct:.2f}% capped at {max_risk_pct:.2f}%"
        )
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

    def can_open_position(self, symbol: str,
                          market_context: Optional[Dict] = None,
                          current_equity: Optional[float] = None,
                          current_price: Optional[float] = None) -> Tuple[bool, str]:
        """
        Check if a new position can be opened

        Returns:
            Tuple of (can_open, reason)
        """
        self.reset_daily_stats()
        equity = current_equity or self.last_known_equity
        if equity:
            self.last_known_equity = equity

        # Hard trading curfew windows (e.g., low-liquidity hours)
        blocked_hours = self.config.get('blocked_hours', [])
        now = datetime.now().time()
        for window in blocked_hours:
            try:
                start_str, end_str = window.split('-')
                start = datetime.strptime(start_str, "%H:%M").time()
                end = datetime.strptime(end_str, "%H:%M").time()
                if start <= now <= end:
                    return False, f"Trading blocked during {window}"
            except Exception:
                logger.warning(f"Invalid blocked_hours window: {window}")

        # Daily loss cut - stop opening new trades
        daily_loss_pct = self.config.get('max_daily_loss_percent')
        if equity and daily_loss_pct and self.daily_pnl <= -(equity * daily_loss_pct / 100):
            return False, f"Daily loss limit reached ({daily_loss_pct}%)"

        # Check if position already exists
        if symbol in self.positions:
            return False, f"Position already open for {symbol}"

        # IN PAPER MODE: Skip daily trades and cooldown limits, but keep max positions
        if self.trading_mode == "paper":
            # Still check max open positions to avoid overexposure
            if len(self.positions) >= self.config['max_open_positions']:
                return False, f"Max positions ({self.config['max_open_positions']}) reached"
            return True, "OK (paper mode - limited checks)"

        # LIVE/TESTNET MODE: Apply all safety limits
        
        # Correlation exposure check
        groups = self.config.get('correlation_groups', [])
        max_group_positions = self.config.get('max_positions_per_group', 1)
        for group in groups:
            if symbol in group:
                open_in_group = sum(1 for sym in self.positions if sym in group)
                if open_in_group >= max_group_positions:
                    return False, f"Correlation limit reached for group {group}"

        # Cooldown check (extended when volatility is high)
        cooldown = self.config.get('cooldown_seconds')
        if cooldown and symbol in self.last_trade_time:
            elapsed = (datetime.now() - self.last_trade_time[symbol]).total_seconds()
            effective_cooldown = cooldown

            # Extend cooldown based on ATR percent if provided
            if market_context and current_price:
                atr = market_context.get('atr')
                if atr and atr > 0:
                    atr_pct = (atr / current_price) * 100
                    mult = self.config.get('volatility_cooldown_multiplier', 0.0)
                    threshold = self.config.get('volatility_cooldown_atr_threshold_pct', 0.0)
                    max_extra = self.config.get('volatility_cooldown_max_extra', 0.0)
                    if mult > 0 and atr_pct >= threshold:
                        extra = cooldown * mult * (atr_pct / 100)
                        if max_extra > 0:
                            extra = min(extra, cooldown * max_extra)
                        effective_cooldown += extra

            if elapsed < effective_cooldown:
                return False, f"Cooldown active ({int(effective_cooldown - elapsed)}s remaining)"

        # Check max open positions
        if len(self.positions) >= self.config['max_open_positions']:
            return False, f"Maximum open positions reached ({self.config['max_open_positions']})"

        # Check daily trade limit
        if self.daily_trades >= self.config['max_daily_trades']:
            return False, f"Daily trade limit reached ({self.config['max_daily_trades']})"

        return True, "OK"

    def open_position(self, symbol: str, side: str, entry_price: float,
                     quantity: float, stop_loss: float = None,
                     take_profit: float = None,
                     meta: Optional[Dict] = None,
                     current_equity: Optional[float] = None) -> Optional[Position]:
        """
        Open a new position

        Returns:
            Position object if successful, None otherwise
        """
        can_open, reason = self.can_open_position(
            symbol,
            market_context=meta,
            current_equity=current_equity,
            current_price=entry_price
        )
        if not can_open:
            logger.warning(f"Cannot open position: {reason}")
            return None

        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            meta=meta or {}
        )

        # Attach time stop if provided in meta or config
        if not position.max_duration_minutes:
            position.max_duration_minutes = self.config.get('max_position_duration_minutes')

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
        position.close(exit_price, cost_rate=self.trade_cost_percent)

        self.daily_pnl += position.pnl
        self.closed_positions.append(position)
        del self.positions[symbol]
        # Record last trade action time for cooldown logic
        self.last_trade_time[symbol] = datetime.now()

        logger.info(f"Closed position: {symbol} @ {exit_price} | PnL: ${position.pnl:.2f} | Reason: {reason}")
        return position

    def update_positions(self, prices: Dict[str, float],
                         market_contexts: Optional[Dict[str, Dict]] = None) -> List[Dict]:
        """
        Update all positions and check stop loss/take profit

        INTELLIGENT TRAILING STOP:
        - Only activates after +3% profit
        - Trails at 50% of profit (if +6%, trails to +3%)
        - Lets winners run, locks in gains

        Args:
            prices: Dict of {symbol: current_price}

        Returns:
            List of closed positions
        """
        closed = []

        # Global loss cut: close everything if daily loss limit breached
        equity_ref = self.last_known_equity
        loss_limit = self.config.get('max_daily_loss_percent')
        if equity_ref and loss_limit and self.daily_pnl <= -(equity_ref * loss_limit / 100):
            logger.error(f"🛑 Daily loss limit reached ({loss_limit}%), enforcing loss cut")
            close_all = self.config.get('close_all_on_loss_cut', False)
            for symbol, position in list(self.positions.items()):
                close_price = prices.get(symbol)
                if close_price is None:
                    continue
                # Keep winners if configured
                if not close_all:
                    position.update_pnl(close_price, cost_rate=self.trade_cost_percent)
                    if position.pnl > 0:
                        continue
                closed_pos = self.close_position(symbol, close_price, "Daily Loss Cut")
                if closed_pos:
                    closed.append(closed_pos.to_dict())
            return closed

        for symbol, position in list(self.positions.items()):
            if symbol not in prices:
                continue

            context = (market_contexts or {}).get(symbol, {})
            current_price = prices[symbol]
            position.update_pnl(current_price, cost_rate=self.trade_cost_percent)

            # Calculate profit stats
            if position.side == 'long':
                profit_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                price_move = current_price - position.entry_price
            else:  # short
                profit_pct = ((position.entry_price - current_price) / position.entry_price) * 100
                price_move = position.entry_price - current_price

            # Risk/Reward and break-even logic
            initial_risk = position.initial_risk or abs(position.entry_price * (self.config['stop_loss_percent'] / 100))
            rr = (price_move / initial_risk) if initial_risk else 0
            break_even_rr = self.config.get('break_even_rr', 1.0)

            if rr >= break_even_rr and not position.break_even_armed:
                # Move stop to break-even plus costs
                buffer = position.entry_price * (self.trade_cost_percent / 100)
                if position.side == 'long':
                    new_stop = position.entry_price + buffer
                    if not position.stop_loss or new_stop > position.stop_loss:
                        position.stop_loss = new_stop
                else:
                    new_stop = position.entry_price - buffer
                    if not position.stop_loss or new_stop < position.stop_loss:
                        position.stop_loss = new_stop
                position.break_even_armed = True
                logger.info(f"🛡️ Break-even stop armed for {symbol} at {position.stop_loss:.4f} (RR: {rr:.2f})")

            # Volatility-aware trailing stop
            atr = context.get('atr') or position.atr_at_entry
            trailing_stop = None
            if atr and atr > 0:
                atr_mult = self.config.get('atr_trailing_multiplier', 1.5)
                distance = atr * atr_mult
                if position.side == 'long':
                    trailing_stop = current_price - distance
                    if trailing_stop > (position.stop_loss or 0):
                        position.stop_loss = trailing_stop
                        logger.info(f"📈 ATR trailing stop update {symbol}: {trailing_stop:.4f} (ATR={atr:.4f})")
                else:
                    trailing_stop = current_price + distance
                    if not position.stop_loss or trailing_stop < position.stop_loss:
                        position.stop_loss = trailing_stop
                        logger.info(f"📈 ATR trailing stop update {symbol}: {trailing_stop:.4f} (ATR={atr:.4f})")

            # Profit-based trailing fallback when no ATR
            if not trailing_stop:
                MIN_PROFIT_TO_TRAIL = 3.0  # 3%
                PROFIT_LOCK_RATIO = 0.5    # Lock 50% of profit
                if profit_pct > MIN_PROFIT_TO_TRAIL:
                    locked_profit_pct = profit_pct * PROFIT_LOCK_RATIO
                    if position.side == 'long':
                        trailing_stop = position.entry_price * (1 + locked_profit_pct / 100)
                        if not position.stop_loss or trailing_stop > position.stop_loss:
                            position.stop_loss = trailing_stop
                            logger.info(f"📈 Trailing stop activated: {symbol} - Locking {locked_profit_pct:.1f}% profit (current: {profit_pct:.1f}%)")
                    else:
                        trailing_stop = position.entry_price * (1 - locked_profit_pct / 100)
                        if not position.stop_loss or trailing_stop < position.stop_loss:
                            position.stop_loss = trailing_stop
                            logger.info(f"📈 Trailing stop activated: {symbol} - Locking {locked_profit_pct:.1f}% profit (current: {profit_pct:.1f}%)")

            # Time-based exit
            if position.max_duration_minutes:
                age_minutes = (datetime.now() - position.entry_time).total_seconds() / 60
                if age_minutes > position.max_duration_minutes:
                    closed_pos = self.close_position(symbol, current_price, "Time Stop Hit")
                    if closed_pos:
                        closed.append(closed_pos.to_dict())
                    continue

            # Check stop loss (including trailing stop)
            if position.check_stop_loss(current_price):
                reason = "Trailing Stop Hit" if trailing_stop else "Stop Loss Hit"
                closed_pos = self.close_position(symbol, current_price, reason)
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
                position.update_pnl(current_prices[symbol], cost_rate=self.trade_cost_percent)
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
