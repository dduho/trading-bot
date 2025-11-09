# Configuration Telegram - Guide Rapide

## ✅ Fichiers Créés

### Scripts
- `scripts/get_chat_id.py` - Récupérer votre Chat ID Telegram
- `scripts/test_telegram.py` - Tester la connexion au bot
- `scripts/test_notifications.py` - Tester tous les types de notifications

### Source
- `src/telegram_notifier.py` - Service de notifications Telegram
- `src/notification_formatter.py` - Formateur de messages

### Configuration
- `config.yaml` - Configuration des notifications ajoutée
- `.env.example` - Template mis à jour avec Telegram
- `requirements.txt` - Dépendance python-telegram-bot==20.7 ajoutée

## 📋 Étapes de Configuration

### 1. Obtenir le Chat ID (EN COURS)

**Token du bot fourni:**
```
8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
```

**Instructions:**
1. Ouvrez Telegram
2. Cherchez votre bot par son username
3. Cliquez sur "Start" ou envoyez un message
4. Exécutez: `python scripts/get_chat_id.py`

### 2. Créer le fichier .env

Une fois le Chat ID obtenu, créez `.env` avec:

```bash
TELEGRAM_BOT_TOKEN=8243134407:AAFboClTP0SUpN7qAd68OCRlgHNIA8v3JuI
TELEGRAM_CHAT_ID=votre_chat_id_ici

# Autres variables si nécessaire
TRADING_MODE=paper
```

### 3. Installer les dépendances

```bash
pip install python-telegram-bot==20.7
# ou
pip install -r requirements.txt
```

### 4. Tester la connexion

```bash
python scripts/test_telegram.py
```

### 5. Tester les notifications

```bash
python scripts/test_notifications.py
```

### 6. Intégrer dans le bot

L'intégration dans `trading_bot.py` sera faite après validation des tests.

## 🔔 Types de Notifications Configurées

### ✅ Activées par Défaut

- **Trades** - Ouverture/fermeture de positions
- **Learning** - Cycles d'apprentissage ML (toutes les 2h)
- **Errors** - Toutes les erreurs (critiques et warnings)
- **Reports** - Rapport quotidien à 20h00 (Europe/Paris)

### ⚙️ Configuration

Dans `config.yaml`:

```yaml
notifications:
  enabled: true
  telegram:
    enabled: true
    trades:
      enabled: true
      min_pnl_percent: 0.0  # Notifier tous les trades
    learning:
      enabled: true
    errors:
      enabled: true
      critical_only: false
    reports:
      enabled: true
      schedule: "daily"
      time: "20:00"
    formatting:
      use_emoji: true
      use_markdown: true
      timezone: "Europe/Paris"
    rate_limit:
      max_messages_per_hour: 30
      cooldown_between_messages: 2
```

## 🚀 Prochaines Étapes

1. ⏳ **EN ATTENTE:** Envoyer un message au bot sur Telegram
2. ⏳ Obtenir le Chat ID
3. ⏳ Créer le fichier .env
4. ⏳ Tester la connexion
5. ⏳ Tester les notifications
6. ⏳ Intégrer dans trading_bot.py
7. ⏳ Committer et déployer

## 🔒 Sécurité

- ✅ `.env` est dans `.gitignore` (credentials ne seront pas committés)
- ✅ `.env.example` fourni comme template
- ✅ Rate limiting configuré (30 messages/heure max)
- ✅ Gestion d'erreurs avec retry pour messages urgents

## 📖 Documentation

Voir `TELEGRAM_NOTIFICATIONS_PROCESS.md` pour la documentation complète.
