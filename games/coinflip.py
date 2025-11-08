import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI, add_xp
from database import db

class Coinflip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='coinflip', description='Jouer au coinflip!')
    @app_commands.describe(
        choix='Ton choix: heads/tails (face/pile)',
        montant='Le montant à miser'
    )
    @app_commands.checks.cooldown(1, 3, key=lambda i: i.user.id)
    async def coinflip(self, interaction: discord.Interaction, choix: str, montant: int):
        """
        Jouer au coinflip! 💰

        Côte: 2x (double ta mise si tu gagnes!)
        """

        # Valider le choix
        choix = choix.lower()
        if choix not in ['heads', 'tails', 'pile', 'face', 'h', 't', 'p', 'f']:
            await interaction.response.send_message("❌ Choix invalide! Utilise: `heads/tails` ou `pile/face`")
            return

        # Normaliser le choix
        if choix in ['heads', 'face', 'h', 'f']:
            choix = 'heads'
        else:
            choix = 'tails'

        # Valider le montant
        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif!")
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        if profile['balance'] < montant:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de {CURRENCY_NAME}s! (Tu as: {profile['balance']:,})")
            return

        # Lancer la pièce
        result = random.choice(['heads', 'tails'])

        # Animation
        coin_animation = ["🪙", "💫", "✨", "🌟"]
        embed = discord.Embed(
            title="🪙 Coinflip!",
            description=f"{interaction.user.mention} lance la pièce...\n\n{''.join(random.choices(coin_animation, k=5))}",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        await asyncio.sleep(2)

        # Résultat
        won = (choix == result)

        if won:
            winnings = montant * 2
            profit = montant
            profile['balance'] += profit
            profile['gambling_profit'] += profit
            profile['games_won'] += 1
            color = discord.Color.green()
            title = "🎉 Gagné!"
            result_emoji = "💰"
        else:
            profile['balance'] -= montant
            profile['gambling_profit'] -= montant
            profile['games_lost'] += 1
            color = discord.Color.red()
            title = "💔 Perdu!"
            result_emoji = "❌"

        profile['games_played'] += 1
        profile['total_wagered'] += montant

        # XP
        xp_gain = 15 if won else 5
        leveled_up = add_xp(interaction.user.id, interaction.guild.id, xp_gain)
        # Embed résultat
        result_display = "Face 😊" if result == 'heads' else "Pile 🔄"
        choice_display = "Face 😊" if choix == 'heads' else "Pile 🔄"

        embed = discord.Embed(
            title=title,
            description=f"**Tu as choisi:** {choice_display}\n**Résultat:** {result_display}",
            color=color
        )

        if won:
            embed.add_field(name="Gain", value=f"+{profit:,} {CURRENCY_NAME}s {result_emoji}", inline=True)
        else:
            embed.add_field(name="Perte", value=f"-{montant:,} {CURRENCY_NAME}s {result_emoji}", inline=True)

        embed.add_field(name="Nouveau solde", value=f"{profile['balance']:,} {CURRENCY_NAME}s", inline=True)

        if leveled_up:
            embed.add_field(name="🎉 Level Up!", value=f"Niveau {profile['level']}!", inline=False)

        await message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Coinflip(bot))
