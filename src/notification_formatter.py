"""
Formatage des messages de notification pour Telegram.
Gère le formatage Markdown, les emojis et la troncature des messages.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
import pytz


class NotificationFormatter:
    """
    Formater les messages de notification pour Telegram.
    
    Gère:
    - Formatage Markdown
    - Ajout d'emojis
    - Troncature des messages trop longs
    - Formatage des nombres (prix, pourcentages)
    """
    
    def __init__(self, formatting_config: Dict):
        """
        Args:
            formatting_config: Config de formatage depuis config.yaml
        """
        self.use_emoji = formatting_config.get('use_emoji', True)
        self.use_markdown = formatting_config.get('use_markdown', True)
        self.timezone = formatting_config.get('timezone', 'UTC')
        
        try:
            self.tz = pytz.timezone(self.timezone)
        except:
            self.tz = pytz.UTC
    
    def format_trade(self, action: str, **kwargs) -> str:
        """
        Formater une notification de trade.
        
        Args:
            action: 'OPEN' ou 'CLOSE'
            **kwargs: Données du trade
            
        Returns:
            Message formaté en Markdown
        """
        if action == 'OPEN':
            return self._format_trade_open(**kwargs)
        elif action == 'CLOSE':
            return self._format_trade_close(**kwargs)
        else:
            return f"⚠️ Action inconnue: {action}"
    
    def _format_trade_open(self, **kwargs) -> str:
        """Formater une ouverture de position"""
        emoji = "🟢" if self.use_emoji else ""
        header = f"{emoji} *POSITION OUVERTE*"
        
        symbol = kwargs.get('symbol', 'N/A')
        side = kwargs.get('side', 'N/A')
        entry_price = kwargs.get('entry_price', 0)
        quantity = kwargs.get('quantity', 0)
        position_value = kwargs.get('position_value', 0)
        stop_loss = kwargs.get('stop_loss')
        take_profit = kwargs.get('take_profit')
        signal_data = kwargs.get('signal_data', {})
        portfolio = kwargs.get('portfolio_info', {})
        
        # Calculer les pourcentages SL/TP si disponibles
        sl_text = ""
        tp_text = ""
        if stop_loss and entry_price:
            sl_percent = ((stop_loss - entry_price) / entry_price) * 100
            sl_text = f"*Stop Loss:* ${self._format_price(stop_loss)} ({self._format_percent(sl_percent)}%)\n"
        if take_profit and entry_price:
            tp_percent = ((take_profit - entry_price) / entry_price) * 100
            tp_text = f"*Take Profit:* ${self._format_price(take_profit)} ({self._format_percent(tp_percent)}%)\n"
        
        base_asset = symbol.split('/')[0] if '/' in symbol else symbol
        
        message = f"""{header}

*Symbol:* `{symbol}`
*Side:* {side}
*Entry Price:* ${self._format_price(entry_price)}
*Quantity:* {self._format_price(quantity, 4)} {base_asset}
*Position Value:* ${self._format_price(position_value)} USDT

{sl_text}{tp_text}
*Signal Strength:* {signal_data.get('confidence', 0):.2f}

📊 *Positions:* {portfolio.get('open_positions', 0)}/{portfolio.get('max_positions', 3)}
💰 *Portfolio:* ${self._format_price(portfolio.get('balance', 0))} USDT

🕐 {self._format_timestamp()}"""
        
        return self._truncate(message.strip())
    
    def _format_trade_close(self, **kwargs) -> str:
        """Formater une fermeture de position"""
        pnl = kwargs.get('pnl', 0)
        pnl_percent = kwargs.get('pnl_percent', 0)
        
        emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪" if self.use_emoji else ""
        header = f"{emoji} *POSITION FERMÉE*"
        
        symbol = kwargs.get('symbol', 'N/A')
        exit_price = kwargs.get('exit_price', 0)
        entry_price = kwargs.get('entry_price', 0)
        quantity = kwargs.get('quantity', 0)
        duration = kwargs.get('duration', 'N/A')
        reason = kwargs.get('reason', 'Manual')
        portfolio = kwargs.get('portfolio_info', {})
        
        pnl_emoji = "✅" if pnl > 0 else "❌" if pnl < 0 else "➖" if self.use_emoji else ""
        pnl_label = "PROFIT" if pnl > 0 else "PERTE" if pnl < 0 else "BREAK-EVEN"
        
        base_asset = symbol.split('/')[0] if '/' in symbol else symbol
        
        message = f"""{header}

*Symbol:* `{symbol}`
*Exit Price:* ${self._format_price(exit_price)}
*Quantity:* {self._format_price(quantity, 4)} {base_asset}

*Entry:* ${self._format_price(entry_price)} → *Exit:* ${self._format_price(exit_price)}
*Duration:* {duration}

{pnl_emoji} *{pnl_label}:* {self._format_percent(pnl_percent, sign=True)}% (${self._format_price(pnl, sign=True)} USDT)
*Raison:* {reason}

📊 *Positions:* {portfolio.get('open_positions', 0)}/{portfolio.get('max_positions', 3)}
💰 *Portfolio:* ${self._format_price(portfolio.get('balance', 0))} USDT

🕐 {self._format_timestamp()}"""
        
        return self._truncate(message.strip())
    
    def format_learning(self, **kwargs) -> str:
        """Formater une notification de cycle d'apprentissage"""
        emoji = "🧠" if self.use_emoji else ""
        header = f"{emoji} *CYCLE D'APPRENTISSAGE TERMINÉ*"
        
        duration = kwargs.get('duration', 0)
        trades_analyzed = kwargs.get('trades_analyzed', 0)
        model_metrics = kwargs.get('model_metrics', {})
        weight_changes = kwargs.get('weight_changes', {})
        adaptations = kwargs.get('adaptations', [])
        performance = kwargs.get('performance', {})
        
        # Métriques du modèle
        metrics_text = ""
        if model_metrics:
            accuracy = model_metrics.get('accuracy', 0)
            precision = model_metrics.get('precision', 0)
            recall = model_metrics.get('recall', 0)
            f1 = model_metrics.get('f1_score', 0)
            auc = model_metrics.get('auc_score', 0)
            
            metrics_text = f"""
*Métriques du modèle:*
• Accuracy: {accuracy:.1%}
• Precision: {precision:.1%}
• Recall: {recall:.1%}
• F1-Score: {f1:.2f}
• ROC-AUC: {auc:.2f}"""
        
        # Changements de poids
        weights_text = ""
        if weight_changes:
            weights_text = "\n*Optimisation des poids:*"
            for indicator, change in list(weight_changes.items())[:5]:
                sign = "+" if change > 0 else ""
                weights_text += f"\n• {indicator}: {sign}{change:.2f}%"
        
        # Adaptations
        adaptations_text = ""
        if adaptations:
            adaptations_text = "\n*Adaptations appliquées:*"
            for adaptation in adaptations[:3]:
                adaptations_text += f"\n✅ {adaptation}"
        
        # Performance
        perf_text = ""
        if performance:
            win_rate = performance.get('win_rate', 0)
            total_pnl = performance.get('total_pnl', 0)
            profit_factor = performance.get('profit_factor', 0)
            
            perf_text = f"""
*Performance récente:*
📈 Win Rate: {win_rate:.1f}%
💰 Total PnL: ${self._format_price(total_pnl, sign=True)} USDT
📊 Profit Factor: {profit_factor:.2f}"""
        
        message = f"""{header}

*Durée:* {duration:.1f} secondes
*Trades analysés:* {trades_analyzed}
{metrics_text}
{weights_text}
{adaptations_text}
{perf_text}

🕐 {self._format_timestamp()}"""
        
        return self._truncate(message.strip())
    
    def format_error(self, module: str, **kwargs) -> str:
        """Formater une notification d'erreur"""
        severity = kwargs.get('severity', 'warning')
        emoji = "🚨" if severity == 'critical' else "⚠️" if self.use_emoji else ""
        header_label = "ERREUR CRITIQUE" if severity == 'critical' else "AVERTISSEMENT"
        header = f"{emoji} *{header_label}*"
        
        error_type = kwargs.get('error_type', 'Unknown')
        error_message = kwargs.get('error_message', 'N/A')
        context = kwargs.get('context', {})
        
        context_text = ""
        if context:
            context_text = "\n*Contexte:*"
            for key, value in list(context.items())[:5]:
                context_text += f"\n• {key}: {value}"
        
        message = f"""{header}

*Module:* {module}
*Type:* {error_type}

*Message:*
{error_message}
{context_text}

🕐 {self._format_timestamp()}"""
        
        return self._truncate(message.strip())
    
    def format_status_report(self, **kwargs) -> str:
        """Formater un rapport de statut complet"""
        emoji = "📊" if self.use_emoji else ""
        
        stats = kwargs.get('stats', {})
        portfolio = kwargs.get('portfolio', {})
        positions = kwargs.get('positions', [])
        ml_status = kwargs.get('ml_status', {})
        trading_mode = kwargs.get('trading_mode', 'UNKNOWN')
        uptime = kwargs.get('uptime', 'N/A')
        
        # Stats de trading
        total_trades = stats.get('total_trades', 0)
        winning_trades = stats.get('winning_trades', 0)
        losing_trades = stats.get('losing_trades', 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = stats.get('total_pnl', 0)
        
        # Positions ouvertes
        positions_text = ""
        if positions:
            positions_text = "\n*Positions ouvertes:*"
            for pos in positions[:5]:
                symbol = pos.get('symbol', 'N/A')
                pnl = pos.get('unrealized_pnl', 0)
                pnl_pct = pos.get('unrealized_pnl_percent', 0)
                positions_text += f"\n├─ {symbol}: {self._format_percent(pnl_pct, sign=True)}% (${self._format_price(pnl, sign=True)})"
        
        # ML status
        ml_text = ""
        if ml_status:
            ml_accuracy = ml_status.get('accuracy', 0)
            ml_enabled = ml_status.get('enabled', False)
            ml_text = f"""
*ML Learning:*
├─ Status: {'✅ Enabled' if ml_enabled else '❌ Disabled'}
└─ Model Accuracy: {ml_accuracy:.1%}"""
        
        message = f"""{emoji} *RAPPORT QUOTIDIEN*

═══════════════════════
*RÉSUMÉ*
═══════════════════════

*Trades exécutés:* {total_trades}
├─ Gagnants: {winning_trades} ({win_rate:.1f}%)
├─ Perdants: {losing_trades}
└─ Win Rate: {win_rate:.1f}%

*Performance:*
└─ PnL Total: ${self._format_price(total_pnl, sign=True)} ({self._format_percent(stats.get('total_pnl_percent', 0), sign=True)}%)

═══════════════════════
*PORTFOLIO*
═══════════════════════

*Solde:* ${self._format_price(portfolio.get('balance', 0))} USDT
*Positions:* {len(positions)}/{portfolio.get('max_positions', 3)}
{positions_text}

═══════════════════════
*STATUS*
═══════════════════════

*Mode:* {trading_mode}
*Uptime:* {uptime}
{ml_text}

🕐 {self._format_timestamp()}"""
        
        return self._truncate(message.strip())
    
    def _format_price(self, price: float, decimals: int = 2, sign: bool = False) -> str:
        """Formater un prix"""
        if price == 0:
            return "0.00"
        
        formatted = f"{abs(price):.{decimals}f}"
        
        if sign and price != 0:
            return f"+{formatted}" if price > 0 else f"-{formatted}"
        
        return formatted
    
    def _format_percent(self, percent: float, decimals: int = 2, sign: bool = False) -> str:
        """Formater un pourcentage"""
        if percent == 0:
            return "0.00"
        
        formatted = f"{abs(percent):.{decimals}f}"
        
        if sign:
            return f"+{formatted}" if percent > 0 else f"-{formatted}"
        
        return formatted
    
    def _format_timestamp(self, timestamp: Optional[float] = None) -> str:
        """Formater un timestamp"""
        if timestamp:
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)
        
        # Convertir au timezone configuré
        dt_local = dt.astimezone(self.tz)
        
        return dt_local.strftime('%Y-%m-%d %H:%M:%S %Z')
    
    def _truncate(self, text: str, max_length: int = 4096) -> str:
        """Tronquer un message trop long (limite Telegram: 4096 chars)"""
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length - 50]
        return truncated + "\n\n... (message tronqué)"
    
    def _get_rsi_label(self, rsi: Optional[float]) -> str:
        """Obtenir le label RSI"""
        if rsi is None:
            return "N/A"
        if rsi < 30:
            return "survente"
        elif rsi > 70:
            return "surachat"
        else:
            return "neutre"
    
    def _get_macd_label(self, macd: Optional[float]) -> str:
        """Obtenir le label MACD"""
        if macd is None:
            return "N/A"
        if macd > 0:
            return "haussier"
        elif macd < 0:
            return "baissier"
        else:
            return "neutre"
    
    def _get_ma_status(self, signal_data: Dict) -> str:
        """Obtenir le statut des moyennes mobiles"""
        ema = signal_data.get('ema', 0)
        sma = signal_data.get('sma', 0)
        
        if ema > sma:
            return "EMA > SMA (trend haussier)"
        elif ema < sma:
            return "EMA < SMA (trend baissier)"
        else:
            return "EMA = SMA (neutre)"
    
    def _get_volume_status(self, signal_data: Dict) -> str:
        """Obtenir le statut du volume"""
        volume_change = signal_data.get('volume_change', 0)
        
        if volume_change > 20:
            return f"+{volume_change:.0f}% (fort momentum)"
        elif volume_change < -20:
            return f"{volume_change:.0f}% (faible momentum)"
        else:
            return f"{volume_change:+.0f}% (normal)"
