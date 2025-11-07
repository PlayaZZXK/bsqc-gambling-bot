import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp
from database import db

class Plinko(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.multipliers = [0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 5.0, 2.0, 1.0, 0.5, 0.2]

    @app_commands.command(name='plinko', description='Jeu Plinko! La balle tombe!')
    @app_commands.describe(montant='Le montant à miser')
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def plinko(self, interaction: discord.Interaction, montant: int):
        """Jeu Plinko! 🎯 La balle tombe!"""

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s!")

        embed = discord.Embed(title="🎯 Plinko", description="La balle tombe...\n\n⚪", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(2)

        slot = random.randint(0, 10)
        multiplier = self.multipliers[slot]

        winnings = int(montant * multiplier)
        profit = winnings - montant
        won = multiplier > 1.0

        profile['balance'] += profit
        profile['gambling_profit'] += profit
        profile['games_won' if won else 'games_lost'] += 1
        profile['games_played'] += 1
        profile['total_wagered'] += montant
        add_xp(interaction.user.id, interaction.guild.id, 15)
slots_display = "".join([f"[**×{m}**]" if i == slot else f"[×{m}]" for i, m in enumerate(self.multipliers)])

        embed = discord.Embed(
            title="🎯 Plinko - Résultat!"
            description=f"{slots_display}\n\n**Multiplicateur: ×{multiplier}**"
            color=discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Gain/Perte", value=f"{'+' if profit >= 0 else ''}{profit:,} {CURRENCY_NAME}s")
        embed.add_field(name="Solde", value=f"{profile['balance']:,}")

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Plinko(bot))
