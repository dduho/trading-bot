# 🚀 Setup Oracle Cloud avec GitHub (15 min)

**Version simplifiée - Ton bot est déjà sur GitHub !**

---

## ⚡ Version Ultra-Rapide

### 1. Crée ton Compte Oracle Cloud (10 min)
- Va sur https://www.oracle.com/cloud/free/
- Inscription gratuite (carte bancaire pour vérification, pas débitée)

### 2. Crée ta VM (5 min)
- Menu → Compute → Instances → Create
- Ubuntu 22.04, Ampere (2-4 vCPU, 12-24 GB RAM)
- Sauvegarde la clé SSH

### 3. Installation Automatique (1 commande)
```bash
# Connecte-toi à ta VM
ssh -i ta_cle.key ubuntu@IP_SERVEUR

# Lance le script (il te demandera ton URL GitHub)
curl -sSL https://raw.githubusercontent.com/TON_USERNAME/trading-bot/main/setup_oracle_cloud.sh | bash
```

**OU clonage manuel :**

```bash
# Clone ton repo
git clone https://github.com/TON_USERNAME/trading-bot.git
cd trading-bot

# Lance le script
chmod +x setup_oracle_cloud.sh
./setup_oracle_cloud.sh
```

**C'est tout ! 🎉**

---

## 📋 Guide Détaillé

### Étape 1 : Compte Oracle Cloud

1. **Inscription** : https://www.oracle.com/cloud/free/
2. **Remplis le formulaire** (email, carte bancaire pour vérif)
3. **Choisis ta région** : France (Paris) ou Germany (Frankfurt)
4. **Attends la validation** (5-30 min)

### Étape 2 : Créer la VM

1. **Dashboard Oracle Cloud** → Menu ☰ → Compute → Instances
2. **Create Instance**

**Configuration :**
```
Name: trading-bot
Image: Ubuntu 22.04
Shape: VM.Standard.A1.Flex (Ampere)
  - OCPU: 2 (ou jusqu'à 4)
  - Memory: 12 GB (ou jusqu'à 24 GB)
  - ✅ "Always Free Eligible" visible
SSH Keys: Generate → Sauvegarde le .key
```

3. **Create**
4. **Note l'IP publique**

**Configurer le Firewall :**
- Instance Details → Primary VNIC → Subnet → Security Lists
- Add Ingress Rules : Port 22, Source 0.0.0.0/0

### Étape 3 : Connexion SSH

**Windows PowerShell :**
```powershell
# Aller dans le dossier de la clé
cd C:\Users\TON_NOM\Downloads

# Fixer les permissions
icacls ssh-key-2023-11-08.key /inheritance:r
icacls ssh-key-2023-11-08.key /grant:r "%USERNAME%:R"

# Se connecter
ssh -i ssh-key-2023-11-08.key ubuntu@IP_PUBLIQUE
```

### Étape 4 : Installation du Bot (AVEC GITHUB)

**Tu as 2 options :**

#### Option A : Script Automatique (RECOMMANDÉ)

```bash
# Le script va te demander ton URL GitHub
curl -sSL https://raw.githubusercontent.com/TON_USERNAME/trading-bot/main/setup_oracle_cloud.sh | bash
```

**OU si le script n'est pas encore sur GitHub :**

```bash
# Télécharge le script
wget https://raw.githubusercontent.com/TON_USERNAME/trading-bot/main/setup_oracle_cloud.sh
chmod +x setup_oracle_cloud.sh
./setup_oracle_cloud.sh
```

Quand le script demande l'URL GitHub, donne :
```
https://github.com/TON_USERNAME/trading-bot.git
```

#### Option B : Installation Manuelle

```bash
# 1. Update système
sudo apt update && sudo apt upgrade -y

# 2. Installer dépendances
sudo apt install -y python3-pip git curl nano htop screen

# 3. Installer TA-Lib
sudo apt install -y libta-lib0-dev
pip3 install ta-lib --break-system-packages

# 4. Cloner ton repo GitHub
cd ~
git clone https://github.com/TON_USERNAME/trading-bot.git
cd trading-bot

# 5. Installer requirements Python
pip3 install -r requirements.txt --break-system-packages

# 6. Créer le service systemd
sudo nano /etc/systemd/system/trading-bot.service
```

**Contenu du service :**
```ini
[Unit]
Description=Trading Bot with Machine Learning
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trading-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 /home/ubuntu/trading-bot/src/trading_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 7. Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

# 8. Vérifier
sudo systemctl status trading-bot
```

---

## 🔄 Mettre à Jour le Bot (AVEC GITHUB)

**C'est TRÈS simple avec GitHub !**

### Sur ton PC (commit & push)
```bash
git add .
git commit -m "Update config"
git push
```

### Sur le serveur Oracle (pull & restart)
```bash
# Se connecter
ssh -i ta_cle.key ubuntu@IP

# Mettre à jour
cd ~/trading-bot
git pull

# Redémarrer
sudo systemctl restart trading-bot

# Vérifier
sudo systemctl status trading-bot
```

**Bonus : Script de mise à jour automatique**

Crée `~/update-bot.sh` :
```bash
#!/bin/bash
cd ~/trading-bot
git pull
sudo systemctl restart trading-bot
echo "Bot updated and restarted!"
```

```bash
chmod +x ~/update-bot.sh
```

Maintenant, pour mettre à jour :
```bash
~/update-bot.sh
```

---

## 🎯 Avantages avec GitHub

| Méthode | Sans GitHub | Avec GitHub |
|---------|-------------|-------------|
| **Upload initial** | SCP (lent) | git clone (rapide) |
| **Mise à jour** | Re-upload tout | git pull (quelques secondes) |
| **Versioning** | ❌ | ✅ Historique complet |
| **Collaboration** | ❌ | ✅ Facile |
| **Rollback** | ❌ Difficile | ✅ git checkout |
| **Backup** | ❌ Manuel | ✅ Automatique sur GitHub |

---

## 🔐 Configuration API Keys

**IMPORTANT :** Ne mets PAS tes clés API dans GitHub !

### Option 1 : Variables d'environnement

```bash
# Sur le serveur
sudo nano /etc/systemd/system/trading-bot.service
```

Ajoute :
```ini
Environment="BINANCE_API_KEY=ta_cle"
Environment="BINANCE_API_SECRET=ton_secret"
```

Puis dans ton code Python :
```python
import os
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
```

### Option 2 : Fichier .env (pas sur GitHub)

```bash
# Sur le serveur
cd ~/trading-bot
nano .env
```

Contenu :
```
BINANCE_API_KEY=ta_cle
BINANCE_API_SECRET=ton_secret
```

Ajoute dans `.gitignore` :
```
.env
```

### Option 3 : Config local

```bash
# Sur le serveur, crée un config local (ignoré par git)
cd ~/trading-bot
cp config.yaml config.local.yaml
nano config.local.yaml  # Ajoute tes clés

# Dans .gitignore
echo "config.local.yaml" >> .gitignore
```

---

## 📊 Commandes Utiles

### Voir les logs
```bash
sudo journalctl -u trading-bot -f
```

### Status du bot
```bash
sudo systemctl status trading-bot
```

### Redémarrer
```bash
sudo systemctl restart trading-bot
```

### Mettre à jour depuis GitHub
```bash
cd ~/trading-bot && git pull && sudo systemctl restart trading-bot
```

### Tester le ML
```bash
cd ~/trading-bot
python3 test_ml_system.py
```

---

## 🆘 Dépannage

### Le bot ne démarre pas après git pull

```bash
# Vérifier les logs
sudo journalctl -u trading-bot -n 50

# Réinstaller les dépendances (si requirements.txt a changé)
cd ~/trading-bot
pip3 install -r requirements.txt --break-system-packages --force-reinstall

# Redémarrer
sudo systemctl restart trading-bot
```

### Conflit Git lors du pull

```bash
# Option 1 : Garder la version GitHub
cd ~/trading-bot
git stash
git pull
# Tes changements locaux sont mis de côté

# Option 2 : Forcer la version GitHub
git reset --hard origin/main
git pull
```

### Secrets exposés par erreur sur GitHub

**Si tu as commit tes API keys :**

1. **Change immédiatement tes clés API sur Binance**
2. Supprime-les du repo :
```bash
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config.yaml" \
  --prune-empty --tag-name-filter cat -- --all
git push origin --force --all
```

3. Ajoute config.yaml à .gitignore

---

## ✅ Checklist Finale

- [ ] Compte Oracle Cloud créé
- [ ] VM créée (Ubuntu 22.04, Ampere)
- [ ] Repo GitHub accessible
- [ ] Bot cloné sur le serveur
- [ ] Service systemd créé
- [ ] Bot démarré (`systemctl status` → active)
- [ ] Clés API configurées (PAS sur GitHub)
- [ ] ML actif (test_ml_system.py → 100%)
- [ ] Logs OK (pas d'erreurs)

---

## 🎁 Bonus : Webhook GitHub (Auto-deploy)

**Pour que le serveur se mette à jour automatiquement à chaque push :**

1. **Sur le serveur, crée un webhook listener :**

```bash
# Installe webhook
sudo apt install webhook

# Crée le script de déploiement
nano ~/deploy-bot.sh
```

Contenu de `deploy-bot.sh` :
```bash
#!/bin/bash
cd /home/ubuntu/trading-bot
git pull origin main
pip3 install -r requirements.txt --break-system-packages
sudo systemctl restart trading-bot
```

```bash
chmod +x ~/deploy-bot.sh
```

2. **Configure webhook :**

```bash
nano ~/hooks.json
```

```json
[
  {
    "id": "trading-bot-deploy",
    "execute-command": "/home/ubuntu/deploy-bot.sh",
    "command-working-directory": "/home/ubuntu",
    "response-message": "Deploying trading bot...",
    "trigger-rule": {
      "match": {
        "type": "payload-hash-sha1",
        "secret": "ton_secret_webhook",
        "parameter": {
          "source": "header",
          "name": "X-Hub-Signature"
        }
      }
    }
  }
]
```

3. **Démarre webhook :**
```bash
webhook -hooks ~/hooks.json -verbose -port 9000
```

4. **Sur GitHub :** Settings → Webhooks → Add webhook
   - URL: `http://IP_SERVEUR:9000/hooks/trading-bot-deploy`
   - Secret: ton_secret_webhook

**Maintenant à chaque push → auto-deploy ! 🚀**

---

## 🎉 Terminé !

**Avec GitHub, ton workflow devient :**

```
PC → git push → GitHub → git pull sur serveur → Restart
```

**Super simple et professionnel ! ✨**
