# 🚀 Déploiement du Trading Bot

Guide complet pour déployer ton bot ML sur Oracle Cloud (gratuit 24/7)

---

## 📚 Choisis ton Guide

### ✨ Ton Bot est sur GitHub ? (RECOMMANDÉ)

**→ Suis** [ORACLE_SETUP_WITH_GITHUB.md](ORACLE_SETUP_WITH_GITHUB.md)

**Avantages :**
- ✅ Installation en 15 min (vs 30 min)
- ✅ Mises à jour ultra-rapides (git pull)
- ✅ Versioning automatique
- ✅ Backup sur GitHub
- ✅ Rollback facile si problème

**Setup :**
```bash
git clone https://github.com/TON_USERNAME/trading-bot.git
cd trading-bot
./setup_oracle_cloud.sh
```

---

### 📦 Ton Bot est Local ?

**→ Suis** [QUICK_START_ORACLE.md](QUICK_START_ORACLE.md)

**Ce que tu dois faire :**
- Upload les fichiers via SCP
- Installer manuellement
- Mettre à jour en re-uploadant

**Setup :**
```powershell
.\upload_to_oracle.ps1
```

---

## 🎯 Comparaison

| Critère | Avec GitHub | Sans GitHub |
|---------|-------------|-------------|
| **Setup initial** | 15 min | 30 min |
| **Commande** | `git clone` | `scp -r` (lent) |
| **Mise à jour** | `git pull` (2 sec) | Re-upload tout (5 min) |
| **Rollback** | `git checkout` | ❌ Difficile |
| **Backup** | ✅ Auto sur GitHub | ❌ Manuel |
| **Collaboration** | ✅ Facile | ❌ Compliqué |
| **CI/CD possible** | ✅ Oui (webhook) | ❌ Non |

---

## 🆓 Oracle Cloud Free Tier

**Ce que tu obtiens GRATUITEMENT à VIE :**

- 🖥️ **2-4 vCPU Ampere** (ARM)
- 💾 **12-24 GB RAM**
- 💿 **200 GB stockage**
- 🌐 **Bande passante illimitée**
- ⚡ **Performance excellente**

**Parfait pour :**
- ✅ Bot trading 24/7
- ✅ Machine Learning
- ✅ Base de données
- ✅ Plusieurs bots simultanés

---

## 📋 Étapes Communes

### 1. Créer Compte Oracle Cloud
https://www.oracle.com/cloud/free/

### 2. Créer VM
- Ubuntu 22.04
- Ampere (Always Free)
- 2-4 vCPU, 12-24 GB RAM

### 3. Installer le Bot
Choisis ta méthode (GitHub ou Upload)

### 4. Démarrer
```bash
sudo systemctl start trading-bot
```

### 5. Vérifier
```bash
sudo systemctl status trading-bot
sudo journalctl -u trading-bot -f
```

---

## 🔧 Workflow Quotidien

### Avec GitHub (Optimal)

**Sur ton PC :**
```bash
# Modifier le code
git add .
git commit -m "Update strategy"
git push
```

**Sur le serveur :**
```bash
cd ~/trading-bot
git pull
sudo systemctl restart trading-bot
```

**Ou crée un alias :**
```bash
alias update-bot='cd ~/trading-bot && git pull && sudo systemctl restart trading-bot'
```

Ensuite : `update-bot` → c'est fait ! ⚡

---

### Sans GitHub

**Sur ton PC :**
```powershell
.\upload_to_oracle.ps1
```

**Sur le serveur :**
```bash
sudo systemctl restart trading-bot
```

---

## 🎁 Bonus : Auto-Deploy avec GitHub

**Webhook pour déploiement automatique à chaque push !**

Détails complets dans [ORACLE_SETUP_WITH_GITHUB.md](ORACLE_SETUP_WITH_GITHUB.md#-bonus--webhook-github-auto-deploy)

**Setup rapide :**
1. Crée `deploy-bot.sh` sur le serveur
2. Configure webhook sur GitHub
3. À chaque push → auto-deploy ! 🚀

---

## 📊 Configuration ML Actuelle

**Ton bot est déjà optimisé :**

| Paramètre | Valeur | Optimisé par ML |
|-----------|--------|-----------------|
| **min_confidence** | 0.60 | ✅ |
| **learning_interval** | 12h | ✅ |
| **auto_apply** | TRUE | ✅ |
| **mode** | MODERATE | ✅ |

**Poids optimisés :**
- moving_averages: 33% (le plus important)
- macd: 21%
- rsi: 18%
- volume: 18%
- trend: 11%

Voir [ML_CHANGES_APPLIED.md](ML_CHANGES_APPLIED.md) pour détails

---

## 🆘 Support

### Problème de déploiement ?

1. **Vérifier les guides :**
   - [ORACLE_SETUP_WITH_GITHUB.md](ORACLE_SETUP_WITH_GITHUB.md) - Avec GitHub
   - [QUICK_START_ORACLE.md](QUICK_START_ORACLE.md) - Sans GitHub
   - [ORACLE_CLOUD_SETUP_GUIDE.md](ORACLE_CLOUD_SETUP_GUIDE.md) - Guide complet détaillé

2. **Vérifier les logs :**
   ```bash
   sudo journalctl -u trading-bot -n 100
   ```

3. **Tester manuellement :**
   ```bash
   cd ~/trading-bot
   python3 src/trading_bot.py
   ```

### Problème ML ?

```bash
cd ~/trading-bot
python3 test_ml_system.py
```

Devrait afficher : `100% - ALL SYSTEMS OPERATIONAL`

---

## ✅ Checklist Pré-Deploy

**Avant de déployer, assure-toi que :**

- [ ] Compte Oracle Cloud créé et validé
- [ ] VM créée (Ubuntu 22.04, Ampere)
- [ ] Clé SSH téléchargée et sauvegardée
- [ ] Firewall configuré (port 22 ouvert)
- [ ] IP publique notée

**Si GitHub :**
- [ ] Repo accessible (public ou clé SSH configurée)
- [ ] Fichiers `src/`, `config.yaml`, `requirements.txt` présents
- [ ] `.gitignore` configuré (pas de secrets)

**Si Upload manuel :**
- [ ] Script `upload_to_oracle.ps1` prêt
- [ ] Chemin clé SSH correct
- [ ] Tous les fichiers dans le dossier local

---

## 📈 Après Déploiement

### Monitoring

```bash
# Status
sudo systemctl status trading-bot

# Logs temps réel
sudo journalctl -u trading-bot -f

# Performance
htop

# Espace disque
df -h
```

### Maintenance

**Mise à jour système (1x/mois) :**
```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

**Backup base de données (1x/semaine) :**
```bash
cd ~/trading-bot
tar -czf backup-$(date +%Y%m%d).tar.gz data/ models/
```

**Télécharger backup sur PC :**
```powershell
scp -i "ta_cle.key" ubuntu@IP:~/trading-bot/backup-*.tar.gz C:\Backups\
```

---

## 🎯 Prochaines Étapes

1. **Choisis ton guide**
   - GitHub : [ORACLE_SETUP_WITH_GITHUB.md](ORACLE_SETUP_WITH_GITHUB.md)
   - Local : [QUICK_START_ORACLE.md](QUICK_START_ORACLE.md)

2. **Crée ton compte Oracle Cloud**
   - https://www.oracle.com/cloud/free/

3. **Déploie ton bot**
   - Suis le guide étape par étape

4. **Profite de ton bot 24/7 gratuit !** 🎉

---

## 📚 Documentation Complète

| Fichier | Description | Durée |
|---------|-------------|-------|
| [README_DEPLOYMENT.md](README_DEPLOYMENT.md) | Ce fichier - Vue d'ensemble | 5 min |
| [ORACLE_SETUP_WITH_GITHUB.md](ORACLE_SETUP_WITH_GITHUB.md) | **Setup avec GitHub** | 15 min |
| [QUICK_START_ORACLE.md](QUICK_START_ORACLE.md) | **Setup rapide** | 30 min |
| [ORACLE_CLOUD_SETUP_GUIDE.md](ORACLE_CLOUD_SETUP_GUIDE.md) | Guide détaillé complet | 1h |
| [ML_CHANGES_APPLIED.md](ML_CHANGES_APPLIED.md) | Optimisations ML appliquées | 10 min |
| [LEARNING_INTERVAL_ANALYSIS.md](LEARNING_INTERVAL_ANALYSIS.md) | Analyse intervalle ML | 5 min |

---

## 🚀 Commence Maintenant !

**Si ton bot est sur GitHub →** [ORACLE_SETUP_WITH_GITHUB.md](ORACLE_SETUP_WITH_GITHUB.md)

**Sinon →** [QUICK_START_ORACLE.md](QUICK_START_ORACLE.md)

**Bonne chance ! 💰**
