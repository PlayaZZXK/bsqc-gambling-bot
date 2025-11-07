#!/usr/bin/env python3
"""
Script pour mettre à jour tous les fichiers de jeux pour utiliser SQLite
"""
import os
import re

def update_game_file(filepath):
    """Met à jour un fichier de jeu pour utiliser la base de données SQLite"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Mettre à jour les imports
    if 'from database import db' not in content:
        # Retirer economy_data et save_data des imports
        content = re.sub(
            r'from bot import (.*?)economy_data,?\s*(.*?)save_data,?\s*(.*)',
            r'from bot import \1\2\3',
            content,
            flags=re.DOTALL
        )

        # Nettoyer les virgules en trop
        content = re.sub(r',\s*,', ',', content)
        content = re.sub(r',\s*\n', '\n', content)

        # Ajouter l'import de db
        content = re.sub(
            r'(from bot import.*?\n)',
            r'\1from database import db\n',
            content,
            count=1
        )

    # 2. Retirer tous les appels à save_data(economy_data)
    content = re.sub(r'\s*save_data\(economy_data\)\s*', '\n', content)

    # 3. Commenter les modifications directes de balance pour inspection manuelle
    # (On ne peut pas automatiser complètement car la logique varie)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Liste des fichiers à mettre à jour
game_files = [
    'games/coinflip.py',
    'games/dice.py',
    'games/blackjack.py',
    'games/roulette.py',
    'games/crash.py',
    'games/mines.py',
    'games/plinko.py',
    'games/wheel.py',
    'games/cups.py',
    'games/higherlower.py',
    'games/rps.py',
    'games/coinflip_pvp.py',
    'games/lottery.py'
]

print("[MIGRATION] Mise a jour des fichiers de jeux...")
updated = 0
skipped = 0

for game_file in game_files:
    if not os.path.exists(game_file):
        print(f"  [SKIP] {game_file} - n'existe pas")
        skipped += 1
        continue

    try:
        if update_game_file(game_file):
            print(f"  [OK] {game_file} - mis a jour")
            updated += 1
        else:
            print(f"  [SKIP] {game_file} - deja a jour")
            skipped += 1
    except Exception as e:
        print(f"  [ERROR] {game_file} - {e}")
        skipped += 1

print(f"\n[DONE] {updated} fichiers mis a jour, {skipped} ignores")
print("\n[IMPORTANT] Les fichiers ont ete mis a jour pour les imports,")
print("mais vous devez verifier manuellement que les modifications")
print("de balance utilisent db.modify_balance() et db.update_user_profile()")
