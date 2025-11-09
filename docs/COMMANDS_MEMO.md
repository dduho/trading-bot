# ⚡ Mémo Rapide - Commandes Bot

## 🎮 Gestion du Bot sur VM

```bash
./bot_manager.sh start      # Démarrer le bot
./bot_manager.sh stop       # Arrêter le bot
./bot_manager.sh restart    # Redémarrer le bot
./bot_manager.sh status     # Vérifier le statut
./bot_manager.sh logs       # Voir les logs en temps réel
./bot_manager.sh update     # Mettre à jour depuis GitHub
```

---

## 📱 Commandes Telegram (depuis votre téléphone)

```
/start      - Menu d'aide
/status     - État du bot et portfolio
/ml         - Métriques ML et apprentissage
/positions  - Positions ouvertes
/performance- Stats globales
/today      - Résumé du jour
```

---

## 🔄 Mise à Jour Complète

```bash
# Sur la VM (via PuTTY)
cd ~/trading-bot
./bot_manager.sh update
```

Ça fait automatiquement :
- Stop le bot
- Pull GitHub
- Install dépendances
- Redémarre le bot

---

## 🆘 Aide Rapide

**Bot qui ne répond pas ?**
```bash
./bot_manager.sh restart
```

**Vérifier les erreurs ?**
```bash
./bot_manager.sh logs
```

**Vérifier si le bot tourne ?**
```bash
./bot_manager.sh status
```

---

## 📚 Documentation Complète

- [Guide de Mise à Jour](UPDATE_TELEGRAM.md)
- [Commandes Telegram](../TELEGRAM_COMMANDS.md)
- [Quick Start](../QUICK_START_COMMANDS.md)
