import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp
from database import db

class Wheel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.segments = [
            ("💀 SKULL", 50, 0.01),
            ("💎 Diamant", 20, 0.05),
            ("👑 Couronne", 10, 0.10),
            ("⭐ Étoile", 5, 0.15),
            ("🍒 Cerise", 2, 0.30),
            ("💩 Lose", 0, 0.39)
        ]

    @app_commands.command(name='wheel', description='Roue de la fortune!')
    @app_commands.describe(montant='Le montant à miser')
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def wheel(self, interaction: discord.Interaction, montant: int):
        """Roue de la fortune! 🎡"""

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s!")

        embed = discord.Embed(title="🎡 Roue de la Fortune", description="La roue tourne...", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(2)

        result = random.choices(self.segments, weights=[s[2] for s in self.segments])[0]
        multiplier = result[1]

        if multiplier > 0:
            winnings = montant * multiplier
            profit = winnings - montant
            won = True
        else:
            profit = -montant
            won = False

        profile['balance'] += profit
        profile['gambling_profit'] += profit
        profile['games_won' if won else 'games_lost'] += 1
        profile['games_played'] += 1
        profile['total_wagered'] += montant
        add_xp(interaction.user.id, interaction.guild.id, int(15 * multiplier) if won else 5)
        embed = discord.Embed(
            title=f"🎡 {result[0]}!",
            description=f"**Multiplicateur: ×{multiplier}**",
            color=discord.Color.gold() if multiplier > 10 else discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Résultat", value=f"{'+' if profit >= 0 else ''}{profit:,} {CURRENCY_NAME}s")
        embed.add_field(name="Solde", value=f"{profile['balance']:,}")

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Wheel(bot))
