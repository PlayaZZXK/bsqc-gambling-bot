import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp
from database import db

active_duels = {}

class CoinflipPvP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='duel', description='Défier quelqu\'un en coinflip!')
    @app_commands.describe(
        opponent='Le joueur à défier',
        montant='Le montant à miser'
    )
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.user.id)
    async def duel(self, interaction: discord.Interaction, opponent: discord.Member, montant: int):
        """Défier quelqu'un en coinflip! 🪙 Gagnant prend tout!"""

        if opponent.bot:
            return await interaction.response.send_message("❌ Tu ne peux pas défier un bot!")

        if opponent.id == interaction.user.id:
            return await interaction.response.send_message("❌ Tu ne peux pas te défier toi-même!")

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        challenger_profile = get_user_profile(interaction.user.id, interaction.guild.id)
        opponent_profile = get_user_profile(opponent.id, interaction.guild.id)

        if challenger_profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ Tu n'as pas assez de {CURRENCY_NAME}s!")

        if opponent_profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ {opponent.mention} n'a pas assez de {CURRENCY_NAME}s!")

        if interaction.user.id in active_duels or opponent.id in active_duels:
            return await interaction.response.send_message("❌ Un des joueurs est déjà en duel!")

        # Créer le duel
        duel_id = f"{interaction.user.id}_{opponent.id}"
        active_duels[interaction.user.id] = duel_id
        active_duels[opponent.id] = duel_id

        embed = discord.Embed(
            title="⚔️ Défi Coinflip!",
            description=f"{interaction.user.mention} défie {opponent.mention}!\n\n**Mise:** {montant:,} {CURRENCY_NAME}s\n\n{opponent.mention}, réagis avec ✅ pour accepter (30s)",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return user == opponent and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

            if str(reaction.emoji) == "❌":
                del active_duels[interaction.user.id]
                del active_duels[opponent.id]
                return await interaction.followup.send(f"❌ {opponent.mention} a refusé le duel!")

            # Déduire les mises
            challenger_profile['balance'] -= montant
            opponent_profile['balance'] -= montant
            # Lancer la pièce
            embed = discord.Embed(
                title="🪙 Coinflip Duel!",
                description="La pièce est lancée...\n\n💫",
                color=discord.Color.blue()
            )
            await msg.edit(embed=embed)
            await asyncio.sleep(2)

            winner = random.choice([interaction.user, opponent])
            loser = opponent if winner == interaction.user else interaction.user

            winner_profile = get_user_profile(winner.id, interaction.guild.id)
            loser_profile = get_user_profile(loser.id, interaction.guild.id)

            # Distribuer les gains
            total_pot = montant * 2
            winner_profile['balance'] += total_pot
            winner_profile['gambling_profit'] += montant
            winner_profile['games_won'] += 1

            loser_profile['gambling_profit'] -= montant
            loser_profile['games_lost'] += 1

            winner_profile['games_played'] += 1
            loser_profile['games_played'] += 1

            add_xp(winner.id, interaction.guild.id, 30)
            add_xp(loser.id, interaction.guild.id, 10)
            embed = discord.Embed(
                title="🏆 Victoire!",
                description=f"**{winner.mention} a gagné le duel!**\n\n💰 Gains: {total_pot:,} {CURRENCY_NAME}s\n💔 {loser.mention} perd {montant:,} {CURRENCY_NAME}s",
                color=discord.Color.gold()
            )

            await msg.edit(embed=embed)

            # Nettoyer
            del active_duels[interaction.user.id]
            del active_duels[opponent.id]

        except asyncio.TimeoutError:
            del active_duels[interaction.user.id]
            del active_duels[opponent.id]
            await interaction.followup.send("⏰ Temps écoulé! Duel annulé.")

async def setup(bot):
    await bot.add_cog(CoinflipPvP(bot))
