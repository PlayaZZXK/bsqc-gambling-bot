import discord
from discord import app_commands
from discord.ext import commands
import random
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp
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
                    title="💎 Mines"
                    description=f"**Cases révélées:** {len(self.revealed)}\n**Multiplicateur:** {multiplier:.2f}x\n**Gain potentiel:** {int(self.amount * multiplier):,} {CURRENCY_NAME}s"
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

        self.profile['gambling_profit'] -= self.amount
        self.profile['games_lost'] += 1
        self.profile['games_played'] += 1
embed = discord.Embed(title="💥 BOOM!", description=f"Perte: -{self.amount:,} {CURRENCY_NAME}s", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def cashout(self, interaction: discord.Interaction):
        if interaction.user != self.interaction.user or self.game_over:
            return

        self.game_over = True
        multiplier = 1 + (len(self.revealed) * 0.3)
        winnings = int(self.amount * multiplier)
        profit = winnings - self.amount

        self.profile['balance'] += profit
        self.profile['gambling_profit'] += profit
        self.profile['games_won'] += 1
        self.profile['games_played'] += 1
        add_xp(self.interaction.user.id, self.interaction.guild.id, 20)
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
        montant='Le montant à miser'
        num_mines='Nombre de mines (1-20, défaut: 5)'
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def mines(self, interaction: discord.Interaction, montant: int, num_mines: int = 5):
        """Jeu Mines! 💣 Évite les bombes!"""

        if montant <= 0 or num_mines < 1 or num_mines > 20:
            return await interaction.response.send_message("❌ Montant/mines invalide!")

        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < montant:
            return await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s!")

        profile['balance'] -= montant
        profile['total_wagered'] += montant
view = MinesView(interaction, montant, profile, num_mines)
        embed = discord.Embed(title="💣 Mines", description=f"Évite les {num_mines} bombes!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Mines(bot))
