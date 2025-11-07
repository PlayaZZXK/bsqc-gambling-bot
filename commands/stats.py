import discord
from discord import app_commands
from discord.ext import commands
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='stats', description='Voir tes statistiques de gambling complètes')
    @app_commands.describe(member='Le membre dont tu veux voir les stats (optionnel)')
    async def stats(self, interaction: discord.Interaction, member: discord.Member = None):
        """Voir tes statistiques de gambling complètes 📊"""
        if member is None:
            member = interaction.user

        profile = get_user_profile(member.id, interaction.guild.id)

        # Calculs
        total_games = profile['games_played']
        wins = profile['games_won']
        losses = profile['games_lost']

        win_rate = (wins / total_games * 100) if total_games > 0 else 0

        # Ratio gains/pertes
        if profile['total_wagered'] > 0:
            profit_ratio = (profile['gambling_profit'] / profile['total_wagered']) * 100
        else:
            profit_ratio = 0

        # Embed principal
        embed = discord.Embed(
            title=f"📊 Statistiques de {member.display_name}",
            color=discord.Color.blue()
        )

        # Infos générales
        embed.add_field(
            name="💰 Économie",
            value=f"**Balance:** {profile['balance']:,} {CURRENCY_NAME}s\n"
                  f"**Total gagné:** {profile['total_earned']:,} {CURRENCY_NAME}s\n"
                  f"**Niveau:** {profile['level']} ({profile['xp']}/100 XP)",
            inline=False
        )

        # Stats de gambling
        profit_emoji = "📈" if profile['gambling_profit'] > 0 else "📉" if profile['gambling_profit'] < 0 else "➖"

        embed.add_field(
            name="🎰 Gambling",
            value=f"**Profit net:** {profit_emoji} {profile['gambling_profit']:,} {CURRENCY_NAME}s\n"
                  f"**Total misé:** {profile['total_wagered']:,} {CURRENCY_NAME}s\n"
                  f"**Ratio profit:** {profit_ratio:.1f}%",
            inline=False
        )

        # Victoires/Défaites
        embed.add_field(
            name="⚔️ Record",
            value=f"**Parties jouées:** {total_games}\n"
                  f"**Victoires:** {wins} 🏆\n"
                  f"**Défaites:** {losses} ❌\n"
                  f"**Taux de victoire:** {win_rate:.1f}%",
            inline=False
        )

        # Daily streak
        if profile.get('daily_streak', 0) > 0:
            embed.add_field(
                name="🔥 Streak Daily",
                value=f"{profile['daily_streak']} jours consécutifs!",
                inline=False
            )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='profile', description='Voir le profil d\'un joueur')
    @app_commands.describe(member='Le membre dont tu veux voir le profil (optionnel)')
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        """Alias pour /stats"""
        await self.stats(interaction, member)

    @app_commands.command(name='rank', description='Voir ton rang dans le serveur')
    @app_commands.describe(member='Le membre dont tu veux voir le rang (optionnel)')
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        """Voir ton rang dans le serveur 🏅"""
        if member is None:
            member = interaction.user

        guild_id = str(interaction.guild.id)

        # Récupérer le rang par balance depuis la DB
        rank = db.get_user_rank(member.id, guild_id, order_by='balance')

        if rank is None:
            await interaction.response.send_message("❌ Utilisateur non trouvé dans le classement!", ephemeral=True)
            return

        profile = get_user_profile(member.id, interaction.guild.id)

        # Récupérer le rang par gambling profit
        gambler_rank = db.get_user_rank(member.id, guild_id, order_by='gambling_profit')

        embed = discord.Embed(
            title=f"🏅 Rang de {member.display_name}",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="💰 Classement Richesse",
            value=f"**#{rank}** sur {len(sorted_users)} joueurs\n"
                  f"{profile['balance']:,} {CURRENCY_NAME}s",
            inline=True
        )

        embed.add_field(
            name="🎰 Classement Gambling",
            value=f"**#{gambler_rank}** sur {len(sorted_gamblers)} joueurs\n"
                  f"{profile['gambling_profit']:,} {CURRENCY_NAME}s de profit",
            inline=True
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
