import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp, check_cooldown, MAX_BET_AMOUNT, MAX_WIN_AMOUNT
from database import db

class Plinko(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.multipliers = [0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 5.0, 2.0, 1.0, 0.5, 0.2]

    @app_commands.command(name='plinko', description='Jeu Plinko! La balle tombe!')
    @app_commands.describe(montant='Le montant à miser')
    async def plinko(self, interaction: discord.Interaction, montant: int):
        """Jeu Plinko! 🎯 La balle tombe!"""

        # Vérifier le cooldown
        can_play, remaining = check_cooldown(interaction.user.id, "plinko")
        if not can_play:
            return await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans {remaining:.1f}s")

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        if montant > MAX_BET_AMOUNT:
            return await interaction.response.send_message(f"❌ La mise maximum est de {MAX_BET_AMOUNT} {CURRENCY_NAME}s!")

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
        # Appliquer la limite de gain maximum
        if winnings > MAX_WIN_AMOUNT:
            winnings = MAX_WIN_AMOUNT
        profit = winnings - montant
        won = multiplier > 1.0

        if won:
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, profit, "plinko win")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] + profit,
                games_won=profile['games_won'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance
        else:
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "plinko loss")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] - montant,
                games_lost=profile['games_lost'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance

        add_xp(interaction.user.id, interaction.guild.id, 15)
        slots_display = "".join([f"[**×{m}**]" if i == slot else f"[×{m}]" for i, m in enumerate(self.multipliers)])

        embed = discord.Embed(
            title="🎯 Plinko - Résultat!",
            description=f"{slots_display}\n\n**Multiplicateur: ×{multiplier}**",
            color=discord.Color.green() if won else discord.Color.red()
        )
        embed.add_field(name="Gain/Perte", value=f"{'+' if profit >= 0 else ''}{profit:,} {CURRENCY_NAME}s")
        embed.add_field(name="Solde", value=f"{profile['balance']:,}")

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Plinko(bot))
