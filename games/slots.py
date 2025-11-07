import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI, add_xp
from database import db

class Slots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Symboles avec leurs multiplicateurs
        self.symbols = {
            '💀': 10,   # Skull - Jackpot!
            '💎': 5,    # Diamant
            '👑': 4,    # Couronne
            '🍒': 3,    # Cerise
            '🍋': 2,    # Citron
            '🔔': 2,    # Cloche
            '7️⃣': 8    # Sept chanceux
        }

    @app_commands.command(name='slots', description='Jouer aux machines à sous!')
    @app_commands.describe(montant='Le montant à miser')
    @app_commands.checks.cooldown(1, 4, key=lambda i: i.user.id)
    async def slots(self, interaction: discord.Interaction, montant: int):
        """
        Jouer aux machines à sous! 🎰

        Multiplicateurs:
        💀 💀 💀 = ×10 (JACKPOT!)
        7️⃣ 7️⃣ 7️⃣ = ×8
        💎 💎 💎 = ×5
        👑 👑 👑 = ×4
        🍒 🍒 🍒 = ×3
        🍋 🍋 🍋 = ×2
        🔔 🔔 🔔 = ×2

        2 symboles identiques = ×1.5
        """

        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif!")
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        if profile['balance'] < montant:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de {CURRENCY_NAME}s! (Tu as: {profile['balance']:,})")
            return

        # Animation
        embed = discord.Embed(
            title="🎰 SLOTS",
            description="Les rouleaux tournent...\n\n🎰 | 🎰 | 🎰",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # Simuler l'animation
        for _ in range(3):
            random_symbols = [random.choice(list(self.symbols.keys())) for _ in range(3)]
            embed.description = f"Les rouleaux tournent...\n\n{' | '.join(random_symbols)}"
            await message.edit(embed=embed)
            await asyncio.sleep(0.6)

        # Résultat final
        result = random.choices(
            list(self.symbols.keys()),
            weights=[5, 15, 15, 25, 25, 25, 10],  # Probabilités
            k=3
        )

        # Calculer les gains
        multiplier = 0
        won = False

        # 3 symboles identiques
        if result[0] == result[1] == result[2]:
            multiplier = self.symbols[result[0]]
            won = True
            win_type = "3 IDENTIQUES!"
        # 2 symboles identiques
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            multiplier = 1.5
            won = True
            win_type = "2 IDENTIQUES!"
        else:
            win_type = "Aucune combinaison"

        # Calculs et mise à jour DB
        if won:
            winnings = int(montant * multiplier)
            profit = winnings - montant
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, profit, "slots win")
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
            title = "🎉 GAGNÉ!"

            # Jackpot spécial
            if result[0] == '💀' and multiplier == 10:
                title = "💀 JACKPOT SKULL! 💀"
                color = discord.Color.purple()
        else:
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "slots loss")
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
            title = "💔 Perdu"

        # XP
        xp_gain = int(25 * multiplier) if won else 5
        leveled_up = add_xp(interaction.user.id, interaction.guild.id, xp_gain)
        if leveled_up:
            profile = get_user_profile(interaction.user.id, interaction.guild.id)

        # Résultat final
        embed = discord.Embed(
            title=title,
            description=f"**{' | '.join(result)}**\n\n{win_type}",
            color=color
        )

        if won:
            embed.add_field(name="Multiplicateur", value=f"×{multiplier}", inline=True)
            embed.add_field(name="Gain", value=f"+{profit:,} {CURRENCY_NAME}s", inline=True)
        else:
            embed.add_field(name="Perte", value=f"-{montant:,} {CURRENCY_NAME}s", inline=True)

        embed.add_field(name="Nouveau solde", value=f"{profile['balance']:,} {CURRENCY_NAME}s", inline=True)

        if leveled_up:
            embed.add_field(name="🎉 Level Up!", value=f"Niveau {profile['level']}!", inline=False)

        await message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Slots(bot))
