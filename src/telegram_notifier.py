"""
Service de notifications Telegram pour le trading bot.
Gère l'envoi de notifications formatées avec rate limiting et gestion d'erreurs.
"""

from telegram import Bot
from telegram.error import TelegramError
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
from notification_formatter import NotificationFormatter

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Service de notifications Telegram pour le trading bot.
    
    Responsabilités:
    - Envoyer des notifications formatées
    - Gérer le rate limiting
    - Gérer la file d'attente des messages
    - Gérer les erreurs d'envoi
    """
    
    def __init__(self, config: Dict):
        """
        Initialiser le notifier.
        
        Args:
            config: Configuration du bot (depuis config.yaml)
        """
        load_dotenv()
        
        # Récupérer les credentials
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID doivent être définis dans .env")
        
        # Initialiser le bot
        self.bot = Bot(token=self.bot_token)
        
        # Configuration
        self.config = config.get('notifications', {}).get('telegram', {})
        self.enabled = self.config.get('enabled', True)
        
        # Rate limiting
        self.rate_limit = self.config.get('rate_limit', {})
        self.max_messages_per_hour = self.rate_limit.get('max_messages_per_hour', 30)
        self.cooldown = self.rate_limit.get('cooldown_between_messages', 2)
        
        # Historique des messages pour rate limiting
        self.message_history: List[datetime] = []
        self.last_message_time: Optional[datetime] = None
        
        # File d'attente pour messages en attente
        self.message_queue: List[str] = []
        
        # Formatter
        self.formatter = NotificationFormatter(self.config.get('formatting', {}))
        
        logger.info("Telegram Notifier initialized")
    
    async def send_trade_notification(self, action: str, **kwargs):
        """
        Envoyer notification de trade.
        
        Args:
            action: 'OPEN' ou 'CLOSE'
            **kwargs: Données du trade
        """
        if not self.config.get('trades', {}).get('enabled', True):
            return
        
        # Vérifier si on doit notifier selon min_pnl_percent
        if action == 'CLOSE':
            min_pnl = self.config.get('trades', {}).get('min_pnl_percent', 0.0)
            pnl_percent = kwargs.get('pnl_percent', 0)
            if abs(pnl_percent) < min_pnl:
                logger.debug(f"Trade notification skipped: PnL {pnl_percent}% < min {min_pnl}%")
                return
        
        # Formater le message
        message = self.formatter.format_trade(action, **kwargs)
        
        # Envoyer
        await self._send_message(message)
    
    async def send_learning_notification(self, **kwargs):
        """
        Envoyer notification de learning cycle.
        
        Args:
            **kwargs: Données du learning cycle
        """
        if not self.config.get('learning', {}).get('enabled', True):
            return
        
        message = self.formatter.format_learning(**kwargs)
        await self._send_message(message)
    
    async def send_error_notification(self, module: str, **kwargs):
        """
        Envoyer notification d'erreur.
        
        Args:
            module: Nom du module où l'erreur s'est produite
            **kwargs: Détails de l'erreur
        """
        if not self.config.get('errors', {}).get('enabled', True):
            return
        
        # Vérifier si on veut seulement les erreurs critiques
        if self.config.get('errors', {}).get('critical_only', False):
            if kwargs.get('severity') != 'critical':
                return
        
        message = self.formatter.format_error(module, **kwargs)
        await self._send_message(message, urgent=True)
    
    async def send_status_report(self, **kwargs):
        """
        Envoyer rapport de statut.
        
        Args:
            **kwargs: Données du statut
        """
        if not self.config.get('reports', {}).get('enabled', True):
            return
        
        message = self.formatter.format_status_report(**kwargs)
        await self._send_message(message)
    
    async def send_info_notification(self, message: str):
        """
        Envoyer notification d'information simple.
        
        Args:
            message: Texte du message
        """
        await self._send_message(message)
    
    async def _send_message(self, text: str, parse_mode: str = 'Markdown', urgent: bool = False):
        """
        Envoyer un message via Telegram Bot API.

        Args:
            text: Contenu du message
            parse_mode: Format ('Markdown' ou 'HTML')
            urgent: Si True, bypass le rate limiting
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled, message not sent")
            return

        # Vérifier le rate limiting (sauf si urgent)
        if not urgent and not self._check_rate_limit():
            logger.warning(f"Rate limit reached, adding message to queue ({len(self.message_queue)} in queue)")
            self._add_to_queue(text)
            return

        # Vérifier le cooldown
        if self.last_message_time and not urgent:
            time_since_last = (datetime.now() - self.last_message_time).total_seconds()
            if time_since_last < self.cooldown:
                await asyncio.sleep(self.cooldown - time_since_last)

        try:
            # Créer un nouveau bot pour éviter les conflits d'event loop
            # (le bot Telegram garde une référence à l'event loop de création)
            bot = Bot(token=self.bot_token)

            # Envoyer le message
            await bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )

            # Mettre à jour l'historique
            now = datetime.now()
            self.message_history.append(now)
            self.last_message_time = now

            logger.info("Telegram notification sent successfully")

        except TelegramError as e:
            # Logger l'erreur mais ne pas crasher le bot
            logger.error(f"Failed to send Telegram notification: {e}")

            # Si le message est urgent, réessayer une fois
            if urgent:
                await asyncio.sleep(5)
                try:
                    bot_retry = Bot(token=self.bot_token)
                    await bot_retry.send_message(
                        chat_id=self.chat_id,
                        text=f"⚠️ *Erreur précédente non envoyée*\n\n{text}",
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )
                    logger.info("Urgent message sent on retry")
                except Exception as retry_error:
                    logger.error(f"Failed to send urgent message even on retry: {retry_error}")

        except Exception as e:
            logger.error(f"Unknown error in HTTP implementation: {type(e).__name__}('{e}')", exc_info=False)
    
    def _check_rate_limit(self) -> bool:
        """
        Vérifier si on peut envoyer un message selon le rate limit.
        
        Returns:
            True si on peut envoyer, False sinon
        """
        now = datetime.now()
        
        # Nettoyer l'historique (garder seulement dernière heure)
        one_hour_ago = now - timedelta(hours=1)
        self.message_history = [
            msg_time for msg_time in self.message_history
            if msg_time > one_hour_ago
        ]
        
        # Vérifier la limite
        can_send = len(self.message_history) < self.max_messages_per_hour
        
        if not can_send:
            logger.warning(f"Rate limit reached: {len(self.message_history)}/{self.max_messages_per_hour} messages in the last hour")
        
        return can_send
    
    def _add_to_queue(self, message: str):
        """
        Ajouter un message à la file d'attente.
        
        Args:
            message: Message à ajouter
        """
        self.message_queue.append(message)
        
        # Limiter la taille de la queue
        if len(self.message_queue) > 50:
            dropped = self.message_queue.pop(0)
            logger.warning("Message queue full, dropping oldest message")
    
    async def process_queue(self):
        """Traiter la file d'attente des messages"""
        processed = 0
        
        while self.message_queue and self._check_rate_limit():
            message = self.message_queue.pop(0)
            await self._send_message(message)
            await asyncio.sleep(self.cooldown)
            processed += 1
        
        if processed > 0:
            logger.info(f"Processed {processed} queued messages, {len(self.message_queue)} remaining")
        
        return processed
    
    async def test_connection(self) -> bool:
        """
        Tester la connexion au bot Telegram.
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Connected to Telegram bot: @{bot_info.username} (ID: {bot_info.id})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Telegram bot: {e}")
            return False
