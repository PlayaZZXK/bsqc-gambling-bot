import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp, check_cooldown, MAX_BET_AMOUNT, MAX_WIN_AMOUNT
from database import db

class CrashView(discord.ui.View):
    def __init__(self, interaction, amount, profile):
        super().__init__(timeout=30)
        self.interaction = interaction
        self.amount = amount
        self.profile = profile
        self.multiplier = 1.00
        self.crashed = False
        self.cashed_out = False

    @discord.ui.button(label="💰 Cash Out", style=discord.ButtonStyle.success)
    async def cashout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user or self.cashed_out or self.crashed:
            await interaction.response.send_message("❌ Ce n'est pas ton jeu!", ephemeral=True)
            return

        self.cashed_out = True
        for item in self.children:
            item.disabled = True

        winnings = int(self.amount * self.multiplier)
        # Appliquer la limite de gain maximum
        if winnings > MAX_WIN_AMOUNT:
            winnings = MAX_WIN_AMOUNT
        profit = winnings - self.amount

        new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, profit, "crash win")
        db.update_user_profile(
            interaction.user.id,
            interaction.guild.id,
            gambling_profit=self.profile['gambling_profit'] + profit,
            games_won=self.profile['games_won'] + 1,
            games_played=self.profile['games_played'] + 1,
            total_wagered=self.profile['total_wagered'] + self.amount
        )
        self.profile['balance'] = new_balance

        add_xp(self.interaction.user.id, self.interaction.guild.id, int(20 * self.multiplier))
        embed = discord.Embed(
            title="💰 Cash Out Réussi!",
            description=f"**Multiplicateur:** {self.multiplier:.2f}x\n**Gain:** +{profit:,} {CURRENCY_NAME}s",
            color=discord.Color.green()
        )
        embed.add_field(name="Nouveau solde", value=f"{self.profile['balance']:,} {CURRENCY_NAME}s")

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

class Crash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='crash', description='Jeu Crash! Cash out avant le crash!')
    @app_commands.describe(montant='Le montant à miser')
    async def crash(self, interaction: discord.Interaction, montant: int):
        """
        Jeu Crash! 🚀

        Le multiplicateur monte, cash out avant le crash!
        Plus tu attends, plus tu gagnes... ou perds tout!
        """

        # Vérifier le cooldown
        can_play, remaining = check_cooldown(interaction.user.id, "crash")
        if not can_play:
            await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans {remaining:.1f}s")
            return

        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif!")
            return

        if montant > MAX_BET_AMOUNT:
            await interaction.response.send_message(f"❌ La mise maximum est de {MAX_BET_AMOUNT} {CURRENCY_NAME}s!")
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        if profile['balance'] < montant:
            await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s!")
            return

        db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "crash bet")
        profile['balance'] -= montant
        view = CrashView(interaction, montant, profile)

        # Point de crash aléatoire
        crash_point = random.uniform(1.01, 10.0)

        embed = discord.Embed(title="🚀 CRASH", description=f"**Multiplicateur:** 1.00x", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

        while view.multiplier < crash_point and not view.cashed_out:
            await asyncio.sleep(1.5)
            view.multiplier += random.uniform(0.05, 0.30)

            if view.multiplier >= crash_point:
                break

            embed.description = f"**Multiplicateur:** {view.multiplier:.2f}x 🚀"
            try:
                await message.edit(embed=embed, view=view)
            except:
                break

        if not view.cashed_out:
            view.crashed = True
            for item in view.children:
                item.disabled = True

            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] - montant,
                games_lost=profile['games_lost'] + 1,
                games_played=profile['games_played'] + 1,
                total_wagered=profile['total_wagered'] + montant
            )
            embed = discord.Embed(
                title="💥 CRASH!",
                description=f"**Crash à:** {crash_point:.2f}x\n**Perte:** -{montant:,} {CURRENCY_NAME}s",
                color=discord.Color.red()
            )
            await message.edit(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Crash(bot))
