# Déploiement Telegram sur Google Cloud VM

## 📋 Checklist de Déploiement

### Étape 1: Mettre à jour le code sur la VM

```bash
# Se connecter à la VM
gcloud compute ssh trading-bot-instance --zone=europe-west1-d --project=trading-bot-477713

# Aller dans le répertoire du bot
cd trading-bot

# Pull les derniers changements
git pull origin main
```

### Étape 2: Installer les dépendances

```bash
# Installer python-telegram-bot
pip install python-telegram-bot==20.7

# Ou réinstaller toutes les dépendances
pip install -r requirements.txt
```

### Étape 3: Configurer les credentials Telegram

```bash
# Éditer le fichier .env
nano .env
```

Ajouter ces lignes (ou les mettre à jour):
```bash
TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
TELEGRAM_CHAT_ID=8350384028
```

Sauvegarder avec `Ctrl+X`, puis `Y`, puis `Enter`.

### Étape 4: Vérifier la configuration

```bash
# Vérifier que le fichier .env contient les bonnes credentials
cat .env | grep TELEGRAM

# Devrait afficher:
# TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
# TELEGRAM_CHAT_ID=8350384028
```

### Étape 5: Tester la connexion Telegram

```bash
# Tester la connexion au bot
python scripts/test_telegram.py

# Vous devriez recevoir un message sur Telegram
```

### Étape 6: Arrêter le bot en cours (si actif)

```bash
# Trouver le PID du bot
ps aux | grep python | grep run_bot

# Tuer le processus (remplacer XXXXX par le PID)
kill XXXXX

# Vérifier qu'il est bien arrêté
ps aux | grep run_bot
```

### Étape 7: Redémarrer le bot avec les notifications

```bash
# Démarrer le bot en background
nohup python run_bot.py > bot.log 2>&1 &

# Vérifier que le bot démarre
tail -f bot.log

# Vous devriez voir:
# - "Telegram notifications enabled"
# - Et recevoir une notification de démarrage sur Telegram
```

### Étape 8: Vérifier que les notifications fonctionnent

**Vous devriez recevoir sur Telegram:**
- ✅ Message de démarrage du bot
- ✅ Notifications de positions ouvertes/fermées (quand il trade)
- ✅ Notifications de cycles d'apprentissage ML (toutes les 2h)
- ✅ Notifications d'erreurs (si problème)

### Étape 9: Surveiller les logs

```bash
# Voir les logs en temps réel
tail -f bot.log

# Chercher les messages Telegram dans les logs
grep -i "telegram" bot.log

# Devrait montrer:
# - "Telegram notifications enabled"
# - "Telegram notification sent successfully" (quand il envoie)
```

## 🔧 Commandes Utiles

### Redémarrer le bot
```bash
# Arrêter
pkill -f run_bot.py

# Démarrer
nohup python run_bot.py > bot.log 2>&1 &
```

### Vérifier l'état du bot
```bash
# Voir si le bot tourne
ps aux | grep run_bot

# Voir les dernières lignes de log
tail -20 bot.log

# Compter les notifications envoyées
grep "Telegram notification sent" bot.log | wc -l
```

### Tester les notifications manuellement
```bash
# Tester tous les types de notifications
python scripts/test_notifications.py
```

## ⚠️ Troubleshooting

### Problème: "TELEGRAM_BOT_TOKEN not found"
```bash
# Vérifier que .env existe
ls -la .env

# Vérifier le contenu
cat .env

# Si manquant, créer:
nano .env
# Ajouter les credentials
```

### Problème: "Failed to connect to Telegram"
```bash
# Vérifier la connexion internet
ping api.telegram.org

# Tester avec curl
curl https://api.telegram.org/bot8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI/getMe
```

### Problème: Le bot ne reçoit pas les messages
```bash
# Vérifier que le Chat ID est correct
cat .env | grep CHAT_ID

# Re-exécuter get_chat_id pour vérifier
python scripts/get_chat_id.py
```

### Problème: "Module not found: telegram"
```bash
# Réinstaller la dépendance
pip install --upgrade python-telegram-bot==20.7

# Vérifier l'installation
python -c "import telegram; print(telegram.__version__)"
```

## 📊 Vérification Finale

**Checklist de vérification:**
- [ ] `git pull` effectué avec succès
- [ ] `pip install python-telegram-bot==20.7` installé
- [ ] `.env` contient TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID
- [ ] `python scripts/test_telegram.py` fonctionne
- [ ] Bot redémarré avec `nohup python run_bot.py > bot.log 2>&1 &`
- [ ] Message de démarrage reçu sur Telegram
- [ ] Logs montrent "Telegram notifications enabled"
- [ ] Bot tourne en background (`ps aux | grep run_bot`)

## 🎉 Configuration Complète !

Une fois toutes les étapes validées, vous recevrez:
- 🟢 Notifications d'ouverture de positions
- 🔴 Notifications de fermeture de positions (avec PnL)
- 🧠 Notifications de cycles d'apprentissage ML (toutes les 2h)
- 🚨 Notifications d'erreurs critiques
- 📊 Rapports quotidiens (à 20h00)

Le bot est maintenant entièrement opérationnel avec notifications Telegram !
