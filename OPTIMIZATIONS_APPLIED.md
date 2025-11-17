# Optimisations du Bot Autonome - Novembre 2025

## 🎯 Problèmes Identifiés et Résolus

### 1. **Blocage par limite quotidienne de trades**
**Problème:** Le bot atteignait 80 trades/jour et cessait complètement de trader jusqu'au lendemain.

**Solution:**
- ✅ Augmenté `max_daily_trades` à 200 (au lieu de 80)
- ✅ Ajouté détection automatique du blocage dans le watchdog
- ✅ Force reset automatique si `daily_trades` est bloqué après minuit
- ✅ Reset vérifié à chaque itération du trading loop

### 2. **Watchdog trop agressif**
**Problème:** Le watchdog réinitialisait constamment la confidence à 3% et fermait toutes les positions.

**Solution:**
- ✅ Réduit seuil `min_trades_per_hour` de 2 à 0.5 (plus réaliste)
- ✅ Augmenté `max_position_age` de 6h à 24h (moins de fermetures forcées)
- ✅ Anti-spam: ne reset pas confidence plus d'1x par heure
- ✅ Skip reset si confidence déjà ≤ 3%
- ✅ Détecte et gère spécifiquement le cas "daily limit atteint"

### 3. **Confidence mal plafonnée**
**Problème:** Les optimisations automatiques poussaient min_confidence > 15%, bloquant tous les trades (signaux typiques = 14-20%).

**Solution:**
- ✅ Hard cap à 15% dans `signal_generator.py`
- ✅ Plafond adaptatif dans `dynamic_confidence_manager.py`:
  - Phase apprentissage (WR < 40%): max 8%
  - Phase intermédiaire (WR 40-50%): max 10%
  - Phase mature (WR 50-55%): max 12%
  - Phase expert (WR > 55%): max 15%
- ✅ Watchdog cap augmentation à 10% max

### 4. **Positions fantômes**
**Problème:** Positions existaient en mémoire (`risk_manager`) mais pas en DB, causant incohérences.

**Solution:**
- ✅ Clear systématique des positions fermées dans `risk_manager`
- ✅ Restauration des positions ouvertes depuis DB au démarrage
- ✅ Watchdog détecte et nettoie les phantoms

### 5. **Paramètres d'apprentissage trop agressifs**
**Problème:** Learning cycle toutes les 30min avec seulement 5 trades minimum → bruit, pas assez de signal.

**Solution:**
- ✅ `learning_interval_hours`: 0.5h → 2h
- ✅ `min_trades_for_learning`: 5 → 30
- ✅ `min_accuracy_threshold`: 52% → 55%

## 📊 Nouveaux Paramètres Optimisés

### Configuration Risk Management
```yaml
risk:
  max_position_size_percent: 3       # 2% → 3% (balance volume/risk)
  max_open_positions: 5              # 8 → 5 (moins de surcharge)
  max_daily_trades: 200              # 80 → 200 (assez pour apprendre)
  cooldown_seconds: 30               # 45 → 30 (optimal)
```

### Configuration Learning
```yaml
learning:
  learning_interval_hours: 2         # 0.5 → 2h (plus stable)
  min_trades_for_learning: 30        # 5 → 30 (données suffisantes)
  ml_model:
    min_accuracy_threshold: 0.55     # 52% → 55% (plus fiable)
    retrain_interval_hours: 6        # 12 → 6h (équilibre)
```

### Watchdog Thresholds
```python
min_trades_per_hour: 0.5            # 2 → 0.5 (réaliste)
max_position_age_hours: 24          # 6 → 24 (moins agressif)
confidence_check_interval: 30       # 5 → 30 min (moins spam)
```

## 🚀 Nouveau Système d'Optimisation Autonome

### `autonomous_optimizer.py`
Script qui analyse les performances sur 7 jours et ajuste automatiquement:

1. **Confidence Threshold**
   - Win rate < 45% → Augmente sélectivité
   - Win rate 55-65% + faible volume → Baisse pour plus de trades
   - Win rate > 65% → Mode agressif

2. **Position Sizing**
   - Drawdown important → Réduit taille
   - Profit factor > 2.0 + WR > 55% → Augmente taille
   - 4+ pertes consécutives → Réduit taille

3. **Stop Loss / Take Profit**
   - Win rate < 40% → Élargit SL (trop serré)
   - Profit factor < 1.2 → Augmente TP
   - Performance excellente → Peut serrer SL

## 🔄 Déploiement

### Méthode Automatique (Recommandée)
```powershell
.\deploy_optimizations.ps1
```

Ce script:
1. ✅ Commit et push sur git
2. ✅ Pull sur la VM
3. ✅ Stop le bot
4. ✅ Run autonomous_optimizer
5. ✅ Restart le bot
6. ✅ Affiche les logs

### Méthode Manuelle
```bash
# Local
git add .
git commit -m "Optimizations applied"
git push origin main

# Sur VM
ssh duhodavid12@trading-bot-instance
cd ~/trading-bot
git pull origin main

# Stop bot
pkill -f 'python.*run_bot.py'

# Run optimizer (optionnel)
python3 autonomous_optimizer.py

# Restart bot
nohup python3 run_bot.py > trading_bot.log 2>&1 &

# Monitor
tail -f trading_bot.log
```

## 📈 Améliorations Attendues

### Court terme (1-3 jours)
- ✅ Pas de blocage quotidien
- ✅ Moins de notifications spam du watchdog
- ✅ Trading continu 24/7
- ✅ Confidence stable entre 3-10%

### Moyen terme (1-2 semaines)
- 📈 Win rate: 15% → 45-55%
- 📈 Profit factor: 0.8 → 1.5-2.0
- 📈 Volume: 30-100 trades/jour stable
- 📈 Moins de pertes consécutives

### Long terme (1 mois+)
- 🎯 Win rate: 55-60%
- 🎯 Profit factor: 2.0-2.5
- 🎯 Sharpe ratio: > 1.2
- 🎯 Système complètement autonome

## 🔍 Monitoring

### Vérifier que tout fonctionne
```bash
# Check daily trades counter
gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command="tail -n 100 ~/trading-bot/trading_bot.log | grep 'daily_trades='"

# Check confidence level
gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command="tail -n 100 ~/trading-bot/trading_bot.log | grep 'min_confidence'"

# Check watchdog activity
gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command="tail -n 200 ~/trading-bot/trading_bot.log | grep 'WATCHDOG\|health'"

# Check recent trades
gcloud compute ssh duhodavid12@trading-bot-instance --zone=europe-west1-d --command="cd ~/trading-bot && python3 check_db.py"
```

### Métriques à Surveiller
- ✅ `daily_trades` se reset à minuit
- ✅ `min_confidence` reste entre 3-10%
- ✅ Watchdog ne spam plus toutes les 5min
- ✅ Open positions sont cohérentes (DB = memory)
- ✅ Trades continuent 24/7

## 🛡️ Safety Features

1. **Hard caps**: Confidence plafonnée à 15% maximum
2. **Daily reset**: Force reset si détecté bloqué
3. **Anti-spam**: Watchdog limité à 1 intervention/heure
4. **Adaptive ceiling**: Plafond confidence s'adapte aux performances
5. **Phantom cleanup**: Détection et nettoyage auto des positions fantômes

## 📞 En Cas de Problème

### Bot ne trade plus
```bash
# Vérifier daily limit
python3 -c "from src.risk_manager import *; import yaml; c=yaml.safe_load(open('config.yaml')); r=RiskManager(c['risk']); print(f'Daily trades: {r.daily_trades}/{c[\"risk\"][\"max_daily_trades\"]}')"

# Force reset manuel
python3 -c "from src.trade_database import TradeDatabase; from src.risk_manager import *; import yaml; c=yaml.safe_load(open('config.yaml')); r=RiskManager(c['risk']); r.daily_trades=0; print('Reset done')"
```

### Confidence bloquée trop haut
```bash
# Check current value
grep "min_confidence" config.yaml

# Force reset à 5%
python3 -c "import yaml; c=yaml.safe_load(open('config.yaml')); c['strategy']['min_confidence']=0.05; yaml.dump(c,open('config.yaml','w')); print('Confidence reset to 5%')"
```

### Positions fantômes
```bash
# Lancer nettoyage
python3 -c "from src.trade_database import TradeDatabase; from src.autonomous_watchdog import *; import yaml; db=TradeDatabase(); c=yaml.safe_load(open('config.yaml')); w=AutonomousWatchdog(db,c); w._clear_phantom_positions()"
```

## ✅ Checklist Post-Déploiement

- [ ] Bot redémarré sans erreurs
- [ ] Logs montrent "Daily statistics reset" à minuit
- [ ] Confidence entre 3-10%
- [ ] Watchdog check toutes les 30min (pas 5min)
- [ ] Trades s'exécutent normalement
- [ ] Pas de spam Telegram
- [ ] DB et memory positions cohérentes
- [ ] Learning cycle toutes les 2h

---

*Dernière mise à jour: 17 novembre 2025*
*Version: 2.0 - Autonomous & Self-Optimizing*
