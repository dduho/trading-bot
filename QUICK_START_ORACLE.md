# 🚀 Démarrage Rapide - Oracle Cloud (30 min)

**Héberge ton bot gratuitement 24/7 pour toujours !**

---

## ⚡ Version Ultra-Rapide (TL;DR)

### Avec GitHub (RECOMMANDÉ - Plus Simple) :

```bash
# 1. Connecte-toi à ta VM Oracle
ssh -i ta_cle.key ubuntu@IP_SERVEUR

# 2. Clone ton repo
git clone https://github.com/TON_USERNAME/trading-bot.git
cd trading-bot

# 3. Lance le script d'installation
chmod +x setup_oracle_cloud.sh
./setup_oracle_cloud.sh

# 4. Vérifier
sudo journalctl -u trading-bot -f
```

### Sans GitHub (Upload Manuel) :

```powershell
# 1. Sur ton PC - Upload les fichiers
cd "C:\Users\black\OneDrive\Documents\Web Projects\trading-bot"
.\upload_to_oracle.ps1
```

```bash
# 2. Sur Oracle Cloud - Installer
cd ~/trading-bot
chmod +x setup_oracle_cloud.sh
./setup_oracle_cloud.sh
```

**C'est tout ! 🎉**

💡 **Si ton projet est sur GitHub, consulte** [ORACLE_SETUP_WITH_GITHUB.md](ORACLE_SETUP_WITH_GITHUB.md) **pour un setup encore plus simple !**

---

## 📋 Guide Détaillé (30 min)

### Phase 1 : Créer le Compte (10 min)

1. **Va sur** https://www.oracle.com/cloud/free/
2. **Clique** "Start for Free"
3. **Remplis le formulaire** (email, nom, pays)
4. **Choisis ta région** : France (Paris) ou Germany (Frankfurt)
5. **Vérifie ton email**
6. **Ajoute ta carte bancaire** (pas de débit, juste vérification)
7. **Attends la validation** (5-30 min)

✅ **Tu reçois un email "Account provisioned"**

---

### Phase 2 : Créer la VM (10 min)

1. **Connexion** → https://cloud.oracle.com
2. **Menu ☰** → Compute → Instances
3. **Create Instance**

**Configuration :**
- **Name:** trading-bot
- **Image:** Ubuntu 22.04
- **Shape:** VM.Standard.A1.Flex (Ampere)
  - OCPU: 2-4
  - Memory: 12-24 GB
  - ✅ Vérifie "Always Free Eligible"
- **SSH Keys:** Generate key pair → **Sauvegarde le fichier .key**
- **Create**

4. **Note l'IP publique** (ex: 158.101.123.45)

**Configurer le Firewall :**
1. Instance Details → Primary VNIC → Subnet
2. Security Lists → Default Security List
3. Add Ingress Rules :
   - Source: 0.0.0.0/0
   - Port: 22
   - Description: SSH

✅ **VM prête !**

---

### Phase 3 : Upload le Bot (5 min)

**Option A - Script PowerShell (FACILE) :**

```powershell
cd "C:\Users\black\OneDrive\Documents\Web Projects\trading-bot"
.\upload_to_oracle.ps1
```

Le script va :
- Demander le chemin de ta clé SSH
- Demander l'IP du serveur
- Uploader tous les fichiers
- Te connecter automatiquement

**Option B - Manuel :**

```powershell
cd "C:\Users\black\OneDrive\Documents\Web Projects\trading-bot"

scp -i "C:\Users\black\Downloads\ssh-key-XXX.key" -r * ubuntu@IP_SERVEUR:~/trading-bot/
```

✅ **Fichiers uploadés !**

---

### Phase 4 : Installation Automatique (5 min)

**Connecte-toi au serveur :**

```powershell
ssh -i "C:\Users\black\Downloads\ssh-key-XXX.key" ubuntu@IP_SERVEUR
```

**Lance le script d'installation :**

```bash
cd ~/trading-bot
chmod +x setup_oracle_cloud.sh
./setup_oracle_cloud.sh
```

Le script va :
1. ✅ Mettre à jour le système
2. ✅ Installer Python et dépendances
3. ✅ Installer TA-Lib
4. ✅ Installer les requirements
5. ✅ Créer le service systemd
6. ✅ Tout configurer

À la fin, il demande si tu veux démarrer → **dis oui (y)**

✅ **Bot installé et démarré !**

---

## 🎯 Commandes Essentielles

### Voir si le bot tourne

```bash
sudo systemctl status trading-bot
# Active: active (running) = OK ✅
```

### Voir les logs en direct

```bash
sudo journalctl -u trading-bot -f
# Ctrl+C pour arrêter
```

### Redémarrer le bot

```bash
sudo systemctl restart trading-bot
```

### Arrêter le bot

```bash
sudo systemctl stop trading-bot
```

### Tester le ML

```bash
cd ~/trading-bot
python3 test_ml_system.py
```

---

## 📊 Vérifications

### 1. Le Bot Fonctionne ?

```bash
sudo systemctl status trading-bot
```

Devrait afficher :
```
● trading-bot.service - Trading Bot with Machine Learning
   Loaded: loaded
   Active: active (running) since...
```

### 2. Le ML Est Actif ?

```bash
cd ~/trading-bot
python3 -c "
import sys
sys.path.append('src')
from learning_engine import AdaptiveLearningEngine
from ml_optimizer import MLOptimizer
from performance_analyzer import PerformanceAnalyzer
from trade_database import TradeDatabase
import yaml

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

db = TradeDatabase()
ml = MLOptimizer(db)
ml.load_model()
analyzer = PerformanceAnalyzer(db)
engine = AdaptiveLearningEngine(db, analyzer, ml, config)

print(f'Learning enabled: {engine.learning_enabled}')
print(f'Learning interval: {engine.learning_interval_hours}h')
print(f'Auto-apply: {config[\"learning\"][\"auto_apply_adaptations\"]}')
"
```

Devrait afficher :
```
Learning enabled: True
Learning interval: 12h
Auto-apply: True
```

### 3. La Base de Données Se Remplit ?

```bash
cd ~/trading-bot
ls -lh data/trading_history.db
```

Devrait afficher la taille du fichier (qui grandit au fil des trades)

---

## 🔧 Maintenance

### Mettre à Jour le Bot

**Sur ton PC :**
```powershell
cd "C:\Users\black\OneDrive\Documents\Web Projects\trading-bot"
.\upload_to_oracle.ps1
```

**Sur le serveur :**
```bash
sudo systemctl restart trading-bot
```

### Sauvegarder les Données

```bash
# Sur le serveur
cd ~/trading-bot
tar -czf backup-$(date +%Y%m%d).tar.gz data/ models/

# Télécharger sur ton PC (PowerShell)
scp -i "CHEMIN_CLE.key" ubuntu@IP:~/trading-bot/backup-*.tar.gz C:\Backups\
```

### Mises à Jour de Sécurité (1x/mois)

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

---

## 🆘 Problèmes Courants

### "Permission denied" lors du SSH

**Solution :**
```powershell
# Fixer les permissions de la clé
icacls "CHEMIN_CLE.key" /inheritance:r
icacls "CHEMIN_CLE.key" /grant:r "%USERNAME%:R"
```

### Le bot ne démarre pas

**Vérifier l'erreur :**
```bash
sudo journalctl -u trading-bot -n 50
```

**Tester manuellement :**
```bash
cd ~/trading-bot
python3 src/trading_bot.py
```

### "Module not found" error

**Réinstaller les dépendances :**
```bash
cd ~/trading-bot
pip3 install -r requirements.txt --break-system-packages --force-reinstall
```

### Le ML ne fonctionne pas

**Vérifier les modèles :**
```bash
cd ~/trading-bot
ls -lh models/
```

**Tester :**
```bash
python3 test_ml_system.py
```

---

## 📱 Accès à Distance

### Depuis n'importe où :

```bash
ssh -i "CHEMIN_CLE.key" ubuntu@IP_PUBLIQUE
```

### Voir les logs :

```bash
sudo journalctl -u trading-bot -f
```

### Arrêter/démarrer :

```bash
sudo systemctl stop trading-bot    # Arrêter
sudo systemctl start trading-bot   # Démarrer
sudo systemctl restart trading-bot # Redémarrer
```

---

## ✅ Checklist Finale

- [ ] Compte Oracle Cloud créé
- [ ] VM créée et accessible
- [ ] Fichiers uploadés
- [ ] Script d'installation exécuté
- [ ] Bot démarré (`systemctl status` → active)
- [ ] Logs OK (`journalctl -f` → pas d'erreurs)
- [ ] ML actif (test_ml_system.py → 100%)
- [ ] Base de données créée (trading_history.db existe)

**Si tout est ✅ → Ton bot tourne 24/7 gratuitement ! 🎉**

---

## 🎁 Bonus : Monitoring

### Créer un Alias pour Logs

Ajoute à `~/.bashrc` :

```bash
alias bot-logs='sudo journalctl -u trading-bot -f'
alias bot-status='sudo systemctl status trading-bot'
alias bot-restart='sudo systemctl restart trading-bot'
alias bot-test='cd ~/trading-bot && python3 test_ml_system.py'
```

Puis :
```bash
source ~/.bashrc
```

Maintenant tu peux juste taper :
- `bot-logs` → voir les logs
- `bot-status` → voir le status
- `bot-restart` → redémarrer
- `bot-test` → tester le ML

---

## 🚀 C'est Parti !

**Ton bot est maintenant :**
- ✅ Hébergé gratuitement 24/7
- ✅ Auto-optimisé par ML toutes les 12h
- ✅ Accessible de n'importe où
- ✅ Sauvegardé automatiquement

**Happy Trading! 💰**

---

## 📚 Ressources

- Guide complet : [ORACLE_CLOUD_SETUP_GUIDE.md](ORACLE_CLOUD_SETUP_GUIDE.md)
- ML Changes : [ML_CHANGES_APPLIED.md](ML_CHANGES_APPLIED.md)
- Diagnostic ML : `python3 test_ml_system.py`
