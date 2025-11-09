# 🌍 Oracle Cloud - Guide des Régions pour Trading Bot

## Problème: "Out of capacity" dans ta région actuelle

**Solution: Changer de région Oracle Cloud**

---

## 🎯 Régions Recommandées (par ordre)

### 1. Germany Central (Frankfurt) ✅ MEILLEUR CHOIX

**Pourquoi:**
- ✅ 3 Availability Domains (plus de capacité)
- ✅ Meilleure disponibilité A1.Flex en Europe
- ✅ Latence excellente: 20-30ms depuis France
- ✅ Data center moderne et stable

**Code région:** `eu-frankfurt-1`

---

### 2. UK South (London)

**Pourquoi:**
- ✅ 3 Availability Domains
- ✅ Bonne disponibilité
- ✅ Latence: 30-40ms depuis France

**Code région:** `uk-london-1`

---

### 3. Sweden Central (Stockholm)

**Pourquoi:**
- ✅ Nouveau data center (moins saturé)
- ✅ Bonne disponibilité
- ✅ Latence: 40-50ms depuis France

**Code région:** `eu-stockholm-1`

---

## 🔄 Comment Changer de Région

### Étape 1: Changer la Région

1. **Console Oracle Cloud** → En haut à droite, clique sur ta région actuelle
2. **Sélectionne:** Germany Central (Frankfurt)
3. La page se recharge

### Étape 2: Créer VCN dans la Nouvelle Région

**IMPORTANT:** Chaque région a son propre réseau, tu dois créer une VCN.

1. **Menu ☰** → Networking → Virtual Cloud Networks
2. **Start VCN Wizard**
3. **Create VCN with Internet Connectivity**
4. **VCN Name:** trading-bot-vcn
5. **Next** → **Create**

⏱️ Durée: 2 minutes

### Étape 3: Créer l'Instance

1. **Menu ☰** → Compute → Instances
2. **Create Instance**

**Configuration:**
```
Name: trading-bot
Image: Ubuntu 22.04
Shape: VM.Standard.E2.1.Micro (ou A1.Flex si dispo)
VCN: trading-bot-vcn (celle que tu viens de créer)
Subnet: Public Subnet
Assign public IP: YES
SSH keys: Generate new key pair → SAVE THE KEY!

Placement:
  Availability domain: (laisse le choix par défaut)
  Fault domain: NO PREFERENCE ← IMPORTANT!
```

3. **Create**

### Étape 4: Attendre la Création

⏱️ Durée: 1-2 minutes

Tu verras:
```
State: Provisioning → Running
```

✅ **Note l'IP publique!**

---

## 📊 Comparaison des Régions

| Région | AD disponibles | Latence France | Disponibilité A1 | Recommandé |
|--------|----------------|----------------|------------------|------------|
| **Frankfurt** | 3 | 20-30ms | ⭐⭐⭐⭐⭐ | ✅ OUI |
| **London** | 3 | 30-40ms | ⭐⭐⭐⭐ | ✅ OUI |
| **Stockholm** | 3 | 40-50ms | ⭐⭐⭐⭐ | ✅ OUI |
| **Amsterdam** | 1 | 20-30ms | ⭐⭐ | ⚠️ Saturé |
| **Paris** | 1 | 5-10ms | ⭐⭐ | ⚠️ Saturé |
| **Marseille** | 1 | 10-20ms | ⭐⭐ | ⚠️ Saturé |

---

## ⚠️ Pièges à Éviter

### Piège 1: Oublier de Créer une VCN dans la Nouvelle Région

**Erreur:**
```
Error: No subnets available in compartment
```

**Solution:**
- Crée d'abord la VCN (Étape 2 ci-dessus)

### Piège 2: Spécifier un Fault Domain

**Erreur:**
```
Out of capacity for shape ... in fault domain FAULT-DOMAIN-1
```

**Solution:**
- Laisse "Fault domain" sur "No preference"

### Piège 3: Utiliser les Anciennes Clés SSH

**Important:**
- Génère de **nouvelles clés SSH** pour chaque région
- Sauvegarde-les bien!

---

## 🎁 Bonus: Script de Test Multi-Régions

Si tu veux tester plusieurs régions automatiquement:

```bash
#!/bin/bash

REGIONS=("eu-frankfurt-1" "uk-london-1" "eu-stockholm-1")

for region in "${REGIONS[@]}"; do
    echo "Testing $region..."

    # Test E2.1.Micro availability
    oci compute shape list \
        --region "$region" \
        --compartment-id "$COMPARTMENT_ID" \
        | grep "VM.Standard.E2.1.Micro"

    echo "---"
done
```

---

## 🆘 Si Aucune Région ne Fonctionne

Cela signifie que ton compte Oracle n'est pas complètement activé:

### Vérifications:

1. **Menu ☰** → **Governance** → **Tenancy Details**
2. **Status:** Doit être "Active"
3. **Email:** Doit être vérifié
4. **Payment method:** Doit être valide

### Si le Compte est Récent (< 30 jours):

Oracle peut limiter les nouvelles inscriptions pour prévenir les abus.

**Solutions:**
1. Attends 24-48h que ton compte soit complètement validé
2. Contacte le support Oracle (chat en ligne disponible)
3. Utilise les crédits gratuits ($300) pour créer une instance **payante** temporairement

### Créer Instance Payante Temporaire (Gratuite avec Crédits)

Si vraiment bloqué:

1. **Shape:** VM.Standard.E3.Flex (toujours disponible)
2. **OCPU:** 1
3. **Memory:** 1 GB
4. **Cost:** ~$5/mois (payé avec les $300 de crédits gratuits)

Tu auras 60 mois gratuits avec tes crédits!

---

## ✅ Checklist Changement de Région

- [ ] Choisir nouvelle région (Frankfurt recommandé)
- [ ] Créer VCN dans la nouvelle région
- [ ] Générer nouvelles clés SSH
- [ ] Créer instance (E2.1.Micro ou A1.Flex)
- [ ] Fault domain: "No preference"
- [ ] Noter la nouvelle IP publique
- [ ] Sauvegarder les nouvelles clés SSH
- [ ] Tester connexion SSH
- [ ] Déployer le bot

---

## 🚀 Après le Changement de Région

Une fois l'instance créée, le déploiement est identique:

```bash
# Se connecter
ssh -i nouvelle_cle.key ubuntu@NOUVELLE_IP

# Cloner le repo
git clone https://github.com/TON_USERNAME/trading-bot.git
cd trading-bot

# Installer
chmod +x setup_oracle_cloud.sh
./setup_oracle_cloud.sh
```

**La région n'affecte PAS les performances de trading:**
- Latence Binance API: Négligeable (<50ms de différence)
- Le bot fonctionne identiquement dans toutes les régions

---

## 📞 Support

Si bloqué après avoir essayé Frankfurt:

1. **Oracle Cloud Chat Support:**
   - Console → Help (?) → Chat
   - Dis: "Cannot create any instance, all shapes out of capacity"

2. **Oracle Forums:**
   - https://community.oracle.com/

Ils peuvent débloquer manuellement ton compte ou t'indiquer les régions disponibles.

---

**Commence avec Frankfurt maintenant - ça devrait fonctionner! 🎯**
