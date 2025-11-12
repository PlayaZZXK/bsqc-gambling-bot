import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp, check_cooldown, MAX_BET_AMOUNT, MAX_WIN_AMOUNT
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
    async def wheel(self, interaction: discord.Interaction, montant: int):
        """Roue de la fortune! 🎡"""

        # Vérifier le cooldown
        can_play, remaining = check_cooldown(interaction.user.id, "wheel")
        if not can_play:
            await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans {remaining:.1f}s")
            return

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        if montant > MAX_BET_AMOUNT:
            await interaction.response.send_message(f"❌ La mise maximum est de {MAX_BET_AMOUNT} {CURRENCY_NAME}s!")
            return

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
            winnings = int(montant * multiplier)
            # Appliquer la limite de gain maximum
            if winnings > MAX_WIN_AMOUNT:
                winnings = MAX_WIN_AMOUNT
            profit = winnings - montant
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, profit, "wheel win")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] + profit,
                games_won=profile['games_won'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance
            xp_gain = int(15 * multiplier)
        else:
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "wheel loss")
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

        won = multiplier > 0
        profit = winnings - montant if won else -montant
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
