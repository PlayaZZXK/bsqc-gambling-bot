import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp, check_cooldown, MAX_BET_AMOUNT, MAX_WIN_AMOUNT
from database import db

class HigherLower(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='higherlower', description='Higher or Lower! Carte plus haute ou plus basse?')
    @app_commands.describe(
        choix='Ton choix: higher/lower',
        montant='Le montant à miser'
    )
    async def higherlower(self, interaction: discord.Interaction, choix: str, montant: int):
        """Higher or Lower! 🎴 Carte plus haute ou plus basse?"""

        # Vérifier le cooldown
        can_play, remaining = check_cooldown(interaction.user.id, "higherlower")
        if not can_play:
            await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans {remaining:.1f}s")
            return

        choix = choix.lower()
        if choix not in ['higher', 'lower', 'h', 'l', 'high', 'low']:
            return await interaction.response.send_message("❌ Choisis: higher/lower!")

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        if montant > MAX_BET_AMOUNT:
            await interaction.response.send_message(f"❌ La mise maximum est de {MAX_BET_AMOUNT} {CURRENCY_NAME}s!")
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s!")

        cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        card_values = {c: i for i, c in enumerate(cards, 2)}

        first_card = random.choice(cards)
        second_card = random.choice(cards)

        embed = discord.Embed(
            title="🎴 Higher or Lower",
            description=f"**Première carte:** {first_card}\n\nTu as parié: **{choix.upper()}**",
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
            winnings = montant * 2
            # Appliquer la limite de gain maximum
            if winnings > MAX_WIN_AMOUNT:
                winnings = MAX_WIN_AMOUNT
            profit = winnings - montant
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, profit, "higherlower win")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] + profit,
                games_won=profile['games_won'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance
            xp_gain = 15
        else:
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "higherlower loss")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] - montant,
                games_lost=profile['games_lost'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance
            xp_gain = 5

        leveled_up = add_xp(interaction.user.id, interaction.guild.id, xp_gain)
        if leveled_up:
            profile = get_user_profile(interaction.user.id, interaction.guild.id)

        embed = discord.Embed(
            title="🎉 Gagné!" if won else "💔 Perdu!",
            description=f"**Première carte:** {first_card} ({first_val})\n**Deuxième carte:** {second_card} ({second_val})",
            color=discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Résultat", value=f"{'+' if won else '-'}{profit if won else montant:,} {CURRENCY_NAME}s")
        embed.add_field(name="Solde", value=f"{profile['balance']:,}")

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(HigherLower(bot))
