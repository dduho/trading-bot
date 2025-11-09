# 🤖 Commandes Telegram Interactives

## Vue d'ensemble

En plus des **notifications automatiques**, le bot répond maintenant à des **commandes interactives** que vous pouvez envoyer à tout moment dans Telegram pour obtenir des informations en temps réel.

## 📋 Commandes Disponibles

### `/start` ou `/help`
Affiche le menu d'aide avec toutes les commandes disponibles.

**Exemple de réponse:**
```
🤖 Trading Bot - Commandes Disponibles

/status - État actuel du bot et portfolio
/ml - Progression et métriques ML
/positions - Positions ouvertes actuellement
/performance - Statistiques de performance globales
/today - Résumé de la journée
/help - Afficher cette aide

💡 Le bot envoie aussi des notifications automatiques 
   pour tous les événements importants
```

---

### `/status`
Affiche l'état actuel du bot et du portfolio.

**Informations retournées:**
- Mode de trading (PAPER/TESTNET/LIVE)
- Symbole tradé
- Timeframe utilisé
- Temps de fonctionnement (uptime)
- Balance actuelle
- Nombre de positions ouvertes
- PnL total ($ et %)
- PnL du jour ($ et %)

**Exemple de réponse:**
```
🤖 État du Bot

📊 Mode: PAPER
💱 Symbole: BTC/USDT
⏱ Timeframe: 1m
🕐 Uptime: 2h 34min

💰 Portfolio

Balance: $10,234.56
Positions: 2
PnL Total: $234.56 (2.34%)
PnL Aujourd'hui: $45.32 (0.45%)
```

---

### `/ml`
Affiche les métriques du système d'apprentissage machine.

**Informations retournées:**
- Précision du modèle
- Win rate
- Sharpe ratio
- Nombre de trades analysés
- Nombre de cycles ML effectués
- Paramètres actuels (RSI, confiance, SL, TP)
- Date du dernier apprentissage

**Exemple de réponse:**
```
🧠 Système d'Apprentissage

📈 Précision: 67.8%
🎯 Win Rate: 62.5%
💹 Sharpe Ratio: 1.45
📊 Trades analysés: 234
🔄 Cycles ML: 5

⚙️ Paramètres Actuels

RSI: 14
Confiance min: 0.65
Stop Loss: 2.0%
Take Profit: 5.0%

🕐 Dernier apprentissage: 08/11/2025 14:23
```

---

### `/positions`
Liste toutes les positions actuellement ouvertes.

**Informations retournées (par position):**
- Type (BUY/SELL)
- Symbole
- Prix d'entrée
- Montant investi
- Durée de la position
- PnL non réalisé

**Exemple de réponse:**
```
📊 Positions Ouvertes (2)

🟢 BUY BTC/USDT
Prix: $89,234.56
Montant: $500.00
Durée: 1h 23min
PnL: $12.34

🔴 SELL ETH/USDT
Prix: $3,456.78
Montant: $300.00
Durée: 34min
PnL: -$5.67
```

---

### `/performance`
Affiche les statistiques de performance globales.

**Informations retournées:**
- Nombre total de trades
- Trades gagnants vs perdants
- Win rate
- PnL total
- Gain moyen
- Perte moyenne
- Ratio gain/perte

**Exemple de réponse:**
```
📊 Performance Globale

📈 Total Trades: 156
✅ Gagnants: 98 (62.8%)
❌ Perdants: 58

💰 Résultats

PnL Total: $1,234.56
Gain Moyen: $23.45
Perte Moyenne: $-15.67
Ratio: 1.50
```

---

### `/today`
Résumé des activités de la journée en cours.

**Informations retournées:**
- Date du jour
- Nombre de trades aujourd'hui
- Trades fermées vs ouvertes
- Trades gagnants vs perdants
- PnL de la journée

**Exemple de réponse:**
```
📅 Résumé du 09/11/2025

📊 Trades: 12
🔒 Fermées: 10
🔓 Ouvertes: 2

✅ Gagnants: 7
❌ Perdants: 3

💰 PnL Aujourd'hui: $123.45
```

---

## 🔐 Sécurité

Les commandes sont **protégées** et ne répondent qu'au chat ID configuré dans votre `.env`. Si quelqu'un d'autre essaie d'utiliser votre bot, il recevra un message "❌ Non autorisé".

---

## 🚀 Utilisation

### 1. Démarrer le bot
```bash
python run_bot.py
```

### 2. Dans Telegram
Ouvrez votre conversation avec `@xii_trading_notifier_bot` et tapez n'importe quelle commande :

```
/status
```

Le bot répondra immédiatement avec les informations demandées !

---

## 📱 Notifications Automatiques vs Commandes

### Notifications Automatiques 🔔
Envoyées automatiquement lors d'événements :
- Ouverture/fermeture de position
- Déclenchement SL/TP
- Cycle d'apprentissage
- Erreurs critiques
- Démarrage/arrêt du bot

### Commandes Interactives 💬
Vous interrogez le bot quand vous voulez :
- État actuel (`/status`)
- Métriques ML (`/ml`)
- Positions (`/positions`)
- Performance (`/performance`)
- Résumé du jour (`/today`)

**Les deux systèmes fonctionnent en parallèle** pour vous donner un contrôle total sur votre bot ! 🎯

---

## 🐛 Dépannage

### Le bot ne répond pas aux commandes
1. Vérifiez que le bot est démarré : `python run_bot.py`
2. Vérifiez les logs : regardez si "Telegram commands started" apparaît
3. Vérifiez votre chat ID dans `.env`

### "❌ Non autorisé"
Votre chat ID n'est pas configuré correctement. Vérifiez `TELEGRAM_CHAT_ID` dans `.env`.

### Erreur de connexion
Vérifiez votre `TELEGRAM_BOT_TOKEN` dans `.env`.

---

## 📚 Prochaines Étapes

Une fois le bot déployé sur la VM, ces commandes fonctionneront 24/7 ! Vous pourrez interroger votre bot à distance à tout moment depuis votre téléphone. 📱✨
