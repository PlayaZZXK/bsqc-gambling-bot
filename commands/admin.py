import discord
from discord import app_commands
from discord.ext import commands
import sys
sys.path.append('..')
from bot import OWNER_ID
from database import db

# Rôles autorisés à exécuter les commandes admin
ADMIN_ROLE_IDS = [
    1333483851053535293,
    1333483900537671710,
    1333483947023138826,
    1333483976119287809,
    1345775821893402818
]

def has_admin_role():
    """Vérifier si l'utilisateur a un des rôles admin autorisés"""
    async def predicate(interaction: discord.Interaction) -> bool:
        # Le owner peut toujours utiliser les commandes
        if interaction.user.id == OWNER_ID:
            return True

        # Vérifier si l'utilisateur a un des rôles autorisés
        if interaction.guild and hasattr(interaction.user, 'roles'):
            user_role_ids = [role.id for role in interaction.user.roles]
            if any(role_id in ADMIN_ROLE_IDS for role_id in user_role_ids):
                return True

        # Si aucun rôle autorisé, refuser
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande!", ephemeral=True)
        return False

    return app_commands.check(predicate)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='forcesave', description='Créer un backup de la base de données (Admin)')
    @has_admin_role()
    async def forcesave(self, interaction: discord.Interaction):
        """Créer un backup immédiat de la base de données SQLite"""

        await interaction.response.defer()

        try:
            # Créer un backup de la base de données
            backup_path = db.backup_database()

            embed = discord.Embed(
                title="✅ Backup créé avec succès!",
                description="Un backup de la base de données SQLite a été créé.",
                color=discord.Color.green()
            )
            embed.add_field(name="Fichier", value=backup_path, inline=False)
            embed.add_field(name="Type", value="Backup complet SQLite", inline=True)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de backup!",
                description=f"Une erreur est survenue: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name='botstats', description='Statistiques du bot (Admin)')
    @has_admin_role()
    async def botstats_cmd(self, interaction: discord.Interaction):
        """Afficher les statistiques du bot depuis la base de données"""

        # Récupérer les stats depuis SQLite
        stats = db.get_global_stats()

        embed = discord.Embed(
            title="📊 Statistiques du Bot",
            color=discord.Color.blue()
        )

        embed.add_field(name="🏰 Serveurs", value=f"{stats['total_guilds']}", inline=True)
        embed.add_field(name="👥 Utilisateurs", value=f"{stats['total_users']}", inline=True)
        embed.add_field(name="💰 Balance Totale", value=f"{stats['total_balance']:,} Skulls", inline=True)
        embed.add_field(name="🎲 Parties jouées", value=f"{stats['total_games']:,}", inline=True)
        embed.add_field(name="💸 Total parié", value=f"{stats['total_wagered']:,} Skulls", inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
