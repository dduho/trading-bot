# Trading Bot - Système d'Analyse et de Trading Automatisé

Un bot de trading professionnel qui analyse les marchés financiers en temps réel et génère des signaux d'achat/vente basés sur l'analyse technique multi-indicateurs.

## 🚀 Fonctionnalités

### Analyse de Marché en Temps Réel
- **Connexion aux exchanges**: Support de Binance, Coinbase, Kraken, et autres via CCXT
- **Données en temps réel**: Analyse seconde par seconde des marchés
- **Multi-timeframes**: Support de 1m, 5m, 15m, 1h, 4h, 1d
- **Multi-symboles**: Surveillance simultanée de plusieurs paires de trading

### Indicateurs Techniques
- **RSI** (Relative Strength Index) - Détection de surachat/survente
- **MACD** (Moving Average Convergence Divergence) - Signaux de momentum
- **Moving Averages** (SMA/EMA) - Détection de tendances
- **Bollinger Bands** - Volatilité et niveaux de prix
- **ATR** (Average True Range) - Mesure de volatilité
- **Stochastic Oscillator** - Momentum du marché
- **Volume Analysis** - Confirmation des mouvements

### Génération de Signaux Intelligents
- **Système multi-indicateurs**: Combine plusieurs indicateurs pour plus de précision
- **Score de confiance**: Chaque signal a un score de confiance (0-100%)
- **Pondération configurable**: Ajustez l'importance de chaque indicateur
- **Signaux graduels**: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL

### Gestion des Risques Avancée
- **Position sizing**: Calcul automatique de la taille des positions
- **Stop Loss**: Protection automatique contre les pertes
- **Take Profit**: Prise de bénéfices automatique
- **Trailing Stop**: Stop loss dynamique
- **Limites de trading**: Protection contre les pertes journalières
- **Risk/Reward Ratio**: Ratio risque/récompense configurable

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Compte sur un exchange de crypto (Binance recommandé)
- API keys de l'exchange (pour le trading réel)

## 🛠️ Installation

### Installation Rapide (Linux/Mac)

```bash
# Cloner le repository
git clone <repository-url>
cd trading-bot

# Exécuter le script d'installation
./setup.sh
```

### Installation Manuelle

```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Copier le fichier de configuration
cp .env.example .env
```

## ⚙️ Configuration

### 1. Configuration de l'Exchange

Éditez le fichier `.env` avec vos informations:

```bash
# Exchange à utiliser
EXCHANGE=binance

# Vos clés API (obtenues depuis votre exchange)
API_KEY=votre_cle_api_ici
API_SECRET=votre_secret_api_ici

# Mode de trading
TRADING_MODE=paper  # Utilisez 'paper' pour tester sans risque!

# Symbole par défaut
DEFAULT_SYMBOL=BTC/USDT
TIMEFRAME=1m
```

**⚠️ IMPORTANT**: Commencez TOUJOURS en mode `paper` (simulation) avant de passer en mode `live`!

**📚 GUIDE COMPLET DES MODES**: Consultez [TRADING_MODES.md](TRADING_MODES.md) pour un guide détaillé sur les modes paper, testnet et live.

### 2. Configuration de la Stratégie

Éditez `config.yaml` pour ajuster:

- **Symboles à surveiller**: Liste des paires de trading
- **Timeframes**: Intervalles de temps pour l'analyse
- **Indicateurs**: Paramètres de chaque indicateur technique
- **Stratégie**: Poids des indicateurs et seuil de confiance
- **Gestion des risques**: Stop loss, take profit, limites

Exemple:

```yaml
symbols:
  - BTC/USDT
  - ETH/USDT
  - BNB/USDT

strategy:
  min_confidence: 0.6  # Confiance minimale pour trader (60%)
  weights:
    rsi: 0.25
    macd: 0.25
    moving_averages: 0.25
    volume: 0.15
    trend: 0.10

risk:
  max_position_size_percent: 10  # Max 10% du capital par position
  stop_loss_percent: 2.0         # Stop loss à -2%
  take_profit_percent: 5.0       # Take profit à +5%
  max_daily_loss_percent: 5.0    # Arrêt si perte > 5% par jour
```

## 🎮 Utilisation

## 🎯 Modes de Trading

Le bot supporte **trois modes** de trading avec des niveaux de risque différents:

### Mode 1: 🟢 PAPER (Simulation) - RECOMMANDÉ POUR COMMENCER

**Mode par défaut - Aucun risque financier**

```bash
# Dans .env
TRADING_MODE=paper
```

- ✅ Simulation complète sans ordres réels
- ✅ Pas besoin de clés API
- ✅ Capital virtuel: 10,000 USDT
- ✅ Données de marché réelles
- ✅ Parfait pour tester votre stratégie

### Mode 2: 🟡 TESTNET (Réseau de Test)

**Test avec API réelles mais argent fictif**

```bash
# Dans .env
TRADING_MODE=testnet
API_KEY=votre_cle_testnet
API_SECRET=votre_secret_testnet
```

- ✅ Utilise le testnet/sandbox de l'exchange
- ✅ Appels API réels avec argent factice
- ⚠️ Nécessite des clés API testnet
- ✅ Teste l'intégration complète

**Pour obtenir des clés testnet Binance:**
- https://testnet.binance.vision/

### Mode 3: 🔴 LIVE (Trading Réel) - DANGER!

**⚠️ ARGENT RÉEL - RISQUE MAXIMUM ⚠️**

```bash
# Dans .env
TRADING_MODE=live
API_KEY=votre_cle_production
API_SECRET=votre_secret_production
```

- 🔴 Ordres RÉELS avec argent RÉEL
- 🔴 Vous pouvez PERDRE tout votre capital
- ⚠️ Nécessite des clés API de production
- 🔴 À utiliser UNIQUEMENT après tests approfondis

**AVANT d'activer le mode live:**
1. ✅ Tester en mode paper pendant 1+ semaine
2. ✅ Tester en mode testnet avec succès
3. ✅ Backtester votre stratégie
4. ✅ Configurer des limites de risque strictes
5. ✅ Désactiver la permission WITHDRAW sur les clés API
6. ✅ Commencer avec un PETIT montant

**📚 GUIDE COMPLET**: Consultez [TRADING_MODES.md](TRADING_MODES.md) pour toutes les instructions détaillées.

---

### Lancer le Bot

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le bot
python run_bot.py
```

Le bot va:
1. Se connecter à l'exchange
2. Récupérer les données de marché
3. Calculer les indicateurs techniques
4. Générer des signaux d'achat/vente
5. Afficher l'analyse en temps réel

### Exemple de Sortie

```
╔═══════════════════════════════════════════════════════════════╗
║                    TRADING BOT v1.0                           ║
║              Real-time Market Analysis System                 ║
╚═══════════════════════════════════════════════════════════════╝

Trading Bot Started!
Symbols: BTC/USDT, ETH/USDT
Timeframe: 1m
Update Interval: 60s

================================================================================
BUY SIGNAL - BTC/USDT
================================================================================
Time:       2025-11-05 14:30:00
Price:      $42,350.50
Quantity:   0.023456
Value:      $993.45
Confidence: 75.3%
Reason:     RSI oversold at 28.5; MACD bullish crossover
Stop Loss:  $41,503.49 (-2.00%)
Take Profit: $44,044.51 (+4.00%)
================================================================================
```

### Backtesting

Testez votre stratégie sur des données historiques:

```bash
python backtest.py
```

Cela vous permettra de:
- Voir les performances de votre stratégie sur le passé
- Identifier les meilleurs paramètres
- Calculer les statistiques (win rate, profit factor, etc.)

## 📊 Architecture du Système

```
trading-bot/
├── src/
│   ├── market_data.py        # Connexion aux exchanges et récupération des données
│   ├── technical_analysis.py # Calcul des indicateurs techniques
│   ├── signal_generator.py   # Génération des signaux de trading
│   ├── risk_manager.py       # Gestion des risques et des positions
│   └── trading_bot.py        # Orchestrateur principal
├── config.yaml               # Configuration de la stratégie
├── .env                      # Configuration de l'exchange (API keys)
├── requirements.txt          # Dépendances Python
├── run_bot.py               # Script de lancement
└── backtest.py              # Script de backtesting
```

## 🧩 Modules Principaux

### 1. MarketDataFeed (`market_data.py`)
- Connexion aux exchanges via CCXT
- Récupération des données OHLCV (Open, High, Low, Close, Volume)
- Streaming en temps réel des prix
- Support de multiple exchanges

### 2. TechnicalAnalyzer (`technical_analysis.py`)
- Calcul de tous les indicateurs techniques
- Analyse de tendance
- Résumé du marché
- Détection des patterns

### 3. SignalGenerator (`signal_generator.py`)
- Analyse multi-indicateurs
- Calcul de score de confiance
- Génération de signaux BUY/SELL/HOLD
- Historique des signaux

### 4. RiskManager (`risk_manager.py`)
- Calcul de la taille des positions
- Gestion des stop loss et take profit
- Suivi des positions ouvertes
- Statistiques de performance
- Protection contre les pertes excessives

### 5. TradingBot (`trading_bot.py`)
- Orchestration de tous les modules
- Boucle de trading principale
- Interface utilisateur
- Logging et monitoring

## 📈 Stratégie de Trading

Le bot utilise une approche **multi-indicateurs** pour générer des signaux:

### Signaux d'Achat (BUY)
- RSI < 30 (survente)
- MACD bullish crossover
- Prix au-dessus des moyennes mobiles
- Volume élevé avec hausse de prix
- Tendance haussière confirmée

### Signaux de Vente (SELL)
- RSI > 70 (surachat)
- MACD bearish crossover
- Prix en-dessous des moyennes mobiles
- Volume élevé avec baisse de prix
- Tendance baissière confirmée

### Score de Confiance
Chaque signal reçoit un score basé sur:
- Nombre d'indicateurs en accord
- Force des signaux individuels
- Poids configurés dans `config.yaml`

**Minimum de 60% de confiance requis par défaut pour trader**

## ⚠️ Avertissements et Précautions

### AVERTISSEMENT DE RISQUE

**Le trading comporte des risques financiers importants. Vous pouvez perdre tout votre capital.**

- ✅ **Commencez TOUJOURS en mode paper (simulation)**
- ✅ **Testez votre stratégie avec le backtesting**
- ✅ **Ne tradez que l'argent que vous pouvez vous permettre de perdre**
- ✅ **Surveillez régulièrement le bot**
- ✅ **Commencez avec de petits montants**
- ❌ **Ne laissez jamais le bot sans surveillance prolongée**
- ❌ **Ne tradez pas avec de l'argent emprunté**

### Sécurité des API Keys

- 🔒 Ne JAMAIS commiter le fichier `.env` dans git
- 🔒 Utilisez des API keys avec permissions limitées (pas de withdrawal)
- 🔒 Activez l'authentification 2FA sur votre exchange
- 🔒 Utilisez des whitelist IP si disponible

## 🔧 Personnalisation

### Ajouter un Nouvel Indicateur

1. Ajoutez la fonction de calcul dans `technical_analysis.py`
2. Ajoutez l'analyse dans `signal_generator.py`
3. Configurez le poids dans `config.yaml`

### Modifier la Stratégie

Éditez `config.yaml` pour ajuster:
- Seuil de confiance minimum
- Poids des indicateurs
- Paramètres de risk management

### Ajouter un Exchange

Le bot utilise CCXT qui supporte 100+ exchanges. Pour changer:
```bash
# Dans .env
EXCHANGE=kraken  # ou coinbase, ftx, etc.
```

## 📊 Métriques de Performance

Le bot calcule automatiquement:
- **Win Rate**: Pourcentage de trades gagnants
- **Profit Factor**: Ratio profits/pertes
- **Average Win/Loss**: Gain/perte moyens par trade
- **Max Drawdown**: Perte maximale
- **Total PnL**: Profit/perte total
- **Sharpe Ratio**: Ratio rendement/risque

## 🐛 Dépannage

### Erreur de connexion à l'exchange
```
Vérifiez vos API keys dans .env
Assurez-vous que l'exchange est accessible
Vérifiez votre connexion internet
```

### Pas de données disponibles
```
Vérifiez le symbole (format: BTC/USDT)
Certains exchanges ont des symboles différents
Vérifiez que le timeframe est supporté
```

### Le bot ne génère pas de signaux
```
Vérifiez que min_confidence n'est pas trop élevé
Assurez-vous qu'il y a assez de données (minimum 100 candles)
Vérifiez les logs dans trading_bot.log
```

## 📝 Logs

Tous les événements sont enregistrés dans `trading_bot.log`:
- Connexions aux exchanges
- Signaux générés
- Trades exécutés
- Erreurs et warnings

```bash
# Suivre les logs en temps réel
tail -f trading_bot.log
```

## 🚀 Améliorations Futures

Fonctionnalités prévues:
- [ ] Support des stratégies de machine learning
- [ ] Interface web/dashboard
- [ ] Notifications (Telegram, email)
- [ ] Multi-exchange arbitrage
- [ ] Support des futures et options
- [ ] Backtesting avancé avec optimisation de paramètres
- [ ] Paper trading avec exchange simulé

## 📚 Ressources

### Documentation
- [CCXT Documentation](https://docs.ccxt.com/)
- [Technical Analysis Library](https://technical-analysis-library-in-python.readthedocs.io/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

### Apprendre le Trading
- [Investopedia - Technical Analysis](https://www.investopedia.com/technical-analysis-4689657)
- [Babypips - Learn Forex Trading](https://www.babypips.com/)

## 📄 Licence

Ce projet est fourni à des fins éducatives uniquement.

## 🤝 Support

Pour toute question ou problème:
1. Consultez la documentation ci-dessus
2. Vérifiez les logs (`trading_bot.log`)
3. Testez d'abord en mode paper trading

---

**Bon trading! 📈💰**

*N'oubliez pas: Les performances passées ne garantissent pas les résultats futurs. Tradez de manière responsable.*
