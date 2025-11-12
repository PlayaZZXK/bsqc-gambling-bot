import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI, add_xp, check_cooldown, MAX_BET_AMOUNT, MAX_WIN_AMOUNT
from database import db

class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='dice', description='Jouer aux dés!')
    @app_commands.describe(
        prediction='Ta prédiction: over/under/exact',
        montant='Le montant à miser'
    )
    async def dice(self, interaction: discord.Interaction, prediction: str, montant: int):
        """
        Jouer aux dés! 🎲

        - over 7: Gagner si le total est > 7 (côte 2x)
        - under 7: Gagner si le total est < 7 (côte 2x)
        - exact 7: Gagner si le total est = 7 (côte 6x)
        """

        # Vérifier le cooldown
        can_play, remaining = check_cooldown(interaction.user.id, "dice")
        if not can_play:
            await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans {remaining:.1f}s")
            return

        prediction = prediction.lower()

        if prediction not in ['over', 'under', 'exact', 'o', 'u', 'e']:
            await interaction.response.send_message("❌ Prédiction invalide! Utilise: `over`, `under` ou `exact`")
            return

        # Normaliser
        if prediction == 'o':
            prediction = 'over'
        elif prediction == 'u':
            prediction = 'under'
        elif prediction == 'e':
            prediction = 'exact'

        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif!")
            return

        if montant > MAX_BET_AMOUNT:
            await interaction.response.send_message(f"❌ La mise maximum est de {MAX_BET_AMOUNT} {CURRENCY_NAME}s!")
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        if profile['balance'] < montant:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de {CURRENCY_NAME}s! (Tu as: {profile['balance']:,})")
            return

        # Lancer les dés
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2

        # Animation
        embed = discord.Embed(
            title="🎲 Lancement des dés...",
            description=f"{interaction.user.mention} lance 2 dés!\n\n🎲 🎲",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        await asyncio.sleep(2)

        # Vérifier le résultat
        won = False
        multiplier = 0

        if prediction == 'over' and total > 7:
            won = True
            multiplier = 2.0
        elif prediction == 'under' and total < 7:
            won = True
            multiplier = 2.0
        elif prediction == 'exact' and total == 7:
            won = True
            multiplier = 6.0

        # Calculs
        if won:
            winnings = int(montant * multiplier)
            # Appliquer la limite de gain maximum
            if winnings > MAX_WIN_AMOUNT:
                winnings = MAX_WIN_AMOUNT
            profit = winnings - montant
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, profit, "dice win")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] + profit,
                games_won=profile['games_won'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance
            color = discord.Color.green()
            title = "🎉 Gagné!"
        else:
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "dice loss")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] - montant,
                games_lost=profile['games_lost'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance
            color = discord.Color.red()
            title = "💔 Perdu!"

        # XP
        xp_gain = 20 if won else 5
        leveled_up = add_xp(interaction.user.id, interaction.guild.id, xp_gain)
        if leveled_up:
            profile = get_user_profile(interaction.user.id, interaction.guild.id)
        # Emoji pour les dés
        dice_emoji = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

        # Résultat
        embed = discord.Embed(
            title=title,
            description=f"**Dés:** {dice_emoji[dice1]} {dice_emoji[dice2]}\n**Total:** {total}\n**Tu as parié:** {prediction.upper()} 7",
            color=color
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
    await bot.add_cog(Dice(bot))
