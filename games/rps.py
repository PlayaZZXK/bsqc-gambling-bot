import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp, check_cooldown, MAX_BET_AMOUNT, MAX_WIN_AMOUNT
from database import db

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='rps', description='Pierre, Papier, Ciseaux!')
    @app_commands.describe(
        choix='Ton choix: rock/paper/scissors',
        montant='Le montant à miser'
    )
    async def rps(self, interaction: discord.Interaction, choix: str, montant: int):
        """Pierre, Papier, Ciseaux! ✊✋✌️"""

        # Vérifier le cooldown
        can_play, remaining = check_cooldown(interaction.user.id, "rps")
        if not can_play:
            await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans {remaining:.1f}s")
            return

        choix = choix.lower()
        if choix not in ['rock', 'paper', 'scissors', 'pierre', 'papier', 'ciseaux', 'r', 'p', 's']:
            return await interaction.response.send_message("❌ Choix invalide! (rock/paper/scissors)")

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        if montant > MAX_BET_AMOUNT:
            await interaction.response.send_message(f"❌ La mise maximum est de {MAX_BET_AMOUNT} {CURRENCY_NAME}s!")
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s!")

        choices_map = {
            'rock': '✊', 'pierre': '✊', 'r': '✊',
            'paper': '✋', 'papier': '✋', 'p': '✋',
            'scissors': '✌️', 'ciseaux': '✌️', 's': '✌️'
        }

        player_choice = choices_map[choix]
        bot_choice = random.choice(['✊', '✋', '✌️'])

        embed = discord.Embed(title="✊✋✌️ RPS", description=f"Tu joues: {player_choice}\nBot joue: ?", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(1.5)

        result = None
        if player_choice == bot_choice:
            result = "tie"
        elif (player_choice == '✊' and bot_choice == '✌️') or \
             (player_choice == '✋' and bot_choice == '✊') or \
             (player_choice == '✌️' and bot_choice == '✋'):
            result = "win"
        else:
            result = "lose"

        if result == "win":
            winnings = montant * 2
            # Appliquer la limite de gain maximum
            if winnings > MAX_WIN_AMOUNT:
                winnings = MAX_WIN_AMOUNT
            profit = winnings - montant
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, profit, "rps win")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] + profit,
                games_won=profile['games_won'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance
            title = "🎉 Tu gagnes!"
            color = discord.Color.green()
            xp_gain = 15
        elif result == "lose":
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "rps loss")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] - montant,
                games_lost=profile['games_lost'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            profile['balance'] = new_balance
            title = "💔 Tu perds!"
            color = discord.Color.red()
            xp_gain = 5
        else:
            # Égalité - pas de changement de balance
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            title = "🤝 Égalité!"
            color = discord.Color.orange()
            xp_gain = 5

        leveled_up = add_xp(interaction.user.id, interaction.guild.id, xp_gain)
        if leveled_up:
            profile = get_user_profile(interaction.user.id, interaction.guild.id)

        embed = discord.Embed(
            title=title,
            description=f"**Toi:** {player_choice}\n**Bot:** {bot_choice}",
            color=color
        )

        if result != "tie":
            embed.add_field(name="Résultat", value=f"{'+' if result == 'win' else '-'}{profit if result == 'win' else montant:,} {CURRENCY_NAME}s")

        embed.add_field(name="Solde", value=f"{profile['balance']:,}")

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(RPS(bot))
