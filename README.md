# 💀 Discord Gambling Bot - SKULL CASINO 🎰

Bot Discord de gambling complet avec 14 jeux différents et un système d'économie avancé!

## 🎮 JEUX DISPONIBLES (14 au total)

### Jeux Classiques
1. **Coinflip** (`!coinflip`) - Pile ou face classique (×2)
2. **Dice** (`!dice`) - Lancer de dés avec prédictions (×2 ou ×6)
3. **Slots** (`!slots`) - Machine à sous avec jackpot (×10 max)
4. **Blackjack** (`!blackjack`) - Jeu de cartes interactif (×2 ou ×2.5)
5. **Roulette** (`!roulette`) - Rouge/Noir/Numéro (×2 ou ×36)

### Jeux Modernes
6. **Crash** (`!crash`) - Multiplicateur qui monte, cash out avant le crash!
7. **Mines** (`!mines`) - Démineur avec paris progressifs
8. **Plinko** (`!plinko`) - Balle qui tombe (×0.2 à ×10)
9. **Wheel** (`!wheel`) - Roue de la fortune (×2 à ×50)
10. **Cups** (`!cups`) - Jeu des gobelets (×2)

### Jeux PvP & Spéciaux
11. **Higher/Lower** (`!hl`) - Carte plus haute ou basse (×2)
12. **RPS** (`!rps`) - Pierre Papier Ciseaux (×2)
13. **Lottery** (`!lottery`) - Loterie communautaire du serveur
14. **Coinflip Duel** (`!duel`) - Défi PvP, gagnant prend tout!

## 💰 SYSTÈME D'ÉCONOMIE

### Monnaie: **Skulls** 💀
- Commande `!daily` - 100 Skulls/jour + bonus streak
- Commande `!gift` - Donner des Skulls à d'autres joueurs
- Sauvegarde automatique toutes les 5 minutes
- Backup quotidien de sécurité

### Statistiques Complètes
- Balance totale
- Profits de gambling (sans daily/gifts)
- Total misé
- Parties jouées / Victoires / Défaites
- Ratio gains/pertes
- Système de niveaux avec XP

## 📊 COMMANDES

### 💵 Économie
- `!balance` / `!bal` - Voir ton solde
- `!daily` - Réclamer tes Skulls quotidiens (cooldown 24h)
- `!gift <@user> <montant>` - Donner des Skulls
- `!stats` / `!profile` - Voir tes statistiques complètes
- `!rank` - Voir ton classement dans le serveur

### 🏆 Classements
- `!leaderboard` / `!lb` - Top 10 des plus riches
- `!gamblingtop` / `!gtop` - Top 10 meilleurs gamblers (profits nets)

### 🎲 Système de Paris Communautaires
- `!createbet` - Créer un pari (Admin seulement)
  - Titre personnalisé
  - Multiple options (2-10)
  - Côtes personnalisées pour chaque option
- `!placebet <id> <option> <montant>` - Parier
- `!viewbet <id>` - Voir les détails d'un pari
- `!activebets` - Voir tous les paris actifs
- `!closebet <id> <option gagnante>` - Fermer et distribuer (Admin)

### ⚙️ Administration (Owner seulement)
- `!reload <module>` - Recharger un module
- `!save` - Sauvegarder manuellement la DB

## 🔒 SÉCURITÉ

Le bot quitte automatiquement un serveur si l'owner (User ID: 1270241225861234690) n'est pas présent!

## 📁 STRUCTURE DU PROJET

```
discord_gambling_bot/
│
├── bot.py                      # Fichier principal
│
├── commands/
│   ├── economy.py              # Daily, balance, gift
│   ├── leaderboard.py          # Classements
│   ├── betting.py              # Système de paris
│   └── stats.py                # Statistiques personnelles
│
├── games/
│   ├── coinflip.py
│   ├── dice.py
│   ├── slots.py
│   ├── blackjack.py
│   ├── roulette.py
│   ├── crash.py
│   ├── mines.py
│   ├── plinko.py
│   ├── wheel.py
│   ├── cups.py
│   ├── higherlower.py
│   ├── rps.py
│   ├── lottery.py
│   └── coinflip_pvp.py
│
├── data/
│   ├── economy.json            # Base de données principale
│   └── backup_YYYYMMDD.json   # Backups quotidiens
│
└── requirements.txt
```

## 🚀 INSTALLATION

### 1. Prérequis
- Python 3.8 ou supérieur
- Un bot Discord (créé sur Discord Developer Portal)

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration

Ouvre `bot.py` et remplace:
```python
await bot.start('TON_TOKEN_ICI')
```

Par ton token Discord bot.

### 4. Lancer le bot

```bash
python bot.py
```

## 🎯 OBTENIR UN TOKEN DISCORD

1. Va sur https://discord.com/developers/applications
2. Clique "New Application"
3. Donne un nom à ton bot
4. Va dans "Bot" dans le menu de gauche
5. Clique "Add Bot"
6. Active ces intents:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
7. Clique "Reset Token" et copie ton token
8. **NE PARTAGE JAMAIS TON TOKEN!**

## 📝 INVITER LE BOT

Lien d'invitation (remplace CLIENT_ID par ton Application ID):
```
https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=8&scope=bot
```

Permissions nécessaires:
- Send Messages
- Embed Links
- Add Reactions
- Read Message History
- Use External Emojis

## ⚡ FONCTIONNALITÉS AVANCÉES

### Système de Niveaux
- Gagne de l'XP en jouant
- Plus tu joues, plus tu montes de niveau
- 100 XP = 1 niveau

### Cooldowns
- Chaque jeu a un cooldown (3-10s)
- Daily: 24h
- Gift: 60s
- Duel: 30s

### Sauvegarde
- Auto-save toutes les 5 minutes
- Backup quotidien automatique
- Commande manuelle `!save` pour l'owner

### Système de Paris
- Crée des paris personnalisés
- Côtes libres par option
- Suivi en temps réel
- Distribution automatique des gains

## 🎨 PERSONNALISATION

### Modifier la monnaie
Dans `bot.py`:
```python
CURRENCY_NAME = "Skull"
CURRENCY_EMOJI = "💀"
```

### Modifier le reward daily
Dans `commands/economy.py`:
```python
base_reward = 100  # Modifier ici
```

### Modifier les cooldowns
Dans chaque fichier de jeu:
```python
@commands.cooldown(1, 3, commands.BucketType.user)  # 1 fois toutes les 3 secondes
```

## 🐛 DÉPANNAGE

### Le bot ne se connecte pas
- Vérifie que ton token est correct
- Vérifie que les intents sont activés

### Les commandes ne fonctionnent pas
- Vérifie que le préfixe est `!`
- Vérifie que le bot a les permissions nécessaires

### Erreur de module
```bash
python -m pip install --upgrade discord.py
```

## 📞 SUPPORT

Pour toute question ou bug, vérifie:
1. Les logs du bot dans la console
2. Les permissions du bot sur le serveur
3. Que tous les modules sont bien chargés

## ⚠️ NOTES IMPORTANTES

1. **Sécurité**: Ne partage JAMAIS ton token!
2. **Backups**: Les backups sont dans `data/backup_YYYYMMDD.json`
3. **Owner Protection**: Le bot quitte si tu quittes le serveur
4. **Données**: Tout est sauvegardé en JSON local

## 🎉 PROFITE BIEN!

Ton bot de gambling est prêt! Lance `!help` dans Discord pour voir toutes les commandes!

**Bon gambling et que les Skulls soient avec toi!** 💀🎰
