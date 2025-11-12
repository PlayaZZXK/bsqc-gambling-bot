import discord
from discord import app_commands
from discord.ext import commands
import random
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp, check_cooldown, MAX_BET_AMOUNT, MAX_WIN_AMOUNT
from database import db

class MinesView(discord.ui.View):
    def __init__(self, interaction, amount, profile, num_mines=5):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.amount = amount
        self.profile = profile
        self.grid_size = 25
        self.num_mines = num_mines
        self.revealed = []
        self.mines = random.sample(range(self.grid_size), num_mines)
        self.game_over = False

        for i in range(min(25, self.grid_size)):
            button = discord.ui.Button(label="❓", style=discord.ButtonStyle.secondary, custom_id=str(i), row=i//5)
            button.callback = self.create_callback(i)
            self.add_item(button)

        cashout = discord.ui.Button(label="💰 Cash Out", style=discord.ButtonStyle.success, row=4)
        cashout.callback = self.cashout
        self.add_item(cashout)

    def create_callback(self, pos):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.interaction.user or self.game_over:
                return await interaction.response.send_message("❌ Ce n'est pas ton jeu!", ephemeral=True)

            if pos in self.revealed:
                return await interaction.response.send_message("❌ Déjà révélé!", ephemeral=True)

            self.revealed.append(pos)

            if pos in self.mines:
                await self.explode(interaction)
            else:
                multiplier = 1 + (len(self.revealed) * 0.3)
                self.children[pos].label = "💎"
                self.children[pos].style = discord.ButtonStyle.success
                self.children[pos].disabled = True

                embed = discord.Embed(
                    title="💎 Mines",
                    description=f"**Cases révélées:** {len(self.revealed)}\n**Multiplicateur:** {multiplier:.2f}x\n**Gain potentiel:** {int(self.amount * multiplier):,} {CURRENCY_NAME}s",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=self)

        return callback

    async def explode(self, interaction):
        self.game_over = True
        for i, item in enumerate(self.children[:-1]):
            if i in self.mines:
                item.label = "💣"
                item.style = discord.ButtonStyle.danger
            item.disabled = True
        self.children[-1].disabled = True

        # Sauvegarder la perte dans la base de données
        new_balance = db.modify_balance(self.interaction.user.id, self.interaction.guild.id, -self.amount, "mines loss")
        db.update_user_profile(
            self.interaction.user.id,
            self.interaction.guild.id,
            gambling_profit=self.profile['gambling_profit'] - self.amount,
            games_lost=self.profile['games_lost'] + 1,
            games_played=self.profile['games_played'] + 1,
            total_wagered=self.profile['total_wagered'] + self.amount
        )
        self.profile['balance'] = new_balance

        leveled_up = add_xp(self.interaction.user.id, self.interaction.guild.id, 5)
        if leveled_up:
            self.profile = get_user_profile(self.interaction.user.id, self.interaction.guild.id)

        embed = discord.Embed(title="💥 BOOM!", description=f"Perte: -{self.amount:,} {CURRENCY_NAME}s", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def cashout(self, interaction: discord.Interaction):
        if interaction.user != self.interaction.user or self.game_over:
            return

        self.game_over = True
        multiplier = 1 + (len(self.revealed) * 0.3)
        winnings = int(self.amount * multiplier)
        # Appliquer la limite de gain maximum
        if winnings > MAX_WIN_AMOUNT:
            winnings = MAX_WIN_AMOUNT
        profit = winnings - self.amount

        # Sauvegarder le gain dans la base de données
        new_balance = db.modify_balance(self.interaction.user.id, self.interaction.guild.id, profit, "mines win")
        db.update_user_profile(
            self.interaction.user.id,
            self.interaction.guild.id,
            gambling_profit=self.profile['gambling_profit'] + profit,
            games_won=self.profile['games_won'] + 1,
            games_played=self.profile['games_played'] + 1,
            total_wagered=self.profile['total_wagered'] + self.amount
        )
        self.profile['balance'] = new_balance

        leveled_up = add_xp(self.interaction.user.id, self.interaction.guild.id, 20)
        if leveled_up:
            self.profile = get_user_profile(self.interaction.user.id, self.interaction.guild.id)

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(title="💰 Cash Out!", description=f"Gain: +{profit:,} {CURRENCY_NAME}s", color=discord.Color.gold())
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

class Mines(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='mines', description='Jeu Mines! Évite les bombes!')
    @app_commands.describe(
        montant='Le montant à miser',
        num_mines='Nombre de mines (1-20, défaut: 5)'
    )
    async def mines(self, interaction: discord.Interaction, montant: int, num_mines: int = 5):
        """Jeu Mines! 💣 Évite les bombes!"""

        # Vérifier le cooldown
        can_play, remaining = check_cooldown(interaction.user.id, "mines")
        if not can_play:
            await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans {remaining:.1f}s")
            return

        if montant <= 0 or num_mines < 1 or num_mines > 20:
            return await interaction.response.send_message("❌ Montant/mines invalide!")

        if montant > MAX_BET_AMOUNT:
            await interaction.response.send_message(f"❌ La mise maximum est de {MAX_BET_AMOUNT} {CURRENCY_NAME}s!")
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s!")

        # Déduire la mise du solde immédiatement
        new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "mines bet")
        profile['balance'] = new_balance
        view = MinesView(interaction, montant, profile, num_mines)
        embed = discord.Embed(title="💣 Mines", description=f"Évite les {num_mines} bombes!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Mines(bot))
