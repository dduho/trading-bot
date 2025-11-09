# Configuration FileZilla pour Google Cloud VM

## ✅ Résumé du Bot

Le bot de trading est **en cours d'exécution** sur la VM Google Cloud:
- **PID**: 44514
- **Uptime**: ~20 minutes
- **Mode**: PAPER (simulation)
- **Statut**: Actif, analyse 5 cryptos toutes les 15 secondes
- **Trades**: 0 nouveaux (200 trades de test générés)
- **Performance**: 55% win rate, +9,311 USDT (données de test)

## 📁 Configuration FileZilla SFTP

### Prérequis
Vos informations de connexion (depuis votre fichier SSH config):
- **IP VM**: `35.241.174.165`
- **Utilisateur**: `duhodavid12` (pour les fichiers du projet)
- **Clé privée**: `C:\Users\black\.ssh\google_compute_engine`
- **Port**: 22

### Étapes de Configuration

#### 1. Ajouter la clé SSH dans FileZilla
1. Ouvrez FileZilla
2. Allez dans **Édition** > **Paramètres**
3. Dans la barre latérale, cliquez sur **SFTP**
4. Cliquez sur **Ajouter un fichier de clé...**
5. Naviguez vers: `C:\Users\black\.ssh\google_compute_engine`
6. Sélectionnez le fichier (FileZilla le convertira automatiquement si nécessaire)
7. Cliquez sur **OK**

#### 2. Créer une connexion dans le Gestionnaire de sites
1. Allez dans **Fichier** > **Gestionnaire de sites**
2. Cliquez sur **Nouveau site** (en bas à gauche)
3. Nommez-le: `Trading Bot - Google Cloud`
4. Configurez comme suit:

```
Protocole: SFTP - SSH File Transfer Protocol
Hôte: 35.241.174.165
Port: 22
Type d'authentification: Fichier de clé
Utilisateur: duhodavid12
Fichier de clé: C:\Users\black\.ssh\google_compute_engine
```

5. Cliquez sur **Connexion**

#### 3. Navigation
Après connexion, vous arriverez dans `/home/duhodavid12/`

Le projet se trouve dans: `/home/duhodavid12/trading-bot/`

### Structure des Dossiers Importants

```
/home/duhodavid12/trading-bot/
├── src/                    # Code source du bot
├── data/                   # Base de données SQLite
│   └── trading_history.db
├── models/                 # Modèles ML entraînés
├── logs/                   # Logs (si le dossier existe)
├── trading_bot.log         # Log principal (106 KB)
├── config.yaml             # Configuration
├── .env                    # Variables d'environnement (API keys)
├── bot_status.py           # Script de statut
└── populate_test_data.py   # Script de génération de données

```

### Fichiers Clés à Consulter

1. **trading_bot.log** (106 KB)
   - Log en temps réel du bot
   - Montre toutes les itérations et signaux

2. **data/trading_history.db** (base SQLite)
   - Contient 200 trades de test
   - Conditions de marché
   - Performance du modèle ML

3. **config.yaml**
   - Configuration du bot
   - Stratégie, risk management
   - Symboles surveillés

4. **.env**
   - Clés API Binance
   - ⚠️ Ne jamais télécharger ou partager ce fichier

### Commandes Utiles via SSH

Pour vérifier le statut du bot:
```bash
cd /home/duhodavid12/trading-bot
python3 bot_status.py
```

Pour voir les logs en temps réel:
```bash
tail -f trading_bot.log
```

Pour arrêter le bot:
```bash
pkill -f trading_bot.py
```

Pour redémarrer le bot:
```bash
cd /home/duhodavid12/trading-bot
nohup python3 src/trading_bot.py &
```

## 🔒 Sécurité

- Ne jamais télécharger le fichier `.env` sur votre PC local
- La clé SSH `google_compute_engine` est privée - ne la partagez jamais
- Le bot tourne en mode PAPER (simulation) - pas d'argent réel
- Pour passer en mode LIVE, modifiez `.env`: `TRADING_MODE=live`

## 📊 Surveillance

Pour surveiller l'activité du bot:

1. **Logs FileZilla**: Téléchargez `trading_bot.log` périodiquement
2. **Script de statut**: Exécutez `bot_status.py` via SSH
3. **Base de données**: Téléchargez `data/trading_history.db` pour analyse locale avec DB Browser for SQLite

## ✅ Tout est Configuré

✓ Bot en cours d'exécution  
✓ Base de données avec 200 trades de test  
✓ Modèle ML chargé (68% accuracy)  
✓ Système ML opérationnel à 100%  
✓ Synchronisation Git active  
✓ FileZilla prêt à être configuré  

Vous pouvez maintenant vous connecter via FileZilla et explorer les fichiers!
