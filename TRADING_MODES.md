# Guide des Modes de Trading

Ce document explique les trois modes de trading disponibles dans le bot et comment les utiliser en toute sécurité.

## 📋 Les Trois Modes

### 1. 🟢 Mode PAPER (Simulation)

**C'est le mode par défaut et le plus sûr.**

#### Caractéristiques:
- ✅ Simulation complète - AUCUN ordre réel
- ✅ Pas besoin de clés API
- ✅ Capital virtuel de départ: 10,000 USDT
- ✅ Données de marché réelles
- ✅ Parfait pour tester votre stratégie
- ✅ Aucun risque financier

#### Configuration:
```bash
# Dans .env
TRADING_MODE=paper
API_KEY=  # Peut rester vide
API_SECRET=  # Peut rester vide
```

#### Utilisation:
```bash
python run_bot.py
```

Le bot affichera:
```
📝 PAPER TRADING MODE - Simulation only
This is a safe simulation mode. No real orders will be executed.
Starting capital: $10,000.00 USDT
```

#### Quand l'utiliser:
- ✅ Première fois que vous lancez le bot
- ✅ Test de nouvelles stratégies
- ✅ Ajustement des paramètres
- ✅ Apprentissage du fonctionnement du bot

---

### 2. 🟡 Mode TESTNET (Réseau de Test)

**Mode intermédiaire avec API réelles mais argent fictif.**

#### Caractéristiques:
- ✅ Utilise le testnet/sandbox de l'exchange
- ✅ Appels API réels mais avec de l'argent factice
- ⚠️ Nécessite des clés API de testnet
- ✅ Teste l'intégration complète avec l'exchange
- ✅ Aucun risque financier

#### Configuration:

**1. Obtenir des clés API testnet:**

**Binance Testnet:**
- Allez sur: https://testnet.binance.vision/
- Créez un compte testnet
- Générez des clés API testnet
- Vous recevrez des fonds fictifs automatiquement

**Autres exchanges:**
- Recherchez "[nom_exchange] testnet" ou "sandbox"
- Suivez leurs instructions

**2. Configurer le bot:**
```bash
# Dans .env
TRADING_MODE=testnet
EXCHANGE=binance
API_KEY=votre_cle_api_testnet
API_SECRET=votre_secret_api_testnet
```

#### Utilisation:
```bash
python run_bot.py
```

Le bot affichera:
```
📝 TESTNET MODE - Using exchange testnet/sandbox
This mode uses the exchange's testnet with fake money.
Orders are real API calls but with test funds.
```

#### Quand l'utiliser:
- ✅ Après avoir testé en mode paper
- ✅ Pour vérifier que vos clés API fonctionnent
- ✅ Pour tester l'exécution réelle d'ordres
- ✅ Avant de passer en mode live
- ✅ Pour identifier les bugs d'intégration

---

### 3. 🔴 Mode LIVE (Trading Réel)

**⚠️ MODE DANGER - ARGENT RÉEL EN JEU ⚠️**

#### Caractéristiques:
- 🔴 Ordres RÉELS avec de l'argent RÉEL
- 🔴 Vous pouvez PERDRE de l'argent réel
- ⚠️ Nécessite des clés API de production
- ⚠️ Permissions API: LIRE + ÉCRIRE (PAS de WITHDRAW!)
- 🔴 Risque financier maximum

#### ⚠️ PRÉREQUIS OBLIGATOIRES:

**AVANT d'activer le mode live, vous DEVEZ:**
1. ✅ Avoir testé en mode paper pendant au moins 1 semaine
2. ✅ Avoir testé en mode testnet sans problèmes
3. ✅ Avoir backtesté votre stratégie avec de bons résultats
4. ✅ Comprendre parfaitement comment fonctionne le bot
5. ✅ Avoir lu TOUTE la documentation
6. ✅ Comprendre que vous pouvez perdre tout votre capital
7. ✅ N'utiliser que de l'argent que vous pouvez vous permettre de perdre
8. ✅ Avoir configuré des limites de risque strictes

#### Configuration des Clés API (IMPORTANT!):

**1. Créer des clés API sur votre exchange:**

**Binance:**
- Allez dans: Compte > API Management
- Créez une nouvelle clé API
- Nom: "Trading Bot" (ou similaire)
- **Permissions:**
  - ✅ Enable Reading
  - ✅ Enable Spot & Margin Trading
  - ❌ **DISABLE** Enable Withdrawals (CRITIQUE!)
- **Whitelist IP** (optionnel mais recommandé)
- Activez 2FA si demandé
- Sauvegardez votre clé et secret de manière sécurisée

**Autres exchanges:**
- Suivez un processus similaire
- TOUJOURS désactiver les retraits
- TOUJOURS utiliser 2FA

**2. Configurer le bot:**
```bash
# Dans .env
TRADING_MODE=live
EXCHANGE=binance
API_KEY=votre_cle_api_production
API_SECRET=votre_secret_api_production
```

#### ⚠️ SÉCURITÉ - LISTE DE VÉRIFICATION:

Avant de lancer en mode live:
- [ ] Les clés API n'ont PAS la permission de retrait
- [ ] L'authentification 2FA est activée sur l'exchange
- [ ] Le fichier .env n'est PAS commité dans git
- [ ] Les limites de risque sont configurées dans config.yaml
- [ ] Vous avez testé en paper ET testnet
- [ ] Vous commencez avec un PETIT montant
- [ ] Vous comprenez comment arrêter le bot en urgence (Ctrl+C)
- [ ] Vous allez surveiller le bot régulièrement
- [ ] Vous avez configuré MAX_DAILY_LOSS dans config.yaml

#### Configuration des Limites (config.yaml):

```yaml
risk:
  max_position_size_percent: 5    # COMMENCEZ BAS! (5% max par position)
  stop_loss_percent: 2.0          # Stop loss à -2%
  take_profit_percent: 5.0        # Take profit à +5%
  max_open_positions: 2           # Max 2 positions simultanées
  max_daily_trades: 5             # Max 5 trades par jour
  max_daily_loss_percent: 5.0     # STOP si perte > 5% par jour
```

#### Utilisation:
```bash
python run_bot.py
```

Le bot affichera:
```
================================================================================
⚠️  WARNING: LIVE TRADING MODE - REAL MONEY AT RISK! ⚠️
================================================================================

This bot will execute REAL trades with REAL money!
Make sure you understand the risks and have tested your strategy.
Capital available: $XXX.XX USDT
```

#### ❌ N'UTILISEZ JAMAIS LE MODE LIVE SI:
- Vous n'avez pas testé en paper/testnet
- Vous ne comprenez pas comment fonctionne le bot
- Vous utilisez de l'argent emprunté
- Vous ne pouvez pas surveiller le bot
- Les limites de risque ne sont pas configurées
- Vous n'avez pas désactivé les retraits sur les clés API

---

## 🔄 Progression Recommandée

### Étape 1: Mode Paper (1-2 semaines)
1. Lancez le bot en mode paper
2. Observez les signaux générés
3. Ajustez les paramètres dans config.yaml
4. Vérifiez les performances (win rate, profit factor)
5. Testez différentes configurations

### Étape 2: Backtesting
```bash
python backtest.py
```
1. Vérifiez les performances historiques
2. Assurez-vous d'avoir un win rate > 50%
3. Vérifiez que le profit factor > 1.5

### Étape 3: Mode Testnet (3-7 jours)
1. Obtenez des clés testnet
2. Configurez TRADING_MODE=testnet
3. Lancez le bot
4. Vérifiez que les ordres s'exécutent correctement
5. Testez les stop loss et take profit

### Étape 4: Mode Live (avec prudence)
1. ✅ Toutes les étapes précédentes réussies
2. Créez des clés API de production (sans withdraw!)
3. Configurez TRADING_MODE=live
4. **COMMENCEZ AVEC UN TRÈS PETIT MONTANT**
5. Surveillez activement les premières heures/jours
6. Augmentez progressivement si les résultats sont bons

---

## 🛑 Comment Arrêter le Bot en Urgence

### Arrêt Normal:
```bash
Ctrl + C
```
Le bot fermera proprement toutes les positions en cours.

### Arrêt d'Urgence (si ça ne répond pas):
1. `Ctrl + C` (plusieurs fois)
2. Si nécessaire: `killall python` ou fermez le terminal
3. Connectez-vous à votre exchange et fermez manuellement les positions

---

## 📊 Surveillance du Bot

### Logs en Temps Réel:
```bash
tail -f trading_bot.log
```

### Vérifier les Positions:
Le bot affiche l'état toutes les 10 itérations.

### Vérifier sur l'Exchange:
Connectez-vous à votre exchange pour voir:
- Positions ouvertes
- Ordres actifs
- Historique des trades
- Solde du compte

---

## ⚠️ Avertissements Finaux

### RISQUES:
- **Perte de capital**: Vous pouvez perdre tout votre argent
- **Bugs logiciels**: Le bot peut avoir des bugs
- **Problèmes de connexion**: Perte de connexion internet/API
- **Mouvements de marché**: Volatilité extrême non prévue
- **Erreurs de configuration**: Mauvais paramètres

### RESPONSABILITÉ:
- Vous êtes seul responsable de vos pertes
- Ce bot est fourni à titre éducatif uniquement
- Aucune garantie de profits
- Tradez uniquement ce que vous pouvez perdre

### RECOMMANDATIONS:
- ✅ Commencez TOUJOURS en mode paper
- ✅ Ne skippe z pas le mode testnet
- ✅ Commencez avec de petites sommes en live
- ✅ Surveillez régulièrement
- ✅ Configurez des limites strictes
- ✅ Utilisez 2FA et sécurisez vos clés API
- ✅ Ne tradez pas avec de l'argent emprunté
- ❌ Ne laissez pas le bot sans surveillance prolongée

---

## 🤝 Support

Si vous avez des questions sur les modes de trading:
1. Relisez ce document attentivement
2. Consultez README.md
3. Vérifiez les logs (trading_bot.log)
4. Testez d'abord en mode paper!

**Bon trading, et soyez prudent!** 📈🛡️
