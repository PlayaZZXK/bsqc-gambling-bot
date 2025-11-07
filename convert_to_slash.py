"""
Script pour convertir automatiquement les commandes prefix en commandes slash
"""
import os
import re

def convert_file(filepath):
    """Convertir un fichier de prefix commands vers slash commands"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Import discord.ext.commands -> ajouter app_commands
    if 'from discord.ext import commands' in content and 'from discord import app_commands' not in content:
        content = content.replace(
            'from discord.ext import commands',
            'from discord import app_commands\nfrom discord.ext import commands'
        )

    # Convertir @commands.command -> @app_commands.command
    content = re.sub(
        r'@commands\.command\(name=\'(\w+)\'(?:, aliases=\[.*?\])?\)',
        r'@app_commands.command(name=\'\1\', description=\'Description à compléter\')',
        content
    )

    # Convertir @commands.cooldown -> @app_commands.checks.cooldown
    content = re.sub(
        r'@commands\.cooldown\((\d+), (\d+), commands\.BucketType\.user\)',
        r'@app_commands.checks.cooldown(\1, \2, key=lambda i: i.user.id)',
        content
    )

    # Convertir async def command(self, ctx vers async def command(self, interaction: discord.Interaction
    content = re.sub(
        r'async def (\w+)\(self, ctx(?:, (.+?))?\):',
        lambda m: f'async def {m.group(1)}(self, interaction: discord.Interaction{", " + m.group(2) if m.group(2) else ""})' if 'discord.Member' not in str(m.group(2) or '') else m.group(0),
        content
    )

    # Convertir ctx.author -> interaction.user
    content = content.replace('ctx.author', 'interaction.user')

    # Convertir ctx.guild -> interaction.guild
    content = content.replace('ctx.guild', 'interaction.guild')

    # Convertir ctx.send -> interaction.response.send_message
    content = re.sub(
        r'await ctx\.send\(([^)]+)\)',
        r'await interaction.response.send_message(\1)',
        content
    )

    # Renommer amount -> montant dans les paramètres
    content = re.sub(
        r'\(self, interaction: discord\.Interaction, amount: int\)',
        r'(self, interaction: discord.Interaction, montant: int)',
        content
    )

    # Remplacer amount par montant dans le corps
    # (seulement si c'est le paramètre de la fonction)
    lines = content.split('\n')
    in_function = False
    new_lines = []

    for line in lines:
        if 'def ' in line and 'montant: int' in line:
            in_function = True
            new_lines.append(line)
        elif in_function and line.strip().startswith('def '):
            in_function = False
            new_lines.append(line)
        elif in_function and 'amount' in line and 'amount:' not in line:
            # Remplacer amount par montant sauf dans les définitions
            line = re.sub(r'\bamount\b', 'montant', line)
            new_lines.append(line)
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

    # Sauvegarder seulement si modifié
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Convertir tous les fichiers"""
    files_to_convert = [
        'commands/betting.py',
        'commands/stats.py',
        'commands/leaderboard.py',
        'games/coinflip.py',
        'games/slots.py',
        'games/crash.py',
        'games/dice.py',
        'games/roulette.py',
        'games/mines.py',
        'games/plinko.py',
        'games/wheel.py',
        'games/cups.py',
        'games/higherlower.py',
        'games/rps.py',
        'games/lottery.py',
        'games/coinflip_pvp.py',
    ]

    converted = []
    skipped = []

    for filepath in files_to_convert:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if os.path.exists(full_path):
            try:
                if convert_file(full_path):
                    converted.append(filepath)
                    print(f"✅ Converti: {filepath}")
                else:
                    skipped.append(filepath)
                    print(f"⏭️  Déjà converti: {filepath}")
            except Exception as e:
                print(f"❌ Erreur {filepath}: {e}")
        else:
            print(f"⚠️  Fichier non trouvé: {filepath}")

    print(f"\n📊 Résumé:")
    print(f"   Convertis: {len(converted)}")
    print(f"   Ignorés: {len(skipped)}")

if __name__ == '__main__':
    main()
