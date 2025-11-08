# Guide Complet : Héberger ton Bot sur Oracle Cloud (GRATUIT À VIE)

**Durée totale : ~30 minutes**
**Coût : 0€ pour toujours**

---

## 📋 Ce dont tu as besoin

- ✅ Une adresse email
- ✅ Une carte bancaire (pour vérification, PAS débitée)
- ✅ Ton code du bot (ce dossier trading-bot)
- ✅ 30 minutes de temps

---

## 🚀 PARTIE A : Créer le Compte Oracle Cloud

### Étape 1 : Inscription (10 min)

1. **Va sur Oracle Cloud Free Tier**
   ```
   https://www.oracle.com/cloud/free/
   ```

2. **Clique sur "Start for Free"** (bouton rouge)

3. **Remplis le formulaire :**
   - **Email :** Ton email principal
   - **Country :** France
   - **First Name / Last Name :** Ton nom
   - **Company Name :** Peut être fictif (ex: "Trading Bot Lab")

4. **Choisis ta région (IMPORTANT) :**
   - **Recommandé :** France (Paris) si disponible
   - **Alternative :** Germany (Frankfurt)
   - **Alternative 2 :** Netherlands (Amsterdam)

   ⚠️ **Tu ne pourras PAS changer de région après !**

5. **Vérifie ton email**
   - Tu recevras un email de confirmation
   - Clique sur le lien de vérification

6. **Configure ton mot de passe**
   - Choisis un mot de passe fort
   - Note-le bien !

7. **Ajoute ta carte bancaire**
   - ⚠️ **AUCUN débit ne sera fait**
   - C'est juste pour vérifier ton identité
   - Oracle ne facture RIEN pour le Free Tier

8. **Attends la validation du compte**
   - Peut prendre 5-30 minutes
   - Tu recevras un email quand c'est prêt

---

### Étape 2 : Première Connexion

1. **Va sur** https://cloud.oracle.com

2. **Connexion :**
   - **Cloud Account Name :** (indiqué dans ton email)
   - **Username :** Ton email
   - **Password :** Ton mot de passe

3. **Tu arrives sur le Dashboard Oracle Cloud** 🎉

---

## 💻 PARTIE B : Créer ta Machine Virtuelle

### Étape 3 : Créer une Instance (VM)

1. **Dans le menu hamburger (☰) en haut à gauche**
   ```
   Compute → Instances
   ```

2. **Clique sur "Create Instance"**

3. **Configuration de l'Instance :**

   **a) Name :**
   ```
   trading-bot-server
   ```

   **b) Compartment :**
   ```
   Laisse par défaut (root)
   ```

   **c) Placement :**
   ```
   Availability Domain : Laisse par défaut
   ```

   **d) Image and Shape :**

   **Image :**
   - Clique sur "Change Image"
   - Choisis **"Ubuntu"**
   - Version : **22.04** (Minimal)
   - Clique "Select Image"

   **Shape :**
   - Clique sur "Change Shape"
   - Choisis **"Ampere"** (ARM - GRATUIT)
   - Shape : **VM.Standard.A1.Flex**
   - OCPU : **2** (tu peux mettre jusqu'à 4)
   - Memory : **12 GB** (tu peux mettre jusqu'à 24 GB)
   - ✅ Vérifie que "Always Free Eligible" est bien affiché
   - Clique "Select Shape"

   **e) Networking :**
   - Laisse tout par défaut
   - ✅ Assure-toi que "Assign a public IPv4 address" est coché

   **f) Add SSH Keys :**

   **Option 1 - Générer automatiquement (RECOMMANDÉ) :**
   - Coche "Generate a key pair for me"
   - Clique "Save Private Key" → Sauvegarde le fichier `.key`
   - Clique "Save Public Key" → Sauvegarde aussi
   - **⚠️ IMPORTANT : Ne perds PAS ce fichier .key !**

   **Option 2 - Si tu as déjà une clé SSH :**
   - Coche "Upload public key files"
   - Upload ta clé publique (.pub)

   **g) Boot Volume :**
   - Laisse par défaut (50 GB suffit largement)

4. **Clique sur "Create"**

5. **Attends 2-3 minutes**
   - Status : Provisioning → Running (orange → vert)
   - Note l'**adresse IP publique** (ex: 158.101.123.45)

---

### Étape 4 : Configurer le Firewall

Oracle Cloud a un firewall strict par défaut. Il faut ouvrir les ports :

1. **Sur la page de ton instance, dans "Instance Details"**

2. **Scroll jusqu'à "Primary VNIC"**
   - Clique sur le nom du subnet (ex: subnet-20231108...)

3. **Clique sur le Security List (Default Security List...)**

4. **Clique sur "Add Ingress Rules"**

5. **Ajoute cette règle (pour SSH si pas déjà là) :**
   ```
   Source CIDR: 0.0.0.0/0
   IP Protocol: TCP
   Source Port Range: All
   Destination Port Range: 22
   Description: SSH Access
   ```

6. **Clique "Add Ingress Rules"**

---

### Étape 5 : Se Connecter à ta VM

#### Sur Windows (PowerShell) :

```powershell
# Va dans le dossier où tu as sauvegardé la clé
cd C:\Users\TON_NOM\Downloads

# Change les permissions de la clé (si nécessaire)
icacls ssh-key-2023-11-08.key /inheritance:r
icacls ssh-key-2023-11-08.key /grant:r "%USERNAME%:R"

# Connecte-toi (remplace IP_PUBLIQUE par ton IP)
ssh -i ssh-key-2023-11-08.key ubuntu@IP_PUBLIQUE
```

#### Exemple :
```powershell
ssh -i ssh-key-2023-11-08.key ubuntu@158.101.123.45
```

**Si ça demande "Are you sure you want to continue connecting?" → tape `yes`**

🎉 **Tu es maintenant connecté à ton serveur Ubuntu dans le cloud !**

---

## ⚙️ PARTIE C : Installation Automatique du Bot

### Étape 6 : Script d'Installation Automatique

Une fois connecté à ta VM, copie-colle ce script complet :

```bash
# Script d'installation automatique du Trading Bot
# À exécuter sur Oracle Cloud Ubuntu

echo "=================================================="
echo "  INSTALLATION TRADING BOT - Oracle Cloud"
echo "=================================================="
echo ""

# 1. Mise à jour du système
echo "[1/7] Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# 2. Installation Python et dépendances
echo "[2/7] Installation Python 3.11..."
sudo apt install -y python3-pip python3-venv git curl wget nano htop screen

# 3. Configuration du firewall local
echo "[3/7] Configuration firewall..."
sudo iptables -I INPUT -p tcp --dport 22 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || true

# 4. Créer le dossier de travail
echo "[4/7] Création dossier de travail..."
cd ~
mkdir -p trading-bot
cd trading-bot

# 5. Message pour l'utilisateur
echo "[5/7] Prêt à recevoir les fichiers du bot"
echo ""
echo "=================================================="
echo "  ÉTAPE SUIVANTE (depuis ton PC Windows) :"
echo "=================================================="
echo ""
echo "Sur ton PC, ouvre PowerShell dans le dossier trading-bot et exécute :"
echo ""
echo "scp -i \"CHEMIN_VERS_TA_CLE.key\" -r * ubuntu@$(curl -s ifconfig.me):~/trading-bot/"
echo ""
echo "Exemple :"
echo "scp -i \"C:\\Users\\TON_NOM\\Downloads\\ssh-key.key\" -r * ubuntu@$(curl -s ifconfig.me):~/trading-bot/"
echo ""
echo "Puis reviens ici et appuie sur ENTRÉE pour continuer..."
read -p ""

# 6. Installation des requirements Python
echo "[6/7] Installation dépendances Python..."
cd ~/trading-bot
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt --break-system-packages
    echo "✓ Requirements installés"
else
    echo "⚠ requirements.txt non trouvé - installation manuelle nécessaire"
    pip3 install ccxt pandas numpy ta-lib python-binance pyyaml scikit-learn --break-system-packages
fi

# 7. Configuration TA-Lib (si nécessaire)
echo "[7/7] Vérification TA-Lib..."
sudo apt install -y libta-lib0-dev
pip3 install --upgrade ta-lib --break-system-packages

echo ""
echo "=================================================="
echo "  INSTALLATION TERMINÉE !"
echo "=================================================="
echo ""
echo "Prochaine étape : Configurer le service systemd"
echo "Tape 'exit' puis relance ce script pour la suite"
```

### Étape 7 : Transférer tes Fichiers

**Sur ton PC Windows**, ouvre PowerShell dans le dossier `trading-bot` :

```powershell
# Remplace les chemins par les tiens
scp -i "C:\Users\TON_NOM\Downloads\ssh-key-2023-11-08.key" -r * ubuntu@IP_PUBLIQUE:~/trading-bot/
```

**Exemple complet :**
```powershell
cd "C:\Users\black\OneDrive\Documents\Web Projects\trading-bot"
scp -i "C:\Users\black\Downloads\ssh-key-2023-11-08.key" -r * ubuntu@158.101.123.45:~/trading-bot/
```

⏳ **Attends que tous les fichiers soient transférés (peut prendre 1-2 min)**

---

### Étape 8 : Configurer le Service Systemd

Retourne sur ta VM (SSH) et crée le service :

```bash
# Créer le fichier service
sudo nano /etc/systemd/system/trading-bot.service
```

**Copie-colle ce contenu :**

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

**Sauvegarde :**
- `Ctrl + O` (pour sauvegarder)
- `Entrée` (confirmer)
- `Ctrl + X` (pour quitter)

**Active le service :**

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer le service au démarrage
sudo systemctl enable trading-bot

# Démarrer le service
sudo systemctl start trading-bot

# Vérifier le statut
sudo systemctl status trading-bot
```

**Tu devrais voir :**
```
● trading-bot.service - Trading Bot with Machine Learning
   Loaded: loaded
   Active: active (running)
```

---

## 📊 Commandes Utiles

### Voir les Logs du Bot

```bash
# Logs en temps réel
sudo journalctl -u trading-bot -f

# Dernières 100 lignes
sudo journalctl -u trading-bot -n 100

# Logs d'aujourd'hui
sudo journalctl -u trading-bot --since today
```

### Gérer le Bot

```bash
# Arrêter le bot
sudo systemctl stop trading-bot

# Redémarrer le bot
sudo systemctl restart trading-bot

# Voir le statut
sudo systemctl status trading-bot

# Désactiver le démarrage automatique
sudo systemctl disable trading-bot
```

### Mettre à Jour le Bot

**Sur ton PC (PowerShell) :**
```powershell
# Transférer les nouveaux fichiers
scp -i "CHEMIN_CLE.key" -r * ubuntu@IP:~/trading-bot/
```

**Sur le serveur (SSH) :**
```bash
# Redémarrer pour appliquer les changements
sudo systemctl restart trading-bot
```

### Vérifier les Performances

```bash
# CPU et RAM
htop

# Espace disque
df -h

# Processus Python
ps aux | grep python
```

---

## 🔍 Vérifications Importantes

### 1. Le Bot Tourne-t-il ?

```bash
sudo systemctl status trading-bot
# Devrait afficher "Active: active (running)"
```

### 2. Les Logs Sont-ils OK ?

```bash
sudo journalctl -u trading-bot -n 50
# Regarde s'il y a des erreurs
```

### 3. Le ML Fonctionne-t-il ?

```bash
cd ~/trading-bot
python3 test_ml_system.py
# Devrait afficher "100% PASS"
```

### 4. La Base de Données se Remplit-elle ?

```bash
cd ~/trading-bot
ls -lh data/
# Tu devrais voir trading_history.db
```

---

## 🎯 Configuration Finale

### Configurer les Credentials Binance

```bash
cd ~/trading-bot
nano config.yaml
```

Ajoute tes clés API Binance si nécessaire, puis :

```bash
sudo systemctl restart trading-bot
```

---

## 🆘 Dépannage

### Le bot ne démarre pas

```bash
# Voir l'erreur exacte
sudo journalctl -u trading-bot -n 50 --no-pager

# Tester manuellement
cd ~/trading-bot
python3 src/trading_bot.py
```

### Problème de dépendances Python

```bash
pip3 install -r requirements.txt --break-system-packages --force-reinstall
```

### VM ne répond plus

1. Va sur Oracle Cloud Console
2. Instances → ta VM
3. More Actions → Reboot

### SSH ne fonctionne pas

Vérifie :
- Le Security List a bien la règle SSH (port 22)
- Ta clé SSH est la bonne
- L'IP publique n'a pas changé

---

## 📈 Monitoring du ML

### Vérifier les Cycles ML

```bash
# Voir quand le dernier cycle ML a eu lieu
cd ~/trading-bot
python3 -c "
import sys
sys.path.append('src')
from trade_database import TradeDatabase
db = TradeDatabase()
cursor = db.conn.cursor()
cursor.execute('SELECT timestamp FROM learning_events ORDER BY timestamp DESC LIMIT 1')
result = cursor.fetchone()
print(f'Dernier cycle ML: {result[0] if result else \"Jamais\"}')
"
```

### Tester le ML

```bash
cd ~/trading-bot
python3 test_ml_system.py
```

---

## 💡 Conseils

### 1. Sauvegarde Régulière

Tous les weekends, sauvegarde ta base de données :

```bash
# Sur le serveur
cd ~/trading-bot
tar -czf backup-$(date +%Y%m%d).tar.gz data/ models/

# Télécharger sur ton PC (depuis PowerShell)
scp -i "CHEMIN_CLE.key" ubuntu@IP:~/trading-bot/backup-*.tar.gz C:\Backups\
```

### 2. Surveillance

Configure un petit script pour vérifier que le bot tourne :

```bash
# Créer un script de monitoring
nano ~/check-bot.sh
```

Contenu :
```bash
#!/bin/bash
if ! systemctl is-active --quiet trading-bot; then
    echo "Bot arrêté ! Redémarrage..."
    sudo systemctl start trading-bot
fi
```

```bash
chmod +x ~/check-bot.sh

# Ajouter à crontab (toutes les 5 min)
crontab -e
# Ajoute cette ligne :
*/5 * * * * /home/ubuntu/check-bot.sh
```

### 3. Mises à Jour de Sécurité

Tous les mois :

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

---

## 🎉 C'est Terminé !

Ton bot tourne maintenant 24/7 gratuitement sur Oracle Cloud !

**Ce qui se passe maintenant :**
- ✅ Bot actif 24/7
- ✅ ML s'exécute toutes les 12h
- ✅ Auto-optimisation active
- ✅ Données sauvegardées en permanence
- ✅ 100% gratuit pour toujours

**Accès à distance :**
```bash
ssh -i "CHEMIN_CLE.key" ubuntu@IP_PUBLIQUE
```

**Voir les logs :**
```bash
sudo journalctl -u trading-bot -f
```

---

## 📞 Support

Si tu as des problèmes, vérifie :
1. Les logs : `sudo journalctl -u trading-bot -n 100`
2. Le status : `sudo systemctl status trading-bot`
3. La connexion : `ping IP_PUBLIQUE`

Bon trading ! 🚀
