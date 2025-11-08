import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp
from database import db

class Cups(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='cups', description='Jeu des gobelets!')
    @app_commands.describe(
        choix='Ton choix: 1, 2 ou 3',
        montant='Le montant à miser'
    )
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def cups(self, interaction: discord.Interaction, choix: int, montant: int):
        """Jeu des gobelets! 🥤 Choisis 1, 2 ou 3"""

        if choix not in [1, 2, 3]:
            return await interaction.response.send_message("❌ Choisis 1, 2 ou 3!")

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s!")

        embed = discord.Embed(title="🥤 Jeu des Gobelets", description="Les gobelets se mélangent...\n\n🥤 🥤 🥤", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(2)

        winning_cup = random.randint(1, 3)
        won = (choix == winning_cup)

        cups_display = []
        for i in range(1, 4):
            if i == winning_cup:
                cups_display.append("🏆" if i == choix else "💎")
            else:
                cups_display.append("❌" if i == choix else "🥤")

        if won:
            profit = montant * 2
            profile['balance'] += profit
            profile['gambling_profit'] += profit
            profile['games_won'] += 1
        else:
            profile['balance'] -= montant
            profile['gambling_profit'] -= montant
            profile['games_lost'] += 1

        profile['games_played'] += 1
        profile['total_wagered'] += montant
        add_xp(interaction.user.id, interaction.guild.id, 20 if won else 5)
        embed = discord.Embed(
            title="🎉 Gagné!" if won else "💔 Perdu!",
            description=f"{' '.join(cups_display)}\n\n**La balle était sous le gobelet {winning_cup}!**",
            color=discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Résultat", value=f"{'+' if won else '-'}{montant if not won else profit:,} {CURRENCY_NAME}s")
        embed.add_field(name="Solde", value=f"{profile['balance']:,}")

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Cups(bot))
