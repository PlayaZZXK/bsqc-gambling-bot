import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI, add_xp
from database import db

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        self.black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

    @app_commands.command(name='roulette', description='Jouer à la roulette!')
    @app_commands.describe(
        bet_type='Type de pari: red/black/odd/even/green/0-36',
        montant='Le montant à miser'
    )
    @app_commands.checks.cooldown(1, 4, key=lambda i: i.user.id)
    async def roulette(self, interaction: discord.Interaction, bet_type: str, montant: int):
        """
        Jouer à la roulette! 🎡

        Types de paris:
        - red / black: Rouge ou noir (×2)
        - odd / even: Pair ou impair (×2)
        - green / 0: Zéro vert (×36)
        - 1-36: Numéro spécifique (×36)
        """

        bet_type = bet_type.lower()

        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif!")
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        if profile['balance'] < montant:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de {CURRENCY_NAME}s! (Tu as: {profile['balance']:,})")
            return

        # Animation
        embed = discord.Embed(
            title="🎡 Roulette",
            description="La roue tourne...\n\n🔴 ⚫ 🟢",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        await asyncio.sleep(2)

        # Lancer la roulette
        number = random.randint(0, 36)

        # Déterminer la couleur
        if number == 0:
            color_result = "🟢 GREEN"
            color_code = discord.Color.green()
        elif number in self.red_numbers:
            color_result = "🔴 RED"
            color_code = discord.Color.red()
        else:
            color_result = "⚫ BLACK"
            color_code = discord.Color.dark_gray()

        # Vérifier le gain
        won = False
        multiplier = 0

        if bet_type in ['red', 'r', 'rouge'] and number in self.red_numbers:
            won = True
            multiplier = 2
        elif bet_type in ['black', 'b', 'noir'] and number in self.black_numbers:
            won = True
            multiplier = 2
        elif bet_type in ['odd', 'o', 'impair'] and number % 2 == 1 and number != 0:
            won = True
            multiplier = 2
        elif bet_type in ['even', 'e', 'pair'] and number % 2 == 0 and number != 0:
            won = True
            multiplier = 2
        elif bet_type in ['green', 'g', '0'] and number == 0:
            won = True
            multiplier = 36
        elif bet_type.isdigit() and int(bet_type) == number:
            won = True
            multiplier = 36

        # Calculs
        if won:
            winnings = montant * multiplier
            profit = winnings - montant
            profile['balance'] += profit
            profile['gambling_profit'] += profit
            profile['games_won'] += 1
            result_color = discord.Color.green()
            title = "🎉 Gagné!"
        else:
            profile['balance'] -= montant
            profile['gambling_profit'] -= montant
            profile['games_lost'] += 1
            result_color = discord.Color.red()
            title = "💔 Perdu!"

        profile['games_played'] += 1
        profile['total_wagered'] += montant

        xp_gain = int(30 * multiplier) if won else 5
        leveled_up = add_xp(interaction.user.id, interaction.guild.id, xp_gain)
        # Résultat
        embed = discord.Embed(
            title=title,
            description=f"**Résultat:** {color_result} **{number}**\n**Tu as parié:** {bet_type.upper()}",
            color=result_color
        )

        if won:
            embed.add_field(name="Gain", value=f"+{profit:,} {CURRENCY_NAME}s (×{multiplier})", inline=True)
        else:
            embed.add_field(name="Perte", value=f"-{montant:,} {CURRENCY_NAME}s", inline=True)

        embed.add_field(name="Nouveau solde", value=f"{profile['balance']:,} {CURRENCY_NAME}s", inline=True)

        if leveled_up:
            embed.add_field(name="🎉 Level Up!", value=f"Niveau {profile['level']}!", inline=False)

        await message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Roulette(bot))
