import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp, check_cooldown, MAX_BET_AMOUNT, MAX_WIN_AMOUNT
from database import db

class Cups(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='cups', description='Jeu des gobelets!')
    @app_commands.describe(
        choix='Ton choix: 1, 2 ou 3',
        montant='Le montant à miser'
    )
    async def cups(self, interaction: discord.Interaction, choix: int, montant: int):
        """Jeu des gobelets! 🥤 Choisis 1, 2 ou 3"""

        # Vérifier le cooldown
        can_play, remaining = check_cooldown(interaction.user.id, "cups")
        if not can_play:
            await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans {remaining:.1f}s")
            return

        if choix not in [1, 2, 3]:
            return await interaction.response.send_message("❌ Choisis 1, 2 ou 3!")

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        if montant > MAX_BET_AMOUNT:
            await interaction.response.send_message(f"❌ La mise maximum est de {MAX_BET_AMOUNT} {CURRENCY_NAME}s!")
            return

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
            winnings = montant * 2
            # Appliquer la limite de gain maximum
            if winnings > MAX_WIN_AMOUNT:
                winnings = MAX_WIN_AMOUNT
            profit = winnings - montant
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, profit, "cups win")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] + profit,
                games_won=profile['games_won'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance
            xp_gain = 20
        else:
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "cups loss")
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
            description=f"{' '.join(cups_display)}\n\n**La balle était sous le gobelet {winning_cup}!**",
            color=discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Résultat", value=f"{'+' if won else '-'}{profit if won else montant:,} {CURRENCY_NAME}s")
        embed.add_field(name="Solde", value=f"{profile['balance']:,}")

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Cups(bot))
