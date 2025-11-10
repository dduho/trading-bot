"""
Telegram Commands Handler
Gère les commandes interactives envoyées par l'utilisateur au bot Telegram
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from notification_formatter import NotificationFormatter

logger = logging.getLogger(__name__)


class TelegramCommandHandler:
    """Gestionnaire de commandes Telegram interactives"""
    
    def __init__(self, config, trading_bot):
        """
        Args:
            config: Configuration du bot
            trading_bot: Instance du TradingBot pour accéder aux données
        """
        self.config = config
        self.bot = trading_bot
        
        # Initialiser le formatter avec config
        formatting_config = config.get('notifications', {}).get('telegram', {}).get('formatting', {
            'use_emoji': True,
            'use_markdown': True,
            'timezone': 'UTC'
        })
        self.formatter = NotificationFormatter(formatting_config)
        
        self.application = None
        
        # Récupérer le chat_id depuis les variables d'environnement ou config
        import os
        self.authorized_chat_id = str(os.getenv('TELEGRAM_CHAT_ID', config.get('notifications', {}).get('telegram', {}).get('chat_id', '')))
        
        logger.info("TelegramCommandHandler initialisé")
    
    def _is_authorized(self, update: Update) -> bool:
        """Vérifie que la commande vient du chat autorisé"""
        if not update.effective_chat:
            return False
        return str(update.effective_chat.id) == self.authorized_chat_id
    
    async def start(self):
        """Démarre le gestionnaire de commandes"""
        try:
            import os
            token = os.getenv('TELEGRAM_BOT_TOKEN', self.config.get('notifications', {}).get('telegram', {}).get('bot_token'))
            if not token:
                logger.warning("Pas de token Telegram, commandes désactivées")
                return
            
            # Créer l'application
            self.application = Application.builder().token(token).build()
            
            # Enregistrer les commandes
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("help", self.cmd_help))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("ml", self.cmd_ml))
            self.application.add_handler(CommandHandler("positions", self.cmd_positions))
            self.application.add_handler(CommandHandler("performance", self.cmd_performance))
            self.application.add_handler(CommandHandler("today", self.cmd_today))
            
            # Démarrer l'application en mode polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("✅ Commandes Telegram activées")
            
        except Exception as e:
            logger.error(f"Erreur démarrage commandes Telegram: {e}")
    
    async def stop(self):
        """Arrête le gestionnaire de commandes"""
        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Commandes Telegram arrêtées")
            except Exception as e:
                logger.error(f"Erreur arrêt commandes: {e}")
    
    # ========================================================================
    # COMMANDES
    # ========================================================================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start - Message de bienvenue"""
        if not self._is_authorized(update):
            await update.message.reply_text("❌ Non autorisé")
            return
        
        message = (
            "🤖 *Trading Bot - Commandes Disponibles*\n\n"
            "/status - État actuel du bot et portfolio\n"
            "/ml - Progression et métriques ML\n"
            "/positions - Positions ouvertes actuellement\n"
            "/performance - Statistiques de performance globales\n"
            "/today - Résumé de la journée\n"
            "/help - Afficher cette aide\n\n"
            "💡 _Le bot envoie aussi des notifications automatiques pour tous les événements importants_"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /help - Aide"""
        await self.cmd_start(update, context)
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /status - État complet du bot et système"""
        if not self._is_authorized(update):
            await update.message.reply_text("❌ Non autorisé")
            return
        
        try:
            # === ÉTAT DU BOT ===
            mode = str(self.bot.trading_mode.value).upper()
            is_running = self.bot.running
            status_emoji = "🟢" if is_running else "🔴"
            status_text = "EN COURS" if is_running else "ARRÊTÉ"
            
            # Symboles et configuration
            symbols = ', '.join(self.bot.symbols)
            timeframe = self.bot.timeframe
            update_interval = self.bot.update_interval
            
            # Uptime
            if hasattr(self.bot, 'start_time'):
                uptime = datetime.now() - self.bot.start_time
                uptime_str = self.bot._format_duration(int(uptime.total_seconds() / 60))
            else:
                uptime_str = "N/A"
            
            # === SYSTÈME ML ===
            ml_status = "❌ Désactivé"
            next_learning = "N/A"
            
            if hasattr(self.bot, 'learning_engine') and self.bot.learning_engine:
                learning_params = self.bot.learning_engine.get_current_strategy_params()
                ml_enabled = learning_params.get('learning_enabled', False)
                
                if ml_enabled:
                    ml_status = "✅ Actif"
                    
                    # Prochaine analyse ML
                    if hasattr(self.bot.learning_engine, 'last_learning_time'):
                        last_time = self.bot.learning_engine.last_learning_time
                        interval_hours = self.bot.learning_engine.config.get('learning_interval_hours', 2)
                        if last_time:
                            from datetime import timedelta
                            next_time = last_time + timedelta(hours=interval_hours)
                            remaining = next_time - datetime.now()
                            if remaining.total_seconds() > 0:
                                next_learning = self.bot._format_duration(int(remaining.total_seconds() / 60))
                            else:
                                next_learning = "Bientôt"
                        else:
                            next_learning = f"Dans {interval_hours}h (depuis démarrage)"
            
            # === ACTIVITÉ DE TRADING ===
            # Récupérer tous les trades
            all_trades = self.bot.trade_db.get_all_trades(limit=1000)
            closed_trades = [t for t in all_trades if t.get('exit_time')]
            
            # Stats globales
            total_trades = len(closed_trades)
            winning_trades = len([t for t in closed_trades if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in closed_trades if t.get('pnl', 0) <= 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Trades aujourd'hui
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_trades = [
                t for t in closed_trades 
                if t.get('exit_time') and datetime.fromisoformat(t['exit_time']) >= today_start
            ]
            today_total = len(today_trades)
            today_wins = len([t for t in today_trades if t.get('pnl', 0) > 0])
            today_losses = len([t for t in today_trades if t.get('pnl', 0) <= 0])
            
            # === PORTFOLIO ===
            portfolio = self.bot._get_portfolio_info()
            
            # === ADAPTATIONS ML RÉCENTES ===
            adaptations_text = ""
            if hasattr(self.bot, 'learning_engine') and self.bot.learning_engine:
                try:
                    learning_params = self.bot.learning_engine.get_current_strategy_params()
                    current_weights = learning_params.get('weights', {})
                    
                    # Top 3 indicateurs les plus importants
                    sorted_weights = sorted(current_weights.items(), key=lambda x: x[1], reverse=True)[:3]
                    if sorted_weights:
                        adaptations_text = "\n\n📊 *Indicateurs Principaux ML:*"
                        for indicator, weight in sorted_weights:
                            adaptations_text += f"\n• {indicator}: {weight:.1%}"
                except:
                    pass
            
            # === SCANNER DE MARCHÉ ===
            scan_status = "🔍 Scan actif" if is_running else "⏸️ En pause"
            scan_info = f"Toutes les {update_interval}s" if is_running else "Arrêté"
            
            # === CONSTRUCTION DU MESSAGE ===
            message = (
                f"🤖 *ÉTAT DU BOT*\n\n"
                f"{status_emoji} Statut: `{status_text}`\n"
                f"📊 Mode: `{mode}`\n"
                f"⏱ Uptime: `{uptime_str}`\n\n"
                
                f"� *SCANNER DE MARCHÉ*\n\n"
                f"{scan_status}\n"
                f"�💱 Symboles: `{symbols}`\n"
                f"⏱ Timeframe: `{timeframe}`\n"
                f"� Fréquence: `{scan_info}`\n\n"
                
                f"🧠 *SYSTÈME ML*\n\n"
                f"{ml_status}\n"
                f"⏰ Prochain cycle: `{next_learning}`{adaptations_text}\n\n"
                
                f"� *PERFORMANCE GLOBALE*\n\n"
                f"Total Trades: `{total_trades}`\n"
                f"✅ Gagnants: `{winning_trades}` ({win_rate:.1f}%)\n"
                f"❌ Perdants: `{losing_trades}`\n\n"
                
                f"📅 *AUJOURD'HUI*\n\n"
                f"Trades: `{today_total}`\n"
                f"✅ Gagnants: `{today_wins}`\n"
                f"❌ Perdants: `{today_losses}`\n"
                f"PnL: `${portfolio['today_pnl']:.2f}` ({portfolio['today_pnl_percent']:.2f}%)\n\n"
                
                f"💰 *PORTFOLIO*\n\n"
                f"Balance: `${portfolio['balance']:.2f}`\n"
                f"Positions ouvertes: `{portfolio['open_positions']}`\n"
                f"PnL Total: `${portfolio['total_pnl']:.2f}` ({portfolio['total_pnl_percent']:.2f}%)"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur commande /status: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def cmd_ml(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /ml - Métriques ML"""
        if not self._is_authorized(update):
            await update.message.reply_text("❌ Non autorisé")
            return
        
        try:
            # Récupérer les métriques ML
            if hasattr(self.bot, 'ml_optimizer') and self.bot.ml_optimizer:
                metrics = self.bot.ml_optimizer.get_current_metrics()
                
                message = (
                    f"🧠 *Système d'Apprentissage*\n\n"
                    f"📈 Précision: `{metrics.get('accuracy', 0):.1f}%`\n"
                    f"🎯 Win Rate: `{metrics.get('win_rate', 0):.1f}%`\n"
                    f"💹 Sharpe Ratio: `{metrics.get('sharpe_ratio', 0):.2f}`\n"
                    f"📊 Trades analysés: `{metrics.get('total_trades', 0)}`\n"
                    f"🔄 Cycles ML: `{metrics.get('learning_cycles', 0)}`\n\n"
                    f"⚙️ *Paramètres Actuels*\n\n"
                    f"RSI: `{metrics.get('rsi_period', 14)}`\n"
                    f"Confiance min: `{metrics.get('min_confidence', 0.6):.2f}`\n"
                    f"Stop Loss: `{metrics.get('stop_loss', 2.0):.1f}%`\n"
                    f"Take Profit: `{metrics.get('take_profit', 5.0):.1f}%`\n\n"
                    f"🕐 Dernier apprentissage: `{metrics.get('last_learning', 'Jamais')}`"
                )
            else:
                message = "⚠️ Système ML non initialisé"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur commande /ml: {e}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /positions - Positions ouvertes"""
        if not self._is_authorized(update):
            await update.message.reply_text("❌ Non autorisé")
            return
        
        try:
            # Récupérer les positions ouvertes
            positions = self.bot.trade_db.get_open_positions()
            
            if not positions:
                await update.message.reply_text("📭 Aucune position ouverte")
                return
            
            message = f"📊 *Positions Ouvertes* ({len(positions)})\n\n"
            
            for pos in positions:
                side_emoji = "🟢" if pos['side'] == 'buy' else "🔴"
                entry_time = datetime.fromisoformat(pos['entry_time'])
                duration = datetime.now() - entry_time
                duration_str = self.bot._format_duration(int(duration.total_seconds() / 60))
                
                # Calculer PnL actuel (simplifié, faudrait le prix actuel)
                unrealized_pnl = pos.get('unrealized_pnl', 0)
                
                message += (
                    f"{side_emoji} *{pos['side'].upper()}* {pos['symbol']}\n"
                    f"Prix: `${pos['entry_price']:.2f}`\n"
                    f"Montant: `${pos['amount']:.4f}`\n"
                    f"Durée: `{duration_str}`\n"
                    f"PnL: `${unrealized_pnl:.2f}`\n\n"
                )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur commande /positions: {e}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def cmd_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /performance - Statistiques globales"""
        if not self._is_authorized(update):
            await update.message.reply_text("❌ Non autorisé")
            return
        
        try:
            # Récupérer toutes les trades fermées
            all_trades = self.bot.trade_db.get_all_trades(limit=1000)
            closed_trades = [t for t in all_trades if t.get('exit_time')]
            
            if not closed_trades:
                await update.message.reply_text("📭 Aucune trade fermée pour statistiques")
                return
            
            # Calculer les stats
            total_trades = len(closed_trades)
            winning_trades = len([t for t in closed_trades if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in closed_trades if t.get('pnl', 0) <= 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = sum(t.get('pnl', 0) for t in closed_trades)
            avg_win = sum(t.get('pnl', 0) for t in closed_trades if t.get('pnl', 0) > 0) / winning_trades if winning_trades > 0 else 0
            avg_loss = sum(t.get('pnl', 0) for t in closed_trades if t.get('pnl', 0) <= 0) / losing_trades if losing_trades > 0 else 0
            
            message = (
                f"📊 *Performance Globale*\n\n"
                f"📈 Total Trades: `{total_trades}`\n"
                f"✅ Gagnants: `{winning_trades}` ({win_rate:.1f}%)\n"
                f"❌ Perdants: `{losing_trades}`\n\n"
                f"💰 *Résultats*\n\n"
                f"PnL Total: `${total_pnl:.2f}`\n"
                f"Gain Moyen: `${avg_win:.2f}`\n"
                f"Perte Moyenne: `${avg_loss:.2f}`\n"
                f"Ratio: `{abs(avg_win/avg_loss) if avg_loss != 0 else 0:.2f}`"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur commande /performance: {e}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def cmd_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /today - Résumé du jour"""
        if not self._is_authorized(update):
            await update.message.reply_text("❌ Non autorisé")
            return
        
        try:
            # Trades du jour
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            all_trades = self.bot.trade_db.get_all_trades(limit=1000)
            today_trades = [
                t for t in all_trades 
                if t.get('entry_time') and datetime.fromisoformat(t['entry_time']) >= today_start
            ]
            
            closed_today = [t for t in today_trades if t.get('exit_time')]
            open_today = [t for t in today_trades if not t.get('exit_time')]
            
            # Stats du jour
            total_today = len(today_trades)
            winning_today = len([t for t in closed_today if t.get('pnl', 0) > 0])
            losing_today = len([t for t in closed_today if t.get('pnl', 0) <= 0])
            pnl_today = sum(t.get('pnl', 0) for t in closed_today)
            
            message = (
                f"📅 *Résumé du {datetime.now().strftime('%d/%m/%Y')}*\n\n"
                f"📊 Trades: `{total_today}`\n"
                f"🔒 Fermées: `{len(closed_today)}`\n"
                f"🔓 Ouvertes: `{len(open_today)}`\n\n"
                f"✅ Gagnants: `{winning_today}`\n"
                f"❌ Perdants: `{losing_today}`\n\n"
                f"💰 PnL Aujourd'hui: `${pnl_today:.2f}`"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur commande /today: {e}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
