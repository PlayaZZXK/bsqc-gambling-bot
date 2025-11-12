import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp, check_cooldown, MAX_BET_AMOUNT
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
    async def duel(self, interaction: discord.Interaction, opponent: discord.Member, montant: int):
        """Défier quelqu'un en coinflip! 🪙 Gagnant prend tout!"""

        # Vérifier le cooldown
        can_play, remaining = check_cooldown(interaction.user.id, "duel")
        if not can_play:
            return await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans {remaining:.1f}s")

        if opponent.bot:
            return await interaction.response.send_message("❌ Tu ne peux pas défier un bot!")

        if opponent.id == interaction.user.id:
            return await interaction.response.send_message("❌ Tu ne peux pas te défier toi-même!")

        if montant <= 0:
            return await interaction.response.send_message("❌ Montant invalide!")

        if montant > MAX_BET_AMOUNT:
            return await interaction.response.send_message(f"❌ La mise maximum est de {MAX_BET_AMOUNT} {CURRENCY_NAME}s!")

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
            db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "duel bet")
            db.modify_balance(opponent.id, interaction.guild.id, -montant, "duel bet")
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

            # Distribuer les gains - le gagnant reçoit le total pot (sa mise + la mise du perdant)
            total_pot = montant * 2
            profit = montant  # Le gagnant gagne la mise de l'adversaire

            # Mise à jour gagnant
            new_winner_balance = db.modify_balance(winner.id, interaction.guild.id, total_pot, "duel win")
            winner_profile = get_user_profile(winner.id, interaction.guild.id)
            db.update_user_profile(
                winner.id,
                interaction.guild.id,
                gambling_profit=winner_profile['gambling_profit'] + profit,
                games_won=winner_profile['games_won'] + 1,
                games_played=winner_profile['games_played'] + 1,
                total_wagered=winner_profile['total_wagered'] + montant
            )

            # Mise à jour perdant
            loser_profile = get_user_profile(loser.id, interaction.guild.id)
            db.update_user_profile(
                loser.id,
                interaction.guild.id,
                gambling_profit=loser_profile['gambling_profit'] - montant,
                games_lost=loser_profile['games_lost'] + 1,
                games_played=loser_profile['games_played'] + 1,
                total_wagered=loser_profile['total_wagered'] + montant
            )

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
