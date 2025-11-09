# 🔄 Mise à Jour des Notifications Telegram sur la VM

## 📋 Commandes Rapides

### Mettre à jour le bot avec les nouvelles notifications
```bash
./bot_manager.sh update
```

Cette commande fait automatiquement :
1. ✅ Arrête le bot
2. ✅ Pull les dernières modifications GitHub
3. ✅ Met à jour les dépendances Python
4. ✅ Redémarre le bot

---

## 🎮 Gestion du Bot

### Démarrer le bot
```bash
./bot_manager.sh start
```

### Arrêter le bot
```bash
./bot_manager.sh stop
```

### Redémarrer le bot
```bash
./bot_manager.sh restart
```

### Vérifier le statut
```bash
./bot_manager.sh status
```

### Voir les logs en temps réel
```bash
./bot_manager.sh logs
```
(Ctrl+C pour quitter)

---

## 🆕 Ce qui a été Ajouté

### 1. Commandes Telegram Interactives
Le bot répond maintenant à ces commandes :
- `/start` ou `/help` - Menu d'aide
- `/status` - État du bot et portfolio
- `/ml` - Métriques ML
- `/positions` - Positions ouvertes
- `/performance` - Stats globales
- `/today` - Résumé du jour

### 2. Nouveaux Fichiers
- `src/telegram_commands.py` - Gestionnaire de commandes
- `src/notification_formatter.py` - Formatage des messages
- `src/telegram_notifier.py` - Système de notifications

### 3. Modifications
- `src/trading_bot.py` - Intégration complète des notifications
- `src/ml_optimizer.py` - Ajout méthode `get_current_metrics()`

---

## ⚙️ Configuration Requise

Vérifiez que votre `.env` sur la VM contient :
```env
TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
TELEGRAM_CHAT_ID=8350384028
```

---

## 🧪 Tester Après Mise à Jour

### 1. Vérifier que le bot tourne
```bash
./bot_manager.sh status
```

### 2. Vérifier les logs
```bash
./bot_manager.sh logs
```

Vous devriez voir :
```
✅ Telegram notifications enabled
✅ Telegram commands started
```

### 3. Dans Telegram
- Ouvrez votre chat avec `@xii_trading_notifier_bot`
- Tapez `/status`
- Le bot devrait répondre instantanément !

---

## 🐛 Dépannage

### Le bot ne démarre pas
```bash
# Vérifier les logs
./bot_manager.sh logs

# Vérifier les dépendances
cd ~/trading-bot
source venv/bin/activate
pip install -r requirements.txt
```

### Pas de réponse aux commandes Telegram
```bash
# Redémarrer le bot
./bot_manager.sh restart

# Vérifier dans les logs si "Telegram commands started" apparaît
./bot_manager.sh logs
```

### Erreur de connexion Telegram
Vérifiez votre `.env` :
```bash
cat ~/trading-bot/.env | grep TELEGRAM
```

---

## 📦 Installation Manuelle (si nécessaire)

Si `bot_manager.sh update` ne fonctionne pas :

```bash
# 1. Arrêter le bot
./bot_manager.sh stop

# 2. Mettre à jour le code
cd ~/trading-bot
git pull

# 3. Activer l'environnement virtuel
source venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Vérifier la config
nano .env  # Ajoutez TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID si manquants

# 6. Redémarrer
./bot_manager.sh start
```

---

## ✅ Checklist Post-Mise à Jour

- [ ] Bot démarré : `./bot_manager.sh status`
- [ ] Logs propres : `./bot_manager.sh logs` (pas d'erreurs)
- [ ] Notification de démarrage reçue sur Telegram
- [ ] `/status` fonctionne dans Telegram
- [ ] `/ml` fonctionne dans Telegram
- [ ] Positions et trades notifiés automatiquement

---

## 🚀 Prochaine Mise à Jour

Pour toute future mise à jour, utilisez simplement :
```bash
./bot_manager.sh update
```

C'est tout ! 🎉
