import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import asyncio
import signal
import sys as system
from database import db

# Configuration
OWNER_ID = 1270241225861234690
PREFIX = "!"
CURRENCY_NAME = "Skull"
CURRENCY_EMOJI = "💀"

# Limites de jeu
MAX_BET_AMOUNT = 50  # Mise maximum pour les jeux normaux
MAX_WIN_AMOUNT = 340  # Gain maximum pour les jeux normaux
MAX_NHL_BET = 5000  # Mise maximum pour les paris NHL
GAME_COOLDOWN = 3  # Cooldown en secondes entre chaque jeu

# Dictionnaire pour gérer les cooldowns par utilisateur et jeu
game_cooldowns = {}

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

print("[SYSTEM] ==================================")
print("[SYSTEM] UTILISATION DE SQLITE DATABASE")
print("[SYSTEM] Sauvegarde instantanee garantie!")
print("[SYSTEM] ==================================")


# ==========================================
# FONCTIONS DATABASE - SQLITE
# ==========================================

def save_data(data=None, force_backup=False):
    """Sauvegarde avec SQLite - Backup seulement"""
    if force_backup:
        db.backup_database()
        print("[DATABASE] Backup force cree")
    # Avec SQLite, pas besoin de sauvegarder manuellement!
    return True

# Sauvegarder avant fermeture du bot
def save_on_exit(signum=None, frame=None):
    """Sauvegarde forcée lors de la fermeture"""
    print("\n[SHUTDOWN] Fermeture du bot detectee...")
    db.backup_database()
    db.close()
    print("[SHUTDOWN] Backup cree et connexion fermee!")
    system.exit(0)

# Enregistrer les signaux de fermeture
signal.signal(signal.SIGINT, save_on_exit)   # Ctrl+C
signal.signal(signal.SIGTERM, save_on_exit)  # Fermeture normale

# Fonction pour obtenir/créer un profil utilisateur
def get_user_profile(user_id, guild_id):
    """Récupère un profil depuis la base de données SQLite"""
    return db.get_user_profile(user_id, guild_id)

# Fonction pour vérifier et gérer les cooldowns
def check_cooldown(user_id, game_name):
    """
    Vérifie si l'utilisateur peut jouer (pas en cooldown)
    Retourne (can_play: bool, remaining_time: float)
    """
    now = datetime.now()
    key = f"{user_id}_{game_name}"

    if key in game_cooldowns:
        elapsed = (now - game_cooldowns[key]).total_seconds()
        if elapsed < GAME_COOLDOWN:
            return False, GAME_COOLDOWN - elapsed

    # Mettre à jour le cooldown
    game_cooldowns[key] = now
    return True, 0

# Backup automatique toutes les heures
async def auto_backup():
    await bot.wait_until_ready()
    print("[DATABASE] Systeme de backup automatique demarre (toutes les heures)")
    while not bot.is_closed():
        await asyncio.sleep(3600)  # 1 heure
        try:
            db.backup_database()
            print(f"[DATABASE] Backup periodique: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"[ERROR] Erreur backup auto: {e}")

# Système de niveaux
def add_xp(user_id, guild_id, amount=10):
    profile = get_user_profile(user_id, guild_id)
    new_xp = profile["xp"] + amount

    # Calcul niveau
    xp_needed = profile["level"] * 100
    if new_xp >= xp_needed:
        # Level up!
        db.update_user_profile(user_id, guild_id, level=profile["level"] + 1, xp=0)
        return True
    else:
        db.update_user_profile(user_id, guild_id, xp=new_xp)
        return False

# Vérification de sécurité - Owner dans le serveur
@bot.event
async def on_guild_join(guild):
    owner = guild.get_member(OWNER_ID)
    if not owner:
        # Envoyer un message avant de quitter
        embed = discord.Embed(
            title="⚠️ Erreur de Sécurité",
            description="Désolé, le Owner n'est pas présent sur le serveur!",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Raison",
            value="Pour des raisons de sécurité, ce bot nécessite que le propriétaire soit présent dans le serveur.",
            inline=False
        )
        embed.add_field(
            name="ID du Owner requis",
            value=f"`{OWNER_ID}`",
            inline=False
        )

        # Trouver le premier channel où on peut envoyer un message
        for channel in guild.text_channels:
            try:
                await channel.send(embed=embed)
                break
            except:
                continue

        await guild.leave()
        print(f"[SECURITY] Quitte le serveur {guild.name} - Owner non present")

@bot.event
async def on_ready():
    print(f'[SYSTEM] Bot connecte en tant que {bot.user}')
    print(f'[SYSTEM] Monnaie: {CURRENCY_NAME} {CURRENCY_EMOJI}')

    # Vérifier tous les serveurs
    for guild in bot.guilds:
        owner = guild.get_member(OWNER_ID)
        if not owner:
            await guild.leave()
            print(f"[SECURITY] Quitte le serveur {guild.name} - Owner non present")

    # Synchroniser les commandes slash
    try:
        synced = await bot.tree.sync()
        print(f'[SYSTEM] {len(synced)} commandes slash synchronisees!')
    except Exception as e:
        print(f'[ERROR] Erreur sync commandes: {e}')

    # Démarrer le backup automatique
    bot.loop.create_task(auto_backup())

@bot.event
async def on_member_remove(member):
    # Si l'owner quitte, le bot quitte aussi
    if member.id == OWNER_ID:
        await member.guild.leave()
        print(f"[SECURITY] Owner a quitte {member.guild.name}, bot quitte aussi")

@bot.event
async def on_message(message):
    # Ignorer les messages du bot
    if message.author.bot:
        return

    # Traiter les commandes normalement
    await bot.process_commands(message)

@bot.tree.command(name='show', description='Afficher les commandes essentielles du bot')
async def show_commands(interaction: discord.Interaction):
    """Afficher les commandes essentielles du bot"""
    embed = discord.Embed(
        title="💀 Commandes Essentielles - Skull Casino 🎰",
        description="Voici toutes les commandes principales du bot!",
        color=discord.Color.dark_gold()
    )

    embed.add_field(
        name="💰 Économie",
        value=(
            "`/balance` - Voir ton solde\n"
            "`/daily` - Récupérer ta récompense quotidienne\n"
            "`/work` - Travailler pour gagner de l'argent\n"
            "`/give` - Donner de l'argent à quelqu'un\n"
            "`/rob` - Tenter de voler quelqu'un"
        ),
        inline=False
    )

    embed.add_field(
        name="👑 Commandes Admin",
        value=(
            "`/giveadmin` - Donner des Skulls sans limite (Admin)\n"
            "`/setlottery` - Configurer la loterie (Admin)\n"
            "`/createbet` - Créer un pari personnalisé (Admin)\n"
            "`/setupnhlbet` - Configurer les paris NHL auto (Admin)\n"
            "`/forcenhlbet` - Forcer un pari NHL maintenant (Admin)"
        ),
        inline=False
    )

    embed.add_field(
        name="🎲 Paris & Jeux",
        value=(
            "`/placebet` - Placer un pari sur une option\n"
            "`/activebets` - Voir les paris actifs\n"
            "`/nhlbetstatus` - Statut des paris NHL auto\n"
            "`/listejeux` - Voir tous les jeux de gambling disponibles"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 Statistiques & Classement",
        value=(
            "`/stats` - Voir tes statistiques de jeu\n"
            "`/leaderboard` - Voir le classement du serveur\n"
            "`/profile` - Voir le profil d'un joueur"
        ),
        inline=False
    )

    embed.add_field(
        name="🎰 Accès Rapide aux Jeux Populaires",
        value=(
            "`/slots` - Machine à sous\n"
            "`/blackjack` - Blackjack (21)\n"
            "`/coinflip` - Pile ou face\n"
            "`/crash` - Crash game"
        ),
        inline=False
    )

    embed.set_footer(text="💀 Utilise /listejeux pour voir tous les jeux!")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='listejeux', description='Afficher la liste de tous les jeux de gambling')
async def liste_jeux(interaction: discord.Interaction):
    """Afficher la liste de tous les jeux de gambling"""
    embed = discord.Embed(
        title="🎰 Liste des Jeux de Gambling 💀",
        description="Voici tous les jeux disponibles pour te ruiner!",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="🎲 Jeux de Dés & Hasard",
        value=(
            "`/coinflip` - Pile ou face\n"
            "`/dice` - Lance les dés\n"
            "`/rps` - Pierre, papier, ciseaux"
        ),
        inline=False
    )

    embed.add_field(
        name="🎰 Machines à Sous",
        value=(
            "`/slots` - Machine à sous classique\n"
            "`/wheel` - Roue de la fortune\n"
            "`/plinko` - Plinko chanceux"
        ),
        inline=False
    )

    embed.add_field(
        name="🃏 Jeux de Cartes",
        value=(
            "`/blackjack` - Blackjack (21)\n"
            "`/higherlower` - Plus haut ou plus bas"
        ),
        inline=False
    )

    embed.add_field(
        name="🎯 Jeux de Stratégie",
        value=(
            "`/roulette` - Roulette (rouge/noir/vert/numéro)\n"
            "`/crash` - Crash game (cashout au bon moment)\n"
            "`/mines` - Démineur (évite les bombes)\n"
            "`/cups` - Jeu des gobelets"
        ),
        inline=False
    )

    embed.add_field(
        name="👥 Jeux PvP",
        value=(
            "`/coinflip_pvp` - Coinflip contre un autre joueur\n"
            "`/lottery` - Loterie du serveur"
        ),
        inline=False
    )

    embed.set_footer(text="💀 Bonne chance! Les montants se spécifient via les options des commandes")

    await interaction.response.send_message(embed=embed)

# Charger tous les modules de jeux
async def load_extensions():
    # Modules fonctionnels avec SQLite
    cogs = [
        'commands.economy',
        'commands.leaderboard',
        'commands.betting',
        'commands.stats',
        'commands.help_command',
        'commands.admin',  # Commandes admin
        'commands.poker',  # Texas Hold'em multijoueur
        'games.slots',
        'games.coinflip',
        'games.dice',
        'games.blackjack',
        'games.roulette',
        'games.crash',
        'games.mines',
        'games.plinko',
        'games.wheel',
        'games.cups',
        'games.higherlower',
        'games.rps',
        'games.lottery',
        'games.coinflip_pvp'
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'[LOAD] Charge: {cog}')
        except Exception as e:
            print(f'[ERROR] Erreur chargement {cog}: {e}')

# Commande de reload pour l'owner
@bot.command(name='reload')
@commands.is_owner()
async def reload_cog(ctx, cog: str):
    """Recharger un module (Owner seulement)"""
    try:
        await bot.reload_extension(cog)
        await ctx.send(f'✅ Module `{cog}` rechargé!')
    except Exception as e:
        await ctx.send(f'❌ Erreur: {e}')

# Commande de backup manuelle
@bot.command(name='save')
@commands.is_owner()
async def manual_save(ctx):
    """Créer un backup de la base de données"""
    db.backup_database()
    await ctx.send('✅ Backup créé!')

# Gestion d'erreurs
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'⏰ Cooldown! Réessaye dans {error.retry_after:.1f}s')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'❌ Argument manquant! Utilise `{PREFIX}help {ctx.command}`')
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignorer les commandes inexistantes
    else:
        print(f'Erreur: {error}')

async def main():
    async with bot:
        await load_extensions()
        try:
            # Récupérer le token depuis les variables d'environnement
            import os
            TOKEN = os.getenv('DISCORD_TOKEN')
            if not TOKEN:
                print("[ERROR] DISCORD_TOKEN non defini dans les variables d'environnement!")
                return
            await bot.start(TOKEN)
        finally:
            # Backup et fermeture propre
            print("[SHUTDOWN] Backup final avant fermeture...")
            db.backup_database()
            db.close()
            print("[SHUTDOWN] Base de donnees fermee proprement!")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Backup avant arret...")
        db.backup_database()
        db.close()
        print("[SHUTDOWN] Bot arrete proprement!")
