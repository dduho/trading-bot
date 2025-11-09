# 🚀 Instructions de Déploiement VM - Méthodes Alternatives

## ⚠️ Problème de Connexion SSH

La connexion SSH directe via gcloud échoue avec "Connection timed out". Cela peut être dû à:
- Firewall bloquant le port SSH (22)
- Configuration IAP non activée
- Connexion réseau restrictive

## ✅ Solution: Utiliser Google Cloud Console (Interface Web)

### Méthode 1: SSH via Browser (Recommandée)

1. **Ouvrir Google Cloud Console:**
   - Allez sur https://console.cloud.google.com
   - Sélectionnez le projet: `trading-bot-477713`

2. **Aller sur Compute Engine:**
   - Menu latéral → Compute Engine → VM instances
   - Vous verrez: `trading-bot-instance` (RUNNING)

3. **Ouvrir SSH dans le navigateur:**
   - Cliquez sur le bouton **"SSH"** à droite de l'instance
   - Une fenêtre de terminal s'ouvre dans votre navigateur

4. **Exécuter le déploiement:**
   ```bash
   cd trading-bot
   bash deploy_telegram.sh
   ```

5. **Surveiller les logs:**
   ```bash
   tail -f bot.log
   ```

### Méthode 2: Éditer Manuellement via Console

Si le script échoue, voici les étapes manuelles:

#### Étape 1: Pull du code
```bash
cd trading-bot
git pull origin main
```

#### Étape 2: Installer la dépendance
```bash
pip install python-telegram-bot==20.7
```

#### Étape 3: Configurer .env
```bash
nano .env
```

Ajouter ces lignes (ou vérifier qu'elles existent):
```
TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
TELEGRAM_CHAT_ID=8350384028
```

Sauvegarder: `Ctrl+X`, `Y`, `Enter`

#### Étape 4: Tester Telegram
```bash
python scripts/test_telegram.py
```

Vous devriez recevoir un message de test sur Telegram.

#### Étape 5: Redémarrer le bot
```bash
# Arrêter l'ancien bot
pkill -f run_bot.py

# Attendre 2 secondes
sleep 2

# Démarrer le nouveau bot
nohup python run_bot.py > bot.log 2>&1 &

# Afficher les logs
tail -f bot.log
```

Vous devriez recevoir un message de démarrage sur Telegram !

### Méthode 3: Via FileZilla (Upload Manuel)

Si vous préférez FileZilla:

1. **Connectez-vous avec FileZilla** (voir FILEZILLA_SETUP.md)

2. **Téléchargez ces fichiers sur la VM:**
   - `src/telegram_notifier.py`
   - `src/notification_formatter.py`
   - `src/trading_bot.py`
   - `scripts/test_telegram.py`
   - `scripts/test_notifications.py`
   - `scripts/get_chat_id.py`
   - `config.yaml`
   - `requirements.txt`
   - `deploy_telegram.sh`

3. **Ouvrez un terminal FileZilla** et suivez Méthode 2 ci-dessus

## 🔍 Vérifications Post-Déploiement

### 1. Vérifier que le bot tourne
```bash
ps aux | grep run_bot
```

Devrait montrer un processus Python actif.

### 2. Vérifier les logs
```bash
tail -20 bot.log
```

Devrait montrer:
- "Telegram notifications enabled"
- "Trading Bot Started!"
- Pas d'erreurs critiques

### 3. Vérifier Telegram
Vous devriez avoir reçu:
- ✅ Message de test (si vous avez exécuté test_telegram.py)
- ✅ Message de démarrage du bot

### 4. Compter les notifications envoyées
```bash
grep "Telegram notification sent" bot.log | wc -l
```

Devrait être > 0 si le bot a envoyé des notifications.

## 📱 Messages Telegram à Attendre

Une fois déployé, vous recevrez automatiquement:

### Immédiatement
- 🤖 **Message de démarrage du bot** avec configuration

### Quand le bot trade
- 🟢 **Ouverture de position** - Détails complets
- 🔴 **Fermeture de position** - PnL, durée, raison

### Toutes les 2 heures
- 🧠 **Cycle d'apprentissage ML** - Métriques, adaptations

### En cas d'erreur
- 🚨 **Erreur critique** - Module, type, message

### Quotidiennement à 20h00
- 📊 **Rapport de performance** - Stats du jour

## 🆘 Support

### Le bot ne démarre pas
```bash
# Voir la fin des logs
tail -50 bot.log

# Chercher les erreurs
grep -i error bot.log
```

### Telegram ne fonctionne pas
```bash
# Vérifier les credentials
cat .env | grep TELEGRAM

# Tester la connexion
python scripts/test_telegram.py
```

### Le bot tourne mais pas de notifications
```bash
# Vérifier la config
cat config.yaml | grep -A 20 "notifications:"

# Vérifier que enabled: true
```

## 📚 Documentation Complète

- `TELEGRAM_IMPLEMENTATION_SUMMARY.md` - Résumé complet
- `VM_TELEGRAM_DEPLOYMENT.md` - Guide détaillé étape par étape
- `TELEGRAM_NOTIFICATIONS_PROCESS.md` - Documentation technique

## 🎯 Checklist de Déploiement

- [ ] VM accessible (console.cloud.google.com)
- [ ] SSH ouvert dans le navigateur
- [ ] `git pull` effectué
- [ ] `pip install python-telegram-bot==20.7` installé
- [ ] `.env` contient les credentials Telegram
- [ ] `python scripts/test_telegram.py` réussi
- [ ] Bot redémarré avec `nohup python run_bot.py > bot.log 2>&1 &`
- [ ] Message de démarrage reçu sur Telegram
- [ ] Logs montrent "Telegram notifications enabled"

## ✨ C'est Parti !

Le système est prêt. Il suffit maintenant de:
1. Aller sur console.cloud.google.com
2. Ouvrir SSH dans le navigateur
3. Exécuter `bash deploy_telegram.sh`

Et c'est tout ! Les notifications Telegram seront actives ! 🚀
