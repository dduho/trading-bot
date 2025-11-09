# 🚀 Guide Rapide - Tester les Commandes Telegram

## 📋 Ce qui a été ajouté

Votre bot Telegram répond maintenant à **7 commandes interactives** que vous pouvez envoyer à tout moment :

| Commande | Description |
|----------|-------------|
| `/start` ou `/help` | Menu d'aide |
| `/status` | État du bot et portfolio |
| `/ml` | Métriques ML et apprentissage |
| `/positions` | Positions ouvertes |
| `/performance` | Stats globales |
| `/today` | Résumé du jour |

---

## ⚡ Test en 3 Étapes

### 1️⃣ Lancer le bot localement
```bash
python run_bot.py
```

Attendez de voir dans les logs :
```
✅ Telegram commands started
```

### 2️⃣ Ouvrir Telegram
- Ouvrez votre chat avec `@xii_trading_notifier_bot`
- Tapez `/start`

### 3️⃣ Tester les commandes
Essayez chaque commande :
```
/status
/ml
/positions
/performance
/today
```

Le bot répond **instantanément** avec les infos demandées ! 🎯

---

## 💡 Double Système

### 🔔 Notifications Automatiques
Le bot envoie automatiquement des notifications pour :
- ✅ Ouvertures/fermetures de positions
- ✅ Stop Loss / Take Profit
- ✅ Cycles d'apprentissage ML
- ✅ Erreurs critiques
- ✅ Démarrage/arrêt

### 💬 Commandes Interactives
Vous interrogez le bot quand vous voulez :
- 🔍 État actuel (`/status`)
- 🧠 Métriques ML (`/ml`)
- 📊 Positions (`/positions`)
- 📈 Performance (`/performance`)
- 📅 Aujourd'hui (`/today`)

**Les deux fonctionnent ensemble** pour un contrôle total ! 🚀

---

## 🔐 Sécurité

Seul **votre chat ID** (`8350384028`) peut utiliser ces commandes. Si quelqu'un d'autre essaie, il recevra "❌ Non autorisé".

---

## 📱 Sur la VM

Une fois déployé sur la VM :
1. Connectez-vous via PuTTY
2. Exécutez : `cd trading-bot && bash deploy_telegram.sh`
3. Les commandes fonctionneront **24/7** !

Vous pourrez interroger votre bot à distance depuis n'importe où, à tout moment ! 🌍✨

---

## 📚 Documentation Complète

Pour plus de détails sur chaque commande et ses réponses :
👉 Voir [TELEGRAM_COMMANDS.md](TELEGRAM_COMMANDS.md)
