import os
import re

# List of all game files to update
game_files = [
    'games/coinflip.py',
    'games/dice.py',
    'games/slots.py',
    'games/blackjack.py',
    'games/roulette.py',
    'games/crash.py',
    'games/mines.py',
    'games/plinko.py',
    'games/wheel.py',
    'games/cups.py',
    'games/higherlower.py',
    'games/rps.py',
    'games/coinflip_pvp.py'
]

for game_file in game_files:
    filepath = game_file
    if not os.path.exists(filepath):
        print(f"[SKIP] {game_file} n'existe pas")
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already migrated
    if 'from database import db' in content:
        print(f"[SKIP] {game_file} deja migre")
        continue

    original_content = content

    # 1. Update imports
    # Remove economy_data and save_data from imports
    content = re.sub(
        r'from bot import ([^\\n]*?)economy_data,?\s*([^\\n]*?)save_data,?\s*([^\\n]*)',
        r'from bot import \1\2\3',
        content
    )

    # Clean up extra commas
    content = re.sub(r',\s*,', ',', content)
    content = re.sub(r'from bot import\s*,', 'from bot import', content)
    content = re.sub(r',\s*$', '', content, flags=re.MULTILINE)

    # Add database import
    if 'from database import db' not in content:
        # Find the last import line
        lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import_idx = i

        lines.insert(last_import_idx + 1, 'from database import db')
        content = '\n'.join(lines)

    # 2. Replace save_data(economy_data) calls with nothing (SQLite auto-saves!)
    content = re.sub(r'\\s*save_data\\(economy_data\\)', '', content)

    # 3. Replace profile modifications with db calls
    # Pattern: profile['balance'] += amount
    # We need to be careful here - let's just remove save_data calls for now
    # and let the developer manually update the complex logic

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[UPDATE] {game_file} modifie - imports mis a jour, save_data() retire")
    else:
        print(f"[NO CHANGE] {game_file}")

print("\n[DONE] Migration des imports terminee!")
print("[NOTE] Les fichiers doivent encore etre mis a jour manuellement pour utiliser db.modify_balance() au lieu de profile['balance'] += X")
