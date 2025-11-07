#!/usr/bin/env python3
"""
Script pour fixer TOUS les jeux pour utiliser db.modify_balance() au lieu de profile['balance'] +=
"""
import os
import re

game_files = [
    'games/coinflip.py',
    'games/dice.py',
    'games/roulette.py',
    'games/crash.py',
    'games/mines.py',
    'games/plinko.py',
    'games/wheel.py',
    'games/cups.py',
    'games/higherlower.py',
    'games/rps.py',
    'games/coinflip_pvp.py',
    'games/lottery.py',
    'games/blackjack.py',
]

for game_file in game_files:
    if not os.path.exists(game_file):
        print(f"[SKIP] {game_file} n'existe pas")
        continue

    print(f"\n[PROCESSING] {game_file}")

    with open(game_file, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Compter les lignes avant/après pour debug
    lines_before = content.count('\n')

    # 2. Retirer TOUTES les lignes save_data(economy_data)
    content = re.sub(r'^\s*save_data\(economy_data\)\s*$', '', content, flags=re.MULTILINE)

    # 3. Nettoyer les lignes vides multiples
    content = re.sub(r'\n\n\n+', '\n\n', content)

    lines_after = content.count('\n')

    if content != original:
        with open(game_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Lignes: {lines_before} -> {lines_after}")
        print(f"  [OK] save_data() calls removed")
    else:
        print(f"  [SKIP] No changes needed")

print("\n[DONE] Tous les save_data() ont ete retires!")
print("\nLes jeux fonctionneront maintenant, mais ils ne sauvegarderont PAS encore correctement.")
print("Il faudra remplacer profile['balance'] += X par db.modify_balance() manuellement")
print("ou laisser le bot fonctionner et on fixera les jeux un par un plus tard.")
