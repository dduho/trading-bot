"""
Trade Database - Persistent storage for trade history and learning data
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)


class TradeDatabase:
    """
    Manages persistent storage of trade history, market conditions, and learning data.
    Provides foundation for machine learning and performance analysis.
    """

    def __init__(self, db_path: str = "data/trading_history.db"):
        """
        Initialize database connection and create tables if needed.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Trade database initialized at {db_path}")

    def _create_tables(self):
        """Create all necessary database tables."""
        cursor = self.conn.cursor()

        # Trades table - main trade history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP,
                pnl REAL,
                pnl_percent REAL,
                status TEXT NOT NULL,
                exit_reason TEXT,
                duration_minutes REAL,
                trading_mode TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Market conditions at trade entry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                macd_hist REAL,
                sma_short REAL,
                sma_long REAL,
                ema_short REAL,
                ema_long REAL,
                bb_upper REAL,
                bb_middle REAL,
                bb_lower REAL,
                atr REAL,
                volume REAL,
                volume_ratio REAL,
                trend TEXT,
                signal_confidence REAL,
                signal_reason TEXT,
                FOREIGN KEY (trade_id) REFERENCES trades (id)
            )
        """)

        # Strategy performance tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                strategy_name TEXT NOT NULL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                win_rate REAL,
                total_pnl REAL,
                avg_win REAL,
                avg_loss REAL,
                profit_factor REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                config_snapshot TEXT
            )
        """)

        # Model performance tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                accuracy REAL,
                precision_score REAL,
                recall REAL,
                f1_score REAL,
                auc_score REAL,
                training_samples INTEGER,
                validation_samples INTEGER,
                parameters TEXT,
                feature_importance TEXT
            )
        """)

        # Learning events - track when bot learns and adapts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                description TEXT,
                parameters_before TEXT,
                parameters_after TEXT,
                reason TEXT,
                impact_metric REAL
            )
        """)

        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conditions_trade_id ON trade_conditions(trade_id)")

        self.conn.commit()
        logger.info("Database tables created successfully")

    def insert_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Insert a new trade record.

        Args:
            trade_data: Dictionary containing trade information

        Returns:
            trade_id: ID of inserted trade
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO trades (
                symbol, side, entry_price, exit_price, quantity,
                stop_loss, take_profit, entry_time, exit_time,
                pnl, pnl_percent, status, exit_reason, duration_minutes, trading_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data.get('symbol'),
            trade_data.get('side'),
            trade_data.get('entry_price'),
            trade_data.get('exit_price'),
            trade_data.get('quantity'),
            trade_data.get('stop_loss'),
            trade_data.get('take_profit'),
            trade_data.get('entry_time'),
            trade_data.get('exit_time'),
            trade_data.get('pnl'),
            trade_data.get('pnl_percent'),
            trade_data.get('status'),
            trade_data.get('exit_reason'),
            trade_data.get('duration_minutes'),
            trade_data.get('trading_mode', 'paper')
        ))

        self.conn.commit()
        trade_id = cursor.lastrowid
        logger.info(f"Trade recorded: ID={trade_id}, Symbol={trade_data.get('symbol')}, Side={trade_data.get('side')}")
        return trade_id

    def update_trade(self, trade_id: int, update_data: Dict[str, Any]):
        """
        Update an existing trade record.

        Args:
            trade_id: ID of trade to update
            update_data: Dictionary with fields to update
        """
        cursor = self.conn.cursor()

        # Build dynamic UPDATE query
        fields = []
        values = []
        for key, value in update_data.items():
            fields.append(f"{key} = ?")
            values.append(value)

        values.append(trade_id)
        query = f"UPDATE trades SET {', '.join(fields)} WHERE id = ?"

        cursor.execute(query, values)
        self.conn.commit()
        logger.info(f"Trade {trade_id} updated")

    def insert_trade_conditions(self, trade_id: int, conditions: Dict[str, Any]):
        """
        Insert market conditions at time of trade entry.

        Args:
            trade_id: ID of associated trade
            conditions: Dictionary of market indicators and conditions
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO trade_conditions (
                trade_id, timestamp, rsi, macd, macd_signal, macd_hist,
                sma_short, sma_long, ema_short, ema_long,
                bb_upper, bb_middle, bb_lower, atr,
                volume, volume_ratio, trend,
                signal_confidence, signal_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_id,
            conditions.get('timestamp'),
            conditions.get('rsi'),
            conditions.get('macd'),
            conditions.get('macd_signal'),
            conditions.get('macd_hist'),
            conditions.get('sma_short'),
            conditions.get('sma_long'),
            conditions.get('ema_short'),
            conditions.get('ema_long'),
            conditions.get('bb_upper'),
            conditions.get('bb_middle'),
            conditions.get('bb_lower'),
            conditions.get('atr'),
            conditions.get('volume'),
            conditions.get('volume_ratio'),
            conditions.get('trend'),
            conditions.get('signal_confidence'),
            conditions.get('signal_reason')
        ))

        self.conn.commit()

    def get_trade_history(self, limit: int = 100, symbol: Optional[str] = None,
                         status: Optional[str] = None) -> List[Dict]:
        """
        Retrieve trade history with optional filters.

        Args:
            limit: Maximum number of trades to return
            symbol: Filter by specific symbol
            status: Filter by status (open/closed)

        Returns:
            List of trade dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY entry_time DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_trade_with_conditions(self, trade_id: int) -> Optional[Dict]:
        """
        Get complete trade information including market conditions.

        Args:
            trade_id: ID of trade to retrieve

        Returns:
            Dictionary with trade and conditions data
        """
        cursor = self.conn.cursor()

        # Get trade data
        cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
        trade = cursor.fetchone()

        if not trade:
            return None

        trade_dict = dict(trade)

        # Get conditions
        cursor.execute("SELECT * FROM trade_conditions WHERE trade_id = ?", (trade_id,))
        conditions = cursor.fetchone()

        if conditions:
            trade_dict['conditions'] = dict(conditions)

        return trade_dict

    def get_winning_trades(self, limit: int = 100) -> List[Dict]:
        """Get all winning trades for analysis."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.*, tc.*
            FROM trades t
            LEFT JOIN trade_conditions tc ON t.id = tc.trade_id
            WHERE UPPER(t.status) = 'CLOSED' AND t.pnl > 0
            ORDER BY t.entry_time DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_losing_trades(self, limit: int = 100) -> List[Dict]:
        """Get all losing trades for analysis."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.*, tc.*
            FROM trades t
            LEFT JOIN trade_conditions tc ON t.id = tc.trade_id
            WHERE UPPER(t.status) = 'CLOSED' AND t.pnl < 0
            ORDER BY t.entry_time DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_trades_for_ml(self, min_trades: int = 50) -> List[Dict]:
        """
        Get closed trades with complete condition data for ML training.

        Args:
            min_trades: Minimum number of trades required

        Returns:
            List of trades with conditions, ready for ML
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.*, tc.*
            FROM trades t
            INNER JOIN trade_conditions tc ON t.id = tc.trade_id
            WHERE UPPER(t.status) = 'CLOSED' AND t.pnl IS NOT NULL
            ORDER BY t.entry_time DESC
        """)

        trades = [dict(row) for row in cursor.fetchall()]

        if len(trades) < min_trades:
            logger.warning(f"Only {len(trades)} trades available, need {min_trades} for ML training")

        return trades

    def insert_strategy_performance(self, perf_data: Dict[str, Any]):
        """Record strategy performance snapshot."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO strategy_performance (
                strategy_name, total_trades, winning_trades, losing_trades,
                win_rate, total_pnl, avg_win, avg_loss, profit_factor,
                sharpe_ratio, max_drawdown, config_snapshot
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            perf_data.get('strategy_name'),
            perf_data.get('total_trades'),
            perf_data.get('winning_trades'),
            perf_data.get('losing_trades'),
            perf_data.get('win_rate'),
            perf_data.get('total_pnl'),
            perf_data.get('avg_win'),
            perf_data.get('avg_loss'),
            perf_data.get('profit_factor'),
            perf_data.get('sharpe_ratio'),
            perf_data.get('max_drawdown'),
            json.dumps(perf_data.get('config', {}))
        ))

        self.conn.commit()

    def insert_model_performance(self, model_data: Dict[str, Any]):
        """Record ML model performance metrics."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO model_performance (
                model_name, model_version, accuracy, precision_score, recall,
                f1_score, auc_score, training_samples, validation_samples,
                parameters, feature_importance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model_data.get('model_name'),
            model_data.get('model_version'),
            model_data.get('accuracy'),
            model_data.get('precision'),
            model_data.get('recall'),
            model_data.get('f1_score'),
            model_data.get('auc_score'),
            model_data.get('training_samples'),
            model_data.get('validation_samples'),
            json.dumps(model_data.get('parameters', {})),
            json.dumps(model_data.get('feature_importance', {}))
        ))

        self.conn.commit()

    def insert_learning_event(self, event_type: str, description: str,
                            params_before: Dict, params_after: Dict,
                            reason: str, impact: float = 0.0):
        """
        Record a learning event when bot adapts its strategy.

        Args:
            event_type: Type of learning event (e.g., 'weight_adjustment', 'threshold_change')
            description: Human-readable description
            params_before: Parameters before adaptation
            params_after: Parameters after adaptation
            reason: Reason for adaptation
            impact: Measured or estimated impact of change
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO learning_events (
                event_type, description, parameters_before, parameters_after,
                reason, impact_metric
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event_type,
            description,
            json.dumps(params_before),
            json.dumps(params_after),
            reason,
            impact
        ))

        self.conn.commit()
        logger.info(f"Learning event recorded: {event_type} - {description}")

    def get_performance_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate performance statistics over specified period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with performance metrics
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                AVG(CASE WHEN pnl > 0 THEN pnl ELSE NULL END) as avg_win,
                AVG(CASE WHEN pnl < 0 THEN pnl ELSE NULL END) as avg_loss,
                SUM(pnl) as total_pnl,
                MAX(pnl) as largest_win,
                MIN(pnl) as largest_loss,
                AVG(duration_minutes) as avg_duration
            FROM trades
            WHERE UPPER(status) = 'CLOSED'
                AND entry_time >= datetime('now', '-' || ? || ' days')
        """, (days,))

        row = cursor.fetchone()

        if row and row['total_trades'] > 0:
            stats = dict(row)
            stats['win_rate'] = stats['winning_trades'] / stats['total_trades'] if stats['total_trades'] > 0 else 0

            # Assurer que les valeurs ne sont pas None
            stats['avg_win'] = stats['avg_win'] or 0.0
            stats['avg_loss'] = stats['avg_loss'] or 0.0
            stats['total_pnl'] = stats['total_pnl'] or 0.0

            # Calculate profit factor
            if stats['avg_loss'] and stats['avg_loss'] != 0 and stats['losing_trades'] > 0:
                stats['profit_factor'] = abs((stats['winning_trades'] * stats['avg_win']) /
                                            (stats['losing_trades'] * stats['avg_loss']))
            else:
                stats['profit_factor'] = 0.0

            return stats

        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
