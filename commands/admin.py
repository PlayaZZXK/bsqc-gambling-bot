import discord
from discord import app_commands
from discord.ext import commands
import sys
sys.path.append('..')
from bot import OWNER_ID
from database import db

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='forcesave', description='Créer un backup de la base de données (Admin)')
    @app_commands.checks.has_permissions(administrator=True)
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
    @app_commands.checks.has_permissions(administrator=True)
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
