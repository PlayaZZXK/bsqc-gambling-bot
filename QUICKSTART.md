# 🚀 GUIDE DE DÉMARRAGE RAPIDE

## ⚡ Installation en 5 minutes

### Étape 1: Installe Python
- Télécharge Python 3.8+ sur https://www.python.org/
- ✅ Coche "Add Python to PATH" pendant l'installation

### Étape 2: Crée ton Bot Discord
1. Va sur https://discord.com/developers/applications
2. Clique "New Application"
3. Donne un nom (ex: "Skull Casino")
4. Va dans "Bot" → "Add Bot"
5. **Active ces 3 intents (important!):**
   - ✅ Presence Intent
   - ✅ Server Members Intent  
   - ✅ Message Content Intent
6. Clique "Reset Token" et **COPIE TON TOKEN**

### Étape 3: Configure le bot
1. Ouvre `bot.py` dans un éditeur de texte
2. Trouve cette ligne tout en bas:
   ```python
   await bot.start('TON_TOKEN_ICI')
   ```
3. Remplace `TON_TOKEN_ICI` par ton token (garde les guillemets!)
4. Sauvegarde le fichier

### Étape 4: Installe les dépendances
Ouvre un terminal dans le dossier du bot et tape:
```bash
pip install -r requirements.txt
```

### Étape 5: Lance le bot!
```bash
python start.py
```
Ou directement:
```bash
python bot.py
```

### Étape 6: Invite le bot sur ton serveur
Remplace `CLIENT_ID` par ton Application ID (dans Developer Portal):
```
https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=8&scope=bot
```

## 🎮 PREMIÈRES COMMANDES

Une fois le bot en ligne:

```
!balance          # Voir ton solde (tu commences à 0)
!daily            # Récupérer tes 100 Skulls quotidiens
!coinflip heads 50   # Jouer au coinflip
!slots 100        # Jouer aux slots
!help             # Voir toutes les commandes
```

## ⚠️ PROBLÈMES COURANTS

### "Module discord not found"
→ Installe discord.py: `pip install discord.py`

### "Improper token"  
→ Vérifie que ton token est correct dans bot.py

### Les commandes ne marchent pas
→ Vérifie que les 3 intents sont activés dans Developer Portal

### Le bot se déconnecte
→ Normal si tu quittes le serveur (sécurité owner)

## 📱 COMMANDES PRINCIPALES

### 💰 Économie
- `!daily` - 100 Skulls/jour
- `!balance` - Voir ton solde  
- `!gift @user 100` - Donner des Skulls
- `!stats` - Tes statistiques

### 🎰 Jeux
- `!coinflip heads 100` - Pile ou face
- `!dice over 50` - Lancer de dés
- `!slots 100` - Machine à sous
- `!blackjack 200` - Blackjack
- `!roulette red 150` - Roulette
- `!crash 100` - Crash game
- `!mines 100` - Démineur
- `!duel @user 500` - Duel PvP

### 🏆 Classements
- `!leaderboard` - Top 10 richesse
- `!gamblingtop` - Top 10 gamblers
- `!rank` - Ton classement

### 🎲 Paris
- `!createbet` - Créer un pari (Admin)
- `!activebets` - Voir les paris actifs
- `!placebet <id> <option> <montant>` - Parier

## 🎯 CONSEILS

1. **Commence par le daily** pour avoir des Skulls
2. **Joue prudemment** - ne mise pas tout!
3. **Consulte !stats** pour suivre tes progrès
4. **Crée des paris** pour animer la communauté
5. **Défie tes amis** en duel!

## 📞 BESOIN D'AIDE?

Lis le `README.md` complet pour plus de détails!

**Bon gambling! 💀🎰**
