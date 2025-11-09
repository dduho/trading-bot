# Processus de Mise en Place des Notifications Telegram

## Table des Matières
1. [Vue d'ensemble](#vue-densemble)
2. [Prérequis](#prérequis)
3. [Architecture proposée](#architecture-proposée)
4. [Configuration](#configuration)
5. [Types de notifications](#types-de-notifications)
6. [Points d'intégration](#points-dintégration)
7. [Implémentation technique](#implémentation-technique)
8. [Sécurité](#sécurité)
9. [Tests](#tests)
10. [Déploiement](#déploiement)

---

## Vue d'ensemble

Le système de notifications Telegram permettra de recevoir en temps réel des alertes sur les activités du trading bot :
- Ouverture/fermeture de positions
- Résultats des cycles d'apprentissage ML
- Alertes d'erreurs critiques
- Rapports de performance périodiques

**Avantages** :
- ✅ Surveillance en temps réel depuis votre téléphone
- ✅ Historique des notifications dans Telegram
- ✅ Possibilité de commandes interactives (optionnel)
- ✅ Pas besoin de consulter les logs en permanence

---

## Prérequis

### 1. Créer un Bot Telegram

**Étapes :**

1. **Ouvrir Telegram** et rechercher `@BotFather`

2. **Créer un nouveau bot** :
   ```
   /newbot
   ```

3. **Choisir un nom** (ex: "Mon Trading Bot Notifier")

4. **Choisir un username** (ex: "my_trading_bot_notifier_bot")
   - Doit se terminer par "bot"
   - Doit être unique

5. **Récupérer le token** fourni par BotFather :
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-1234567
   ```
   ⚠️ **À garder secret !**

6. **Démarrer une conversation** avec votre bot :
   - Chercher le bot par son username
   - Cliquer sur "Start"

### 2. Obtenir votre Chat ID

**Option A : Via un bot helper**
1. Rechercher `@userinfobot` sur Telegram
2. Démarrer la conversation
3. Il vous enverra votre Chat ID

**Option B : Via l'API Telegram**
1. Envoyer un message à votre bot
2. Aller sur :
   ```
   https://api.telegram.org/bot<VOTRE_TOKEN>/getUpdates
   ```
3. Chercher `"chat":{"id":123456789}`

**Option C : Via un script Python**
```python
import requests

token = "VOTRE_TOKEN"
url = f"https://api.telegram.org/bot{token}/getUpdates"
response = requests.get(url)
print(response.json())
```

### 3. Installer la dépendance Python

```bash
pip install python-telegram-bot==20.7
```

ou ajouter au `requirements.txt` :
```
python-telegram-bot==20.7
```

---

## Architecture proposée

### Structure des fichiers

```
trading-bot/
├── src/
│   ├── trading_bot.py              # Existant
│   ├── telegram_notifier.py        # NOUVEAU - Service de notifications
│   ├── notification_formatter.py   # NOUVEAU - Formatage des messages
│   └── ...autres fichiers existants
├── config.yaml                      # Mise à jour pour config Telegram
├── .env                             # Ajout TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID
└── TELEGRAM_NOTIFICATIONS_PROCESS.md
```

### Composants

```
┌─────────────────────────────────────────────────────────────┐
│                      Trading Bot                            │
│                                                             │
│  ┌──────────────┐    ┌────────────────────────────────┐   │
│  │ TradingBot   │───▶│  TelegramNotifier              │   │
│  │              │    │  - send_trade_notification()   │   │
│  │ - execute_   │    │  - send_learning_notification()│   │
│  │   signal()   │    │  - send_error_notification()   │   │
│  │ - update_    │    │  - send_status_report()        │   │
│  │   positions()│    └────────────────────────────────┘   │
│  │ - learning_  │                    │                     │
│  │   cycle()    │                    │                     │
│  └──────────────┘                    ▼                     │
│                          ┌────────────────────────┐        │
│                          │ NotificationFormatter  │        │
│                          │ - format_trade()       │        │
│                          │ - format_learning()    │        │
│                          │ - format_error()       │        │
│                          └────────────────────────┘        │
│                                      │                     │
└──────────────────────────────────────┼─────────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────┐
                        │   Telegram Bot API       │
                        └──────────────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────┐
                        │   Votre Telegram App     │
                        └──────────────────────────┘
```

---

## Configuration

### 1. Fichier `.env`

Ajouter les variables suivantes :

```bash
# Telegram Notifications
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-1234567
TELEGRAM_CHAT_ID=123456789

# Optionnel : Configuration avancée
TELEGRAM_ENABLED=true
TELEGRAM_NOTIFICATION_LEVEL=all  # all, trades_only, errors_only, summary_only
TELEGRAM_RATE_LIMIT=30  # Nombre max de messages par heure
```

### 2. Fichier `config.yaml`

Mettre à jour la section notifications :

```yaml
notifications:
  enabled: true
  telegram:
    enabled: true
    # Types de notifications à envoyer
    trades:
      enabled: true
      include_entry: true
      include_exit: true
      min_pnl_percent: 0.0  # Notifier seulement si PnL > X%
    learning:
      enabled: true
      include_adaptations: true
      include_metrics: true
    errors:
      enabled: true
      critical_only: false
    reports:
      enabled: true
      schedule: "daily"  # daily, every_6h, every_12h
      time: "20:00"  # Heure du rapport quotidien

    # Formatage
    formatting:
      use_emoji: true
      use_markdown: true
      include_charts: false  # Optionnel : graphiques de performance
      timezone: "Europe/Paris"

    # Rate limiting pour éviter le spam
    rate_limit:
      max_messages_per_hour: 30
      cooldown_between_messages: 2  # secondes
```

---

## Types de notifications

### 1. Notifications de Trading

#### A. Ouverture de position
```
🟢 POSITION OUVERTE

Symbol: SOL/USDT
Side: BUY (LONG)
Entry Price: $142.35
Quantity: 0.0352 SOL
Position Value: $5.00 USDT (5.0% du portfolio)

Stop Loss: $139.50 (-2.0%)
Take Profit: $151.08 (+6.0%)

Signal Strength: 0.72 (STRONG_BUY)

Conditions d'entrée:
• RSI: 42.5 (neutral)
• MACD: +0.85 (bullish)
• MA: EMA > SMA (trend haussier)
• Volume: +25% (fort momentum)

📊 Positions ouvertes: 2/3
💰 Portfolio: $100.00 USDT

🕐 2025-11-09 14:32:15 UTC
```

#### B. Fermeture de position
```
🔴 POSITION FERMÉE

Symbol: SOL/USDT
Side: SELL (Clôture LONG)
Exit Price: $148.72
Quantity: 0.0352 SOL

Entry: $142.35 → Exit: $148.72
Duration: 1h 23min

✅ PROFIT: +$0.22 (+4.48%)
Raison: Take Profit atteint

📊 Positions ouvertes: 1/3
💰 Portfolio: $100.22 USDT (+0.22%)

🕐 2025-11-09 15:55:42 UTC
```

#### C. Stop Loss déclenché
```
⚠️ STOP LOSS DÉCLENCHÉ

Symbol: AVAX/USDT
Side: SELL (Clôture LONG)
Exit Price: $39.15
Quantity: 0.128 AVAX

Entry: $40.02 → Exit: $39.15
Duration: 28min

❌ PERTE: -$0.11 (-2.17%)
Raison: Stop Loss (-2.0%)

💡 Conditions de sortie:
• Prix a chuté de -2.17%
• Volume de vente élevé
• RSI tombé à 28 (survente)

📊 Positions ouvertes: 0/3
💰 Portfolio: $99.89 USDT (-0.11%)

🕐 2025-11-09 16:12:08 UTC
```

### 2. Notifications d'Apprentissage ML

```
🧠 CYCLE D'APPRENTISSAGE TERMINÉ

Durée: 12.3 secondes
Trades analysés: 47

Métriques du modèle:
• Accuracy: 62.5% (+2.5%)
• Precision: 68.3%
• Recall: 58.7%
• F1-Score: 0.63
• ROC-AUC: 0.71

Optimisation des poids:
• Moving Averages: 33.05% → 35.12% (+2.07%)
• MACD: 21.16% → 19.88% (-1.28%)
• RSI: 17.71% → 18.45% (+0.74%)
• Volume: 17.52% → 16.33% (-1.19%)
• Trend: 10.57% → 10.22% (-0.35%)

Adaptations appliquées:
✅ Poids des indicateurs optimisés
✅ Threshold min_confidence ajusté: 0.60 → 0.62

Performance récente:
📈 Win Rate: 58.3% (28W / 19L)
💰 Total PnL: +$12.45 (+12.45%)
📊 Profit Factor: 2.18
🎯 Sharpe Ratio: 1.72

Prochain cycle: dans 2 heures

🕐 2025-11-09 16:30:45 UTC
```

### 3. Notifications d'Erreurs

#### A. Erreur critique
```
🚨 ERREUR CRITIQUE

Module: OrderExecutor
Type: InsufficientFunds

Message:
Fonds insuffisants pour exécuter l'ordre BUY sur SOL/USDT.
Required: 5.00 USDT
Available: 3.22 USDT

Action recommandée:
• Vérifier le solde sur l'exchange
• Réduire max_position_size dans config.yaml
• Attendre la clôture de positions ouvertes

Status: Trading en pause (mode sécurisé)

🕐 2025-11-09 17:05:23 UTC
```

#### B. Erreur réseau
```
⚠️ AVERTISSEMENT

Module: MarketDataFeed
Type: NetworkError

Message:
Impossible de récupérer les données OHLCV de Binance.
Connection timeout après 30s.

Tentatives: 3/5
Prochaine tentative: dans 60s

Status: Bot en mode dégradé (utilise cache)

🕐 2025-11-09 17:12:15 UTC
```

### 4. Rapports de Performance

#### A. Rapport quotidien
```
📊 RAPPORT QUOTIDIEN
🗓️ Samedi 9 Novembre 2025

═══════════════════════════
RÉSUMÉ DU JOUR
═══════════════════════════

Trades exécutés: 12
├─ Gagnants: 8 (66.7%)
├─ Perdants: 4 (33.3%)
└─ Win Rate: 66.7%

Performance:
├─ PnL Total: +$4.85 (+4.85%)
├─ Meilleur trade: +$1.22 (SOL/USDT, +8.5%)
├─ Pire trade: -$0.35 (DOGE/USDT, -2.1%)
└─ Profit Factor: 2.45

Symboles tradés:
• SOL/USDT: 4 trades (+$2.10)
• AVAX/USDT: 3 trades (+$1.45)
• MATIC/USDT: 3 trades (+$0.92)
• DOGE/USDT: 2 trades (+$0.38)

Durée moyenne: 1h 42min
Temps total en position: 14h 23min

═══════════════════════════
APPRENTISSAGE ML
═══════════════════════════

Cycles exécutés: 4
Model Accuracy: 62.5%
Adaptations appliquées: 8

Performance ML:
├─ Précision prédictions: 68.3%
├─ Signaux filtrés: 18
└─ Signaux acceptés: 12

═══════════════════════════
PORTFOLIO
═══════════════════════════

Solde initial: $100.00
Solde actuel: $104.85
PnL cumulé: +$4.85 (+4.85%)

Positions ouvertes: 1
├─ ADA/USDT: +$0.12 (+2.4%)
└─ Valeur totale: $5.00

Solde disponible: $99.85

═══════════════════════════
STATS DU MOIS
═══════════════════════════

Total PnL (Nov): +$24.32 (+24.32%)
Win Rate: 64.2%
Meilleur jour: +$8.15 (04 Nov)
Trades total: 87 (56W / 31L)

═══════════════════════════

Mode: PAPER TRADING
Prochaine learning cycle: 21:45

🕐 2025-11-09 20:00:00 UTC
```

### 5. Notifications de Statut

```
ℹ️ BOT STATUS

Status: ✅ Running
Mode: PAPER TRADING
Uptime: 2 jours 14h 32min

Exchange: Binance
Connexion: ✅ Stable
API Rate: 42/1200 req/min

Positions ouvertes: 2/3
├─ SOL/USDT: +$0.35 (+7.0%)
└─ AVAX/USDT: -$0.08 (-1.6%)

ML Learning:
├─ Status: Enabled
├─ Model Accuracy: 62.5%
└─ Prochain cycle: 45min

Portfolio:
├─ Solde: $104.85
├─ Jour: +$4.85 (+4.85%)
└─ Total: +$24.32 (+24.32%)

🕐 2025-11-09 18:30:00 UTC
```

---

## Points d'intégration

### 1. Dans `trading_bot.py`

#### Point A : Initialisation (ligne ~210)
```python
def __init__(self, config_path: str = 'config.yaml'):
    # ... code existant ...

    # NOUVEAU : Initialiser le notifier Telegram
    if self.config.get('notifications', {}).get('telegram', {}).get('enabled', False):
        from telegram_notifier import TelegramNotifier
        self.telegram = TelegramNotifier(self.config)
        logger.info("Telegram notifications enabled")
    else:
        self.telegram = None
        logger.info("Telegram notifications disabled")
```

#### Point B : Ouverture de position (ligne ~347)
```python
def execute_signal(self, analysis: Dict):
    # ... code existant d'exécution de l'ordre ...

    if order_result['success']:
        # ... code existant ...
        self._print_trade(...)

        # NOUVEAU : Envoyer notification Telegram
        if self.telegram:
            await self.telegram.send_trade_notification(
                action='OPEN',
                symbol=symbol,
                side=action,
                entry_price=price,
                quantity=quantity,
                position_value=position_value,
                stop_loss=stop_loss,
                take_profit=take_profit,
                signal_data=analysis,
                portfolio_info=self._get_portfolio_info()
            )
```

#### Point C : Fermeture de position (ligne ~422)
```python
def _close_position(self, position: Position, reason: str):
    # ... code existant de fermeture ...

    if close_result['success']:
        # ... code existant ...
        self._print_close(...)

        # NOUVEAU : Envoyer notification Telegram
        if self.telegram:
            await self.telegram.send_trade_notification(
                action='CLOSE',
                symbol=position.symbol,
                side='SELL' if position.side == 'buy' else 'BUY',
                entry_price=position.entry_price,
                exit_price=exit_price,
                quantity=position.quantity,
                pnl=pnl,
                pnl_percent=pnl_percent,
                duration=duration,
                reason=reason,
                exit_conditions=self._get_exit_conditions(position),
                portfolio_info=self._get_portfolio_info()
            )
```

#### Point D : Cycle d'apprentissage (ligne ~654)
```python
async def execute_learning_cycle(self):
    # ... code existant du learning cycle ...

    if learning_results['success']:
        logger.info("Learning cycle completed successfully")

        # NOUVEAU : Envoyer notification Telegram
        if self.telegram:
            await self.telegram.send_learning_notification(
                duration=learning_results['duration'],
                trades_analyzed=learning_results['trades_count'],
                model_metrics=learning_results['metrics'],
                weight_changes=learning_results['weight_changes'],
                adaptations=learning_results['adaptations'],
                performance_stats=learning_results['performance']
            )
```

#### Point E : Gestion des erreurs (plusieurs endroits)
```python
except Exception as e:
    logger.error(f"Error: {str(e)}", exc_info=True)

    # NOUVEAU : Envoyer notification d'erreur
    if self.telegram:
        await self.telegram.send_error_notification(
            module=self.__class__.__name__,
            error_type=type(e).__name__,
            error_message=str(e),
            traceback_info=traceback.format_exc(),
            severity='critical' if isinstance(e, CriticalError) else 'warning',
            context={'symbol': symbol, 'action': action}
        )
```

#### Point F : Rapport périodique (nouvelle méthode)
```python
async def send_periodic_report(self):
    """Envoyer un rapport périodique via Telegram"""
    if not self.telegram:
        return

    # Récupérer les statistiques
    stats = self.db.get_performance_stats(period='1d')
    portfolio = self._get_portfolio_info()
    positions = self.risk_manager.get_all_positions()
    ml_status = self._get_ml_status()

    # Envoyer le rapport
    await self.telegram.send_status_report(
        stats=stats,
        portfolio=portfolio,
        positions=positions,
        ml_status=ml_status,
        trading_mode=self.trading_mode,
        uptime=self._get_uptime()
    )
```

### 2. Dans `run_loop()` (ligne ~622)

```python
async def run_loop(self):
    last_report_time = time.time()
    report_interval = self._get_report_interval()  # Ex: 24h

    while self.running:
        try:
            # ... code existant ...

            # NOUVEAU : Envoyer rapport périodique
            if self.telegram and (time.time() - last_report_time) >= report_interval:
                await self.send_periodic_report()
                last_report_time = time.time()

            await asyncio.sleep(15)

        except KeyboardInterrupt:
            # NOUVEAU : Notification d'arrêt
            if self.telegram:
                await self.telegram.send_info_notification(
                    "🛑 Bot arrêté manuellement (Ctrl+C)"
                )
            break
```

---

## Implémentation technique

### 1. Fichier `src/telegram_notifier.py`

**Structure de classe principale :**

```python
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
        pass

    async def send_trade_notification(self, action: str, **kwargs):
        """Envoyer une notification de trade (ouverture/fermeture)"""
        pass

    async def send_learning_notification(self, **kwargs):
        """Envoyer une notification de cycle d'apprentissage"""
        pass

    async def send_error_notification(self, module: str, **kwargs):
        """Envoyer une notification d'erreur"""
        pass

    async def send_status_report(self, **kwargs):
        """Envoyer un rapport de statut complet"""
        pass

    async def send_info_notification(self, message: str):
        """Envoyer une notification d'information simple"""
        pass

    async def _send_message(self, text: str, parse_mode: str = 'Markdown'):
        """Méthode interne pour envoyer un message"""
        pass

    def _check_rate_limit(self) -> bool:
        """Vérifier si on peut envoyer un message (rate limiting)"""
        pass

    def _add_to_queue(self, message: str):
        """Ajouter un message à la file d'attente"""
        pass
```

**Détails d'implémentation :**

```python
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

class TelegramNotifier:
    def __init__(self, config: Dict):
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
        from notification_formatter import NotificationFormatter
        self.formatter = NotificationFormatter(self.config.get('formatting', {}))

    async def send_trade_notification(self, action: str, **kwargs):
        """Envoyer notification de trade"""
        if not self.config.get('trades', {}).get('enabled', True):
            return

        # Vérifier si on doit notifier selon min_pnl_percent
        if action == 'CLOSE':
            min_pnl = self.config.get('trades', {}).get('min_pnl_percent', 0.0)
            if kwargs.get('pnl_percent', 0) < min_pnl:
                return  # Ne pas notifier les petits profits

        # Formater le message
        message = self.formatter.format_trade(action, **kwargs)

        # Envoyer
        await self._send_message(message)

    async def send_learning_notification(self, **kwargs):
        """Envoyer notification de learning cycle"""
        if not self.config.get('learning', {}).get('enabled', True):
            return

        message = self.formatter.format_learning(**kwargs)
        await self._send_message(message)

    async def send_error_notification(self, module: str, **kwargs):
        """Envoyer notification d'erreur"""
        if not self.config.get('errors', {}).get('enabled', True):
            return

        # Vérifier si on veut seulement les erreurs critiques
        if self.config.get('errors', {}).get('critical_only', False):
            if kwargs.get('severity') != 'critical':
                return

        message = self.formatter.format_error(module, **kwargs)
        await self._send_message(message, urgent=True)

    async def send_status_report(self, **kwargs):
        """Envoyer rapport de statut"""
        if not self.config.get('reports', {}).get('enabled', True):
            return

        message = self.formatter.format_status_report(**kwargs)
        await self._send_message(message)

    async def send_info_notification(self, message: str):
        """Envoyer notification simple"""
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
            return

        # Vérifier le rate limiting (sauf si urgent)
        if not urgent and not self._check_rate_limit():
            self._add_to_queue(text)
            return

        # Vérifier le cooldown
        if self.last_message_time and not urgent:
            time_since_last = (datetime.now() - self.last_message_time).total_seconds()
            if time_since_last < self.cooldown:
                await asyncio.sleep(self.cooldown - time_since_last)

        try:
            # Envoyer le message
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )

            # Mettre à jour l'historique
            now = datetime.now()
            self.message_history.append(now)
            self.last_message_time = now

        except TelegramError as e:
            # Logger l'erreur mais ne pas crasher le bot
            import logging
            logging.error(f"Failed to send Telegram notification: {e}")

            # Si le message est urgent, réessayer une fois
            if urgent:
                await asyncio.sleep(5)
                try:
                    await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=f"⚠️ Erreur précédente non envoyée. Voici le contenu:\n\n{text}",
                        parse_mode=parse_mode
                    )
                except:
                    pass  # Abandonner après 2e tentative

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
        return len(self.message_history) < self.max_messages_per_hour

    def _add_to_queue(self, message: str):
        """Ajouter un message à la file d'attente"""
        self.message_queue.append(message)

        # Limiter la taille de la queue
        if len(self.message_queue) > 50:
            self.message_queue.pop(0)

    async def process_queue(self):
        """Traiter la file d'attente des messages"""
        while self.message_queue and self._check_rate_limit():
            message = self.message_queue.pop(0)
            await self._send_message(message)
            await asyncio.sleep(self.cooldown)
```

### 2. Fichier `src/notification_formatter.py`

**Structure :**

```python
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

    def format_trade(self, action: str, **kwargs) -> str:
        """Formater une notification de trade"""
        pass

    def format_learning(self, **kwargs) -> str:
        """Formater une notification de learning cycle"""
        pass

    def format_error(self, module: str, **kwargs) -> str:
        """Formater une notification d'erreur"""
        pass

    def format_status_report(self, **kwargs) -> str:
        """Formater un rapport de statut complet"""
        pass

    def _format_price(self, price: float, decimals: int = 2) -> str:
        """Formater un prix"""
        pass

    def _format_percent(self, percent: float, decimals: int = 2) -> str:
        """Formater un pourcentage"""
        pass

    def _format_timestamp(self, timestamp: Optional[float] = None) -> str:
        """Formater un timestamp"""
        pass

    def _truncate(self, text: str, max_length: int = 4096) -> str:
        """Tronquer un message trop long (limite Telegram: 4096 chars)"""
        pass
```

**Exemple de méthode `format_trade()` :**

```python
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
        emoji = "🟢" if self.use_emoji else ""
        header = f"{emoji} POSITION OUVERTE"

        symbol = kwargs.get('symbol')
        side = kwargs.get('side')
        entry_price = kwargs.get('entry_price')
        quantity = kwargs.get('quantity')
        position_value = kwargs.get('position_value')
        stop_loss = kwargs.get('stop_loss')
        take_profit = kwargs.get('take_profit')
        signal_data = kwargs.get('signal_data', {})
        portfolio = kwargs.get('portfolio_info', {})

        # Calculer les pourcentages SL/TP
        sl_percent = ((stop_loss - entry_price) / entry_price) * 100
        tp_percent = ((take_profit - entry_price) / entry_price) * 100

        message = f"""
{header}

*Symbol:* `{symbol}`
*Side:* {side} (LONG)
*Entry Price:* ${self._format_price(entry_price)}
*Quantity:* {self._format_price(quantity, 4)} {symbol.split('/')[0]}
*Position Value:* ${self._format_price(position_value)} USDT ({portfolio.get('position_size_percent', 0)}% du portfolio)

*Stop Loss:* ${self._format_price(stop_loss)} ({self._format_percent(sl_percent)}%)
*Take Profit:* ${self._format_price(take_profit)} ({self._format_percent(tp_percent)}%)

*Signal Strength:* {signal_data.get('confidence', 0):.2f} ({signal_data.get('action', 'N/A')})

*Conditions d'entrée:*
• RSI: {signal_data.get('rsi', 0):.1f} ({self._get_rsi_label(signal_data.get('rsi'))})
• MACD: {signal_data.get('macd', 0):+.2f} ({self._get_macd_label(signal_data.get('macd'))})
• MA: {self._get_ma_status(signal_data)}
• Volume: {self._get_volume_status(signal_data)}

📊 *Positions ouvertes:* {portfolio.get('open_positions', 0)}/{portfolio.get('max_positions', 3)}
💰 *Portfolio:* ${self._format_price(portfolio.get('balance', 0))} USDT

🕐 {self._format_timestamp()}
"""

    elif action == 'CLOSE':
        pnl = kwargs.get('pnl', 0)
        pnl_percent = kwargs.get('pnl_percent', 0)
        emoji = "🟢" if pnl > 0 else "🔴" if self.use_emoji else ""
        header = f"{emoji} POSITION FERMÉE"

        symbol = kwargs.get('symbol')
        exit_price = kwargs.get('exit_price')
        entry_price = kwargs.get('entry_price')
        quantity = kwargs.get('quantity')
        duration = kwargs.get('duration', 'N/A')
        reason = kwargs.get('reason', 'Manual')
        portfolio = kwargs.get('portfolio_info', {})

        pnl_emoji = "✅" if pnl > 0 else "❌" if self.use_emoji else ""
        pnl_label = "PROFIT" if pnl > 0 else "PERTE"

        message = f"""
{header}

*Symbol:* `{symbol}`
*Side:* SELL (Clôture LONG)
*Exit Price:* ${self._format_price(exit_price)}
*Quantity:* {self._format_price(quantity, 4)} {symbol.split('/')[0]}

*Entry:* ${self._format_price(entry_price)} → *Exit:* ${self._format_price(exit_price)}
*Duration:* {duration}

{pnl_emoji} *{pnl_label}:* {self._format_percent(pnl_percent, sign=True)}% (${self._format_price(pnl, sign=True)} USDT)
*Raison:* {reason}

📊 *Positions ouvertes:* {portfolio.get('open_positions', 0)}/{portfolio.get('max_positions', 3)}
💰 *Portfolio:* ${self._format_price(portfolio.get('balance', 0))} USDT ({self._format_percent(portfolio.get('total_pnl_percent', 0), sign=True)}%)

🕐 {self._format_timestamp()}
"""

    return self._truncate(message.strip())
```

---

## Sécurité

### 1. Gestion des Secrets

**IMPORTANT :**
- ❌ **NE JAMAIS** committer `.env` dans Git
- ✅ Ajouter `.env` au `.gitignore`
- ✅ Utiliser `.env.example` comme template
- ✅ Stocker les secrets dans des variables d'environnement ou un gestionnaire de secrets

**Fichier `.gitignore` :**
```
.env
*.log
__pycache__/
models/*.pkl
data/*.db
```

### 2. Validation du Bot Token et Chat ID

```python
def validate_telegram_credentials(bot_token: str, chat_id: str) -> bool:
    """
    Valider que le bot token et chat ID sont valides.

    Returns:
        True si valide, False sinon
    """
    try:
        import re

        # Valider format du token : "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        token_pattern = r'^\d+:[A-Za-z0-9_-]+$'
        if not re.match(token_pattern, bot_token):
            return False

        # Valider format du chat ID : nombre (positif ou négatif)
        if not chat_id.lstrip('-').isdigit():
            return False

        # Tester la connexion
        bot = Bot(token=bot_token)
        bot.get_me()  # Lève une exception si token invalide

        return True

    except Exception as e:
        logger.error(f"Invalid Telegram credentials: {e}")
        return False
```

### 3. Rate Limiting et Protection Anti-Spam

**Limites de l'API Telegram :**
- Max 30 messages/seconde par bot
- Max 1 message/seconde par chat privé
- Max 4096 caractères par message

**Protection implémentée :**
- Rate limiting configurable (30 msg/heure par défaut)
- Cooldown entre messages (2 secondes)
- File d'attente pour messages en excès
- Troncature automatique des messages longs

### 4. Gestion des Erreurs Réseau

```python
async def _send_message_with_retry(self, text: str, max_retries: int = 3):
    """Envoyer un message avec retry automatique"""
    for attempt in range(max_retries):
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode='Markdown'
            )
            return True
        except TelegramError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to send message after {max_retries} attempts: {e}")
                return False
```

### 5. Sanitization des Messages

```python
def _sanitize_markdown(self, text: str) -> str:
    """
    Échapper les caractères spéciaux Markdown pour éviter les erreurs de parsing.

    Caractères à échapper: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    special_chars = r'_*[]()~`>#+-=|{}.!'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
```

---

## Tests

### 1. Script de Test Initial

**Fichier `scripts/test_telegram.py` :**

```python
#!/usr/bin/env python3
"""
Script de test pour les notifications Telegram.
Usage: python scripts/test_telegram.py
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

async def test_telegram_connection():
    """Tester la connexion au bot Telegram"""
    load_dotenv()

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID non défini dans .env")
        return False

    print(f"🔍 Test de connexion...")
    print(f"   Bot Token: {bot_token[:10]}...{bot_token[-10:]}")
    print(f"   Chat ID: {chat_id}")

    try:
        bot = Bot(token=bot_token)

        # Obtenir les infos du bot
        bot_info = await bot.get_me()
        print(f"\n✅ Bot connecté: @{bot_info.username}")
        print(f"   Nom: {bot_info.first_name}")
        print(f"   ID: {bot_info.id}")

        # Envoyer un message de test
        print(f"\n📤 Envoi d'un message de test...")
        message = await bot.send_message(
            chat_id=chat_id,
            text="🤖 *Test de connexion réussi!*\n\nLe bot de notifications Telegram est configuré correctement.",
            parse_mode='Markdown'
        )

        print(f"✅ Message envoyé (ID: {message.message_id})")
        print(f"\n✅ Configuration Telegram OK!")
        return True

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_telegram_connection())
    exit(0 if success else 1)
```

### 2. Test des Notifications

**Fichier `scripts/test_notifications.py` :**

```python
#!/usr/bin/env python3
"""
Tester toutes les types de notifications.
"""

import asyncio
import yaml
from src.telegram_notifier import TelegramNotifier

async def test_all_notifications():
    # Charger config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialiser notifier
    notifier = TelegramNotifier(config)

    print("📤 Test 1: Notification d'ouverture de position...")
    await notifier.send_trade_notification(
        action='OPEN',
        symbol='SOL/USDT',
        side='BUY',
        entry_price=142.35,
        quantity=0.0352,
        position_value=5.0,
        stop_loss=139.50,
        take_profit=151.08,
        signal_data={
            'confidence': 0.72,
            'action': 'STRONG_BUY',
            'rsi': 42.5,
            'macd': 0.85
        },
        portfolio_info={
            'open_positions': 2,
            'max_positions': 3,
            'balance': 100.0,
            'position_size_percent': 5.0
        }
    )
    await asyncio.sleep(3)

    print("📤 Test 2: Notification de fermeture (profit)...")
    await notifier.send_trade_notification(
        action='CLOSE',
        symbol='SOL/USDT',
        side='SELL',
        entry_price=142.35,
        exit_price=148.72,
        quantity=0.0352,
        pnl=0.22,
        pnl_percent=4.48,
        duration='1h 23min',
        reason='Take Profit',
        portfolio_info={
            'open_positions': 1,
            'max_positions': 3,
            'balance': 100.22,
            'total_pnl_percent': 0.22
        }
    )
    await asyncio.sleep(3)

    print("📤 Test 3: Notification d'erreur...")
    await notifier.send_error_notification(
        module='OrderExecutor',
        error_type='InsufficientFunds',
        error_message='Fonds insuffisants pour exécuter l\'ordre',
        severity='critical',
        context={'symbol': 'SOL/USDT', 'required': 5.0, 'available': 3.22}
    )
    await asyncio.sleep(3)

    print("📤 Test 4: Notification de learning...")
    await notifier.send_learning_notification(
        duration=12.3,
        trades_analyzed=47,
        model_metrics={
            'accuracy': 0.625,
            'precision': 0.683,
            'recall': 0.587,
            'f1_score': 0.63
        },
        weight_changes={
            'moving_averages': 2.07,
            'macd': -1.28,
            'rsi': 0.74
        },
        adaptations=['Optimized indicator weights', 'Adjusted min_confidence'],
        performance={
            'win_rate': 58.3,
            'total_pnl': 12.45,
            'profit_factor': 2.18
        }
    )

    print("\n✅ Tous les tests envoyés! Vérifiez votre Telegram.")

if __name__ == "__main__":
    asyncio.run(test_all_notifications())
```

### 3. Tests Unitaires

**Fichier `tests/test_telegram_notifier.py` :**

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.telegram_notifier import TelegramNotifier

@pytest.fixture
def mock_config():
    return {
        'notifications': {
            'telegram': {
                'enabled': True,
                'trades': {'enabled': True},
                'learning': {'enabled': True},
                'errors': {'enabled': True},
                'rate_limit': {
                    'max_messages_per_hour': 30,
                    'cooldown_between_messages': 2
                },
                'formatting': {
                    'use_emoji': True,
                    'use_markdown': True,
                    'timezone': 'UTC'
                }
            }
        }
    }

@pytest.mark.asyncio
async def test_send_trade_notification(mock_config):
    with patch.dict('os.environ', {
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'TELEGRAM_CHAT_ID': '123456789'
    }):
        notifier = TelegramNotifier(mock_config)
        notifier.bot = AsyncMock()

        await notifier.send_trade_notification(
            action='OPEN',
            symbol='BTC/USDT',
            side='BUY',
            entry_price=50000,
            quantity=0.01,
            position_value=500
        )

        assert notifier.bot.send_message.called

@pytest.mark.asyncio
async def test_rate_limiting(mock_config):
    notifier = TelegramNotifier(mock_config)
    notifier.max_messages_per_hour = 2

    # Envoyer 3 messages rapidement
    for i in range(3):
        result = notifier._check_rate_limit()
        if i < 2:
            assert result == True
        else:
            assert result == False
```

---

## Déploiement

### 1. Checklist Pré-Déploiement

```
☐ Bot Telegram créé via @BotFather
☐ Token récupéré et ajouté à .env
☐ Chat ID obtenu et ajouté à .env
☐ Test de connexion réussi (scripts/test_telegram.py)
☐ Tests de notifications réussis (scripts/test_notifications.py)
☐ Configuration config.yaml mise à jour
☐ .env ajouté au .gitignore
☐ Dépendances installées (pip install python-telegram-bot==20.7)
☐ Code testé en mode PAPER avant LIVE
```

### 2. Installation Étape par Étape

```bash
# 1. Installer la dépendance
pip install python-telegram-bot==20.7

# 2. Créer le fichier .env (si pas déjà fait)
cp .env.example .env

# 3. Éditer .env et ajouter les credentials Telegram
nano .env
# Ajouter:
# TELEGRAM_BOT_TOKEN=votre_token_ici
# TELEGRAM_CHAT_ID=votre_chat_id_ici

# 4. Mettre à jour config.yaml
nano config.yaml
# Activer notifications.telegram.enabled: true

# 5. Tester la connexion
python scripts/test_telegram.py

# 6. Tester les notifications
python scripts/test_notifications.py

# 7. Démarrer le bot
python run_bot.py
```

### 3. Activation Progressive

**Phase 1 : Tests (1-2 jours)**
```yaml
notifications:
  telegram:
    enabled: true
    trades:
      enabled: true  # Seulement trades
    learning:
      enabled: false
    errors:
      enabled: false
    reports:
      enabled: false
```

**Phase 2 : Apprentissage (3-7 jours)**
```yaml
notifications:
  telegram:
    enabled: true
    trades:
      enabled: true
    learning:
      enabled: true  # Ajouter learning
    errors:
      enabled: false
    reports:
      enabled: false
```

**Phase 3 : Complet (après 1 semaine)**
```yaml
notifications:
  telegram:
    enabled: true
    trades:
      enabled: true
    learning:
      enabled: true
    errors:
      enabled: true
    reports:
      enabled: true
      schedule: "daily"
```

### 4. Monitoring et Maintenance

**Vérifications régulières :**
- [ ] Vérifier que le bot reçoit bien les messages
- [ ] Vérifier le rate limit (pas de messages perdus)
- [ ] Vérifier les logs pour erreurs Telegram
- [ ] Ajuster la configuration selon les besoins

**Commandes utiles :**
```bash
# Voir les derniers messages dans les logs
tail -f trading_bot.log | grep -i telegram

# Compter le nombre de notifications envoyées
grep "Telegram notification sent" trading_bot.log | wc -l

# Vérifier les erreurs Telegram
grep "Failed to send Telegram" trading_bot.log
```

---

## Améliorations Futures (Optionnelles)

### 1. Commandes Interactives

Permettre de contrôler le bot via Telegram :

```
/status - Afficher le statut actuel
/positions - Voir les positions ouvertes
/stats - Statistiques de performance
/pause - Mettre le trading en pause
/resume - Reprendre le trading
/close <symbol> - Fermer une position
/settings - Voir/modifier la configuration
```

### 2. Graphiques et Charts

Envoyer des graphiques de performance :
- Courbe de PnL
- Distribution des trades
- Performance par symbole
- Évolution de l'accuracy ML

```python
import matplotlib.pyplot as plt
import io

async def send_performance_chart(self):
    # Générer le graphique
    fig, ax = plt.subplots()
    # ... plot data ...

    # Convertir en bytes
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    # Envoyer via Telegram
    await self.bot.send_photo(
        chat_id=self.chat_id,
        photo=buf,
        caption="📊 Performance des 7 derniers jours"
    )
```

### 3. Alertes Personnalisées

```yaml
notifications:
  telegram:
    custom_alerts:
      - type: big_win
        condition: "pnl_percent > 10"
        message: "🎉 GROS GAIN: {pnl_percent}% sur {symbol}!"

      - type: big_loss
        condition: "pnl_percent < -5"
        message: "⚠️ GROSSE PERTE: {pnl_percent}% sur {symbol}"

      - type: high_accuracy
        condition: "ml_accuracy > 70"
        message: "🎯 ML très précis: {ml_accuracy}%"
```

### 4. Multi-Utilisateurs

Envoyer les notifications à plusieurs personnes :

```python
TELEGRAM_CHAT_IDS=123456789,987654321,555555555
```

### 5. Niveaux de Notifications

```yaml
notification_levels:
  minimal:    # Seulement trades et erreurs critiques
  standard:   # Trades, learning, erreurs
  verbose:    # Tout y compris rapports fréquents
  debug:      # Tout + informations de debug
```

---

## Conclusion

### Résumé des Étapes

1. ✅ **Prérequis** : Créer bot Telegram, obtenir token et chat ID
2. ✅ **Installation** : Installer python-telegram-bot
3. ✅ **Configuration** : Mettre à jour .env et config.yaml
4. ✅ **Implémentation** : Créer telegram_notifier.py et notification_formatter.py
5. ✅ **Intégration** : Ajouter les appels dans trading_bot.py
6. ✅ **Tests** : Tester connexion et notifications
7. ✅ **Déploiement** : Activer progressivement

### Temps Estimé

- Configuration initiale : 30 minutes
- Implémentation : 4-6 heures
- Tests : 1-2 heures
- Déploiement et ajustements : 1 heure

**Total : ~1 journée de développement**

### Avantages Attendus

- ✅ Surveillance en temps réel
- ✅ Réactivité aux erreurs
- ✅ Meilleure compréhension du comportement du bot
- ✅ Historique accessible sur mobile
- ✅ Pas besoin d'accès au serveur pour suivre l'activité

---

## Support et Ressources

### Documentation Telegram

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [BotFather Commands](https://core.telegram.org/bots#botfather)

### Debugging

En cas de problème :

1. Vérifier les credentials dans .env
2. Tester la connexion avec scripts/test_telegram.py
3. Vérifier les logs : `tail -f trading_bot.log`
4. Vérifier que le bot n'est pas bloqué sur Telegram
5. Vérifier le rate limiting

### Questions Fréquentes

**Q : Le bot ne reçoit pas les messages**
- Vérifier que vous avez cliqué sur "Start" dans le chat avec le bot
- Vérifier le CHAT_ID (doit être un nombre)
- Vérifier le token du bot

**Q : Trop de notifications**
- Ajuster le rate_limit dans config.yaml
- Désactiver certains types de notifications
- Augmenter min_pnl_percent pour trades

**Q : Messages trop longs**
- Le formatter tronque automatiquement à 4096 caractères
- Réduire le niveau de détail dans la configuration

---

**Prêt pour l'implémentation ?** 🚀
