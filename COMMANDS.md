# 📋 LISTE COMPLÈTE DES COMMANDES

## 💰 ÉCONOMIE

| Commande | Aliases | Description | Cooldown |
|----------|---------|-------------|----------|
| `!balance [@user]` | `!bal`, `!money` | Voir le solde | - |
| `!daily` | - | Réclamer 100 Skulls quotidiens | 24h |
| `!gift <@user> <montant>` | `!give`, `!transfer` | Donner des Skulls | 60s |

## 🎰 JEUX CLASSIQUES

| Commande | Description | Côte | Cooldown |
|----------|-------------|------|----------|
| `!coinflip <heads/tails> <montant>` | Pile ou face | ×2 | 3s |
| `!dice <over/under/exact> <montant>` | Lancer de dés | ×2 / ×6 | 3s |
| `!slots <montant>` | Machine à sous | ×1.5-×10 | 4s |
| `!blackjack <montant>` | Blackjack | ×2 / ×2.5 | 5s |
| `!roulette <red/black/0-36> <montant>` | Roulette | ×2 / ×36 | 4s |

## 🎮 JEUX MODERNES

| Commande | Description | Côte | Cooldown |
|----------|-------------|------|----------|
| `!crash <montant>` | Cash out avant le crash | Variable | 10s |
| `!mines <montant> [nb]` | Démineur avec paris | Variable | 10s |
| `!plinko <montant>` | Balle qui tombe | ×0.2-×10 | 5s |
| `!wheel <montant>` | Roue de la fortune | ×2-×50 | 5s |
| `!cups <1/2/3> <montant>` | Jeu des gobelets | ×2 | 5s |

## 🎯 JEUX PVP & AUTRES

| Commande | Description | Côte | Cooldown |
|----------|-------------|------|----------|
| `!higherlower <h/l> <montant>` | Carte plus haute/basse | ×2 | 5s |
| `!rps <rock/paper/scissors> <montant>` | Pierre-Papier-Ciseaux | ×2 | 3s |
| `!duel <@user> <montant>` | Défi coinflip PvP | ×2 | 30s |
| `!lottery` | Info sur la loterie | - | - |
| `!buyticket` | Acheter un ticket (100 Skulls) | Variable | 60s |
| `!drawlottery` | Tirer au sort (Admin) | - | - |

## 🏆 STATISTIQUES & CLASSEMENTS

| Commande | Aliases | Description |
|----------|---------|-------------|
| `!stats [@user]` | `!profile`, `!me` | Statistiques personnelles détaillées |
| `!rank [@user]` | - | Voir son classement dans le serveur |
| `!leaderboard` | `!lb`, `!top`, `!rich` | Top 10 des plus riches (total) |
| `!gamblingtop` | `!gtop`, `!profittop` | Top 10 meilleurs gamblers (profit net) |

## 🎲 SYSTÈME DE PARIS

| Commande | Description | Permission |
|----------|-------------|------------|
| `!createbet` | Créer un nouveau pari | Admin |
| `!activebets` | Voir les paris actifs | Tous |
| `!viewbet <id>` | Détails d'un pari | Tous |
| `!placebet <id> <opt> <montant>` | Placer un pari | Tous |
| `!closebet <id> <opt_gagnante>` | Fermer un pari | Admin |

## 📚 AIDE & INFO

| Commande | Aliases | Description |
|----------|---------|-------------|
| `!help [catégorie]` | `!h`, `!commands`, `!aide` | Menu d'aide |
| `!info` | `!botinfo`, `!about` | Informations sur le bot |

### Catégories d'aide disponibles:
- `!help economy` - Commandes d'économie
- `!help games` - Tous les jeux
- `!help betting` - Système de paris
- `!help stats` - Stats et classements

## ⚙️ ADMIN (Owner seulement)

| Commande | Description |
|----------|-------------|
| `!reload <module>` | Recharger un module |
| `!save` | Sauvegarder manuellement |

## 📊 STATISTIQUES TRACKÉES

Le bot track automatiquement:
- ✅ Balance totale
- ✅ Total gagné (toutes sources)
- ✅ Profit de gambling pur (sans daily/gifts)
- ✅ Total misé
- ✅ Parties jouées
- ✅ Victoires
- ✅ Défaites
- ✅ Ratio gains/pertes
- ✅ Niveau et XP
- ✅ Streak daily
- ✅ Achievements (à venir)

## 💡 ASTUCES

### Symboles de jeux:
- 💀 Skull - Monnaie et Jackpot
- 🪙 Coinflip
- 🎲 Dice
- 🎰 Slots
- ♠️ Blackjack
- 🎡 Roulette
- 🚀 Crash
- 💣 Mines
- 🎯 Plinko
- 🎡 Wheel
- 🥤 Cups
- 🎴 Higher/Lower
- ✊✋✌️ RPS
- 🎫 Lottery
- ⚔️ Duel

### Raccourcis:
- `!cf` = `!coinflip`
- `!bj` = `!blackjack`
- `!rl` = `!roulette`
- `!hl` = `!higherlower`
- `!s` = `!slots`
- `!lb` = `!leaderboard`
- `!gtop` = `!gamblingtop`
- `!bal` = `!balance`

### Cooldowns:
- Jeux rapides: 3-5s
- Jeux complexes: 10s
- Daily: 24h
- Gift: 60s
- Duel: 30s

## 🎯 EXEMPLES D'UTILISATION

```
# Économie
!daily                          # Réclamer daily
!balance                        # Voir ton solde
!balance @user                  # Voir le solde d'un autre
!gift @friend 500              # Donner 500 Skulls

# Jeux
!coinflip heads 100            # Parier 100 sur heads
!dice over 50                  # Parier 50 sur >7
!slots 200                     # Jouer 200 aux slots
!blackjack 150                 # Jouer 150 au blackjack
!roulette red 100              # Parier 100 sur rouge
!roulette 17 50                # Parier 50 sur le 17

# PvP
!duel @opponent 500            # Défier avec mise de 500

# Stats
!stats                          # Tes stats
!rank                          # Ton classement
!leaderboard                   # Top 10 richesse
!gamblingtop                   # Top 10 gambling

# Paris
!createbet                      # Créer un pari (Admin)
!activebets                    # Voir paris actifs
!placebet abc123 1 500         # Parier 500 sur option 1
!viewbet abc123                # Voir détails du pari
!closebet abc123 2             # Fermer, option 2 gagne
```

---

**🎰 Bon gambling! Que les Skulls soient avec toi! 💀**
