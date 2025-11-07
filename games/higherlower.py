import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp
from database import db

class HigherLower(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='higherlower', description='Higher or Lower! Carte plus haute ou plus basse?')
    @app_commands.describe(
        choix='Ton choix: higher/lower'
        montant='Le montant à miser'
    )
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def higherlower(self, interaction: discord.Interaction, choix: str, montant: int):
        """Higher or Lower! 🎴 Carte plus haute ou plus basse?"""

        choix = choix.lower()
        if choix not in ['higher', 'lower', 'h', 'l', 'high', 'low']:
            return await interaction.response.send_message("❌ Choisis: higher/lower!")

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s!")

        cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        card_values = {c: i for i, c in enumerate(cards, 2)}

        first_card = random.choice(cards)
        second_card = random.choice(cards)

        embed = discord.Embed(
            title="🎴 Higher or Lower"
            description=f"**Première carte:** {first_card}\n\nTu as parié: **{choix.upper()}**"
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(2)

        first_val = card_values[first_card]
        second_val = card_values[second_card]

        if choix in ['higher', 'h', 'high']:
            won = second_val > first_val
        else:
            won = second_val < first_val

        if second_val == first_val:
            won = False

        if won:
            profit = montant
            profile['balance'] += profit
            profile['gambling_profit'] += profit
            profile['games_won'] += 1
        else:
            profile['balance'] -= montant
            profile['gambling_profit'] -= montant
            profile['games_lost'] += 1

        profile['games_played'] += 1
        profile['total_wagered'] += montant
        add_xp(interaction.user.id, interaction.guild.id, 15 if won else 5)
embed = discord.Embed(
            title="🎉 Gagné!" if won else "💔 Perdu!"
            description=f"**Première carte:** {first_card} ({first_val})\n**Deuxième carte:** {second_card} ({second_val})"
            color=discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Résultat", value=f"{'+' if won else '-'}{montant if not won else profit:,} {CURRENCY_NAME}s")
        embed.add_field(name="Solde", value=f"{profile['balance']:,}")

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(HigherLower(bot))
