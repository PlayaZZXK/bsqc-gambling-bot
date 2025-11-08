import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp
from database import db

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='rps', description='Pierre, Papier, Ciseaux!')
    @app_commands.describe(
        choix='Ton choix: rock/paper/scissors',
        montant='Le montant à miser'
    )
    @app_commands.checks.cooldown(1, 3, key=lambda i: i.user.id)
    async def rps(self, interaction: discord.Interaction, choix: str, montant: int):
        """Pierre, Papier, Ciseaux! ✊✋✌️"""

        choix = choix.lower()
        if choix not in ['rock', 'paper', 'scissors', 'pierre', 'papier', 'ciseaux', 'r', 'p', 's']:
            return await interaction.response.send_message("❌ Choix invalide! (rock/paper/scissors)")

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

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
            profit = montant
            profile['balance'] += profit
            profile['gambling_profit'] += profit
            profile['games_won'] += 1
            title = "🎉 Tu gagnes!"
            color = discord.Color.green()
        elif result == "lose":
            profile['balance'] -= montant
            profile['gambling_profit'] -= montant
            profile['games_lost'] += 1
            title = "💔 Tu perds!"
            color = discord.Color.red()
        else:
            title = "🤝 Égalité!"
            color = discord.Color.orange()

        profile['games_played'] += 1
        profile['total_wagered'] += montant
        add_xp(interaction.user.id, interaction.guild.id, 15 if result == "win" else 5)
        embed = discord.Embed(
            title=title,
            description=f"**Toi:** {player_choice}\n**Bot:** {bot_choice}",
            color=color
        )

        if result != "tie":
            embed.add_field(name="Résultat", value=f"{'+' if result == 'win' else '-'}{montant:,} {CURRENCY_NAME}s")

        embed.add_field(name="Solde", value=f"{profile['balance']:,}")

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(RPS(bot))
