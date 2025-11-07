import discord
from discord import app_commands
from discord.ext import commands
import sys
sys.path.append('..')
from bot import CURRENCY_NAME, CURRENCY_EMOJI
from database import db

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='leaderboard', description='Top 10 des joueurs les plus riches du serveur')
    async def leaderboard(self, interaction: discord.Interaction):
        """Top 10 des joueurs les plus riches du serveur 💰"""
        guild_id = str(interaction.guild.id)

        # Récupérer le top 10 depuis la base de données
        top_users = db.get_leaderboard(guild_id, limit=10)

        if not top_users:
            await interaction.response.send_message("❌ Aucune donnée disponible pour ce serveur!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{CURRENCY_EMOJI} Top 10 - Les Plus Riches",
            description="Classement par balance totale",
            color=discord.Color.gold()
        )

        medals = ["🥇", "🥈", "🥉"]

        for i, profile in enumerate(top_users, 1):
            user = self.bot.get_user(int(profile['user_id']))
            username = user.display_name if user else f"Utilisateur {profile['user_id']}"

            medal = medals[i-1] if i <= 3 else f"**{i}.**"

            embed.add_field(
                name=f"{medal} {username}",
                value=f"{profile['balance']:,} {CURRENCY_NAME}s | Niveau {profile['level']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='gamblingtop', description='Top 10 des meilleurs gamblers (profits nets)')
    async def gambling_top(self, interaction: discord.Interaction):
        """Top 10 des meilleurs gamblers (profits nets) 🎰"""
        guild_id = str(interaction.guild.id)

        # Récupérer le top 10 par gambling_profit depuis la base de données
        top_users = db.get_leaderboard(guild_id, order_by='gambling_profit', limit=10)

        if not top_users:
            await interaction.response.send_message("❌ Aucune donnée disponible pour ce serveur!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎰 Top 10 - Meilleurs Gamblers",
            description="Classement par profits de gambling (sans daily/gifts)",
            color=discord.Color.purple()
        )

        medals = ["🥇", "🥈", "🥉"]

        for i, profile in enumerate(top_users, 1):
            user = self.bot.get_user(int(profile['user_id']))
            username = user.display_name if user else f"Utilisateur {profile['user_id']}"

            medal = medals[i-1] if i <= 3 else f"**{i}.**"
            profit = profile['gambling_profit']

            # Emoji selon profit/perte
            status = "📈" if profit > 0 else "📉" if profit < 0 else "➖"

            embed.add_field(
                name=f"{medal} {username}",
                value=f"{status} {profit:,} {CURRENCY_NAME}s | {profile['games_played']} parties",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
