# 📁 STRUCTURE DU PROJET

```
discord_gambling_bot/
│
├── 📄 bot.py                          # Fichier principal du bot
├── 📄 start.py                        # Script de démarrage facile
├── 📄 requirements.txt                # Dépendances Python
├── 📄 config_example.py               # Configuration exemple
├── 📄 .gitignore                      # Fichiers à ignorer sur Git
│
├── 📚 README.md                       # Documentation complète
├── 📚 QUICKSTART.md                   # Guide de démarrage rapide
├── 📚 COMMANDS.md                     # Liste de toutes les commandes
├── 📚 STRUCTURE.md                    # Ce fichier
│
├── 📂 commands/                       # Commandes principales
│   ├── economy.py                     # Daily, balance, gift
│   ├── leaderboard.py                 # Classements top 10
│   ├── betting.py                     # Système de paris
│   ├── stats.py                       # Statistiques personnelles
│   └── help_command.py                # Commande d'aide personnalisée
│
├── 📂 games/                          # Tous les jeux (14)
│   ├── coinflip.py                    # 🪙 Pile ou face (×2)
│   ├── dice.py                        # 🎲 Lancer de dés (×2/×6)
│   ├── slots.py                       # 🎰 Machine à sous (×10 max)
│   ├── blackjack.py                   # ♠️ Blackjack interactif (×2)
│   ├── roulette.py                    # 🎡 Roulette (×2/×36)
│   ├── crash.py                       # 🚀 Crash game
│   ├── mines.py                       # 💣 Démineur
│   ├── plinko.py                      # 🎯 Plinko (×10 max)
│   ├── wheel.py                       # 🎡 Roue de la fortune (×50 max)
│   ├── cups.py                        # 🥤 Jeu des gobelets (×2)
│   ├── higherlower.py                 # 🎴 Higher/Lower (×2)
│   ├── rps.py                         # ✊ Pierre-Papier-Ciseaux (×2)
│   ├── lottery.py                     # 🎫 Loterie du serveur
│   └── coinflip_pvp.py                # ⚔️ Duel coinflip
│
└── 📂 data/                           # Base de données (créé auto)
    ├── economy.json                   # Données principales
    └── backup_YYYYMMDD.json          # Backups quotidiens
```

## 📊 DÉTAILS DES FICHIERS

### Fichiers Principaux
- **bot.py** (150 lignes)
  - Configuration du bot
  - Système de sécurité owner
  - Chargement des modules
  - Sauvegarde automatique
  - Gestion des erreurs

- **start.py** (75 lignes)
  - Script de lancement interactif
  - Vérification des dépendances
  - Création des dossiers

### Modules de Commandes
- **economy.py** (~150 lignes)
  - `!balance` - Voir le solde
  - `!daily` - Réclamer 100 Skulls/jour
  - `!gift` - Donner des Skulls

- **leaderboard.py** (~100 lignes)
  - `!leaderboard` - Top 10 richesse
  - `!gamblingtop` - Top 10 gamblers

- **betting.py** (~250 lignes)
  - Système de paris communautaires
  - Côtes personnalisables
  - Multiple options
  - Distribution automatique

- **stats.py** (~120 lignes)
  - Statistiques détaillées
  - Ratios gains/pertes
  - Classement personnel

- **help_command.py** (~200 lignes)
  - Menu d'aide interactif
  - Catégories détaillées
  - Exemples d'utilisation

### Jeux

#### Simples (50-80 lignes chacun)
- coinflip.py
- dice.py
- rps.py
- cups.py
- higherlower.py
- plinko.py
- wheel.py

#### Moyens (80-150 lignes chacun)
- slots.py
- roulette.py
- crash.py (avec bouton interactif)
- lottery.py
- coinflip_pvp.py

#### Complexes (150-250 lignes chacun)
- blackjack.py (avec UI interactive)
- mines.py (grille de boutons)

## 📦 TAILLE DU PROJET

```
Total fichiers Python: 20 fichiers
Total lignes de code: ~3500 lignes
Total fichiers doc: 4 fichiers
Taille totale: ~500 KB
```

## 🔄 FLUX D'EXÉCUTION

```
1. Lancement (bot.py)
   ↓
2. Chargement config & intents
   ↓
3. Connexion à Discord
   ↓
4. Vérification owner dans serveurs
   ↓
5. Chargement des 19 modules (commands + games)
   ↓
6. Démarrage auto-save (5 min)
   ↓
7. Bot prêt! ✅
```

## 💾 SYSTÈME DE DONNÉES

### economy.json structure:
```json
{
  "guild_id": {
    "user_id": {
      "balance": 1000,
      "total_earned": 2000,
      "gambling_profit": 500,
      "total_wagered": 5000,
      "games_played": 100,
      "games_won": 55,
      "games_lost": 45,
      "level": 5,
      "xp": 50,
      "last_daily": "2024-01-01T12:00:00",
      "daily_streak": 7,
      "achievements": []
    }
  }
}
```

## 🎯 MODULES INTERDÉPENDANTS

```
bot.py (Core)
  ├── Importe: economy_data, get_user_profile, save_data
  ├── Utilisé par: Tous les modules
  │
  ├── commands/
  │   ├── economy.py
  │   ├── leaderboard.py
  │   ├── betting.py
  │   ├── stats.py
  │   └── help_command.py
  │
  └── games/
      ├── Tous héritent de commands.Cog
      ├── Tous utilisent economy_data
      └── Tous utilisent get_user_profile & save_data
```

## 🔧 PERSONNALISATION FACILE

### Modifier les gains/côtes:
- Chaque jeu a ses multiplicateurs dans la classe
- Exemple dans `slots.py`:
  ```python
  self.symbols = {
      '💀': 10,   # Change le multiplicateur
      '💎': 5,
      ...
  }
  ```

### Modifier les cooldowns:
- Dans chaque fichier de jeu:
  ```python
  @commands.cooldown(1, 3, commands.BucketType.user)
  # 1 fois toutes les 3 secondes
  ```

### Modifier la monnaie:
- Dans `bot.py`:
  ```python
  CURRENCY_NAME = "Skull"
  CURRENCY_EMOJI = "💀"
  ```

## 📈 STATISTIQUES TRACKÉES

Le bot suit automatiquement:
- ✅ Balance
- ✅ Total gagné (incluant daily/gifts)
- ✅ Profit gambling pur (excluant daily/gifts)
- ✅ Total misé
- ✅ Parties/Victoires/Défaites
- ✅ Niveau & XP
- ✅ Streak daily

## 🎮 CATÉGORIES DE JEUX

### Jeux à Chance Pure (8)
coinflip, dice, slots, roulette, plinko, wheel, cups, lottery

### Jeux à Décision (3)
blackjack, crash, mines

### Jeux de Prédiction (2)
higherlower, rps

### Jeux PvP (1)
coinflip_pvp (duel)

## 🔒 SÉCURITÉ

1. **Owner Protection**
   - Bot quitte si owner absent
   - Vérifie à chaque join
   - Vérifie si owner leave

2. **Data Protection**
   - Auto-save 5 min
   - Backups quotidiens
   - Validation des entrées

3. **Anti-Cheat**
   - Cooldowns sur toutes les commandes
   - Vérification balance avant jeu
   - Transactions atomiques

---

**Projet créé avec 💀 pour le gambling!**
