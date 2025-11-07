import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta
import json
import os
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, add_xp
from database import db

# Charger les données de loterie
def load_lottery_data():
    if os.path.exists('data/lottery.json'):
        try:
            with open('data/lottery.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"pot": 0, "tickets": {}, "draw_time": None}

# Sauvegarder les données de loterie
def save_lottery_data():
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/lottery.json', 'w', encoding='utf-8') as f:
            json.dump(lottery_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Erreur sauvegarde loterie: {e}")

lottery_data = load_lottery_data()
print(f"✅ Loterie chargée: {lottery_data['pot']} Skulls, {len(lottery_data['tickets'])} tickets")

class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_price = 100

    @app_commands.command(name='lottery', description='Voir les infos de la loterie!')
    async def lottery_info(self, interaction: discord.Interaction):
        """Voir les infos de la loterie! 🎫"""

        embed = discord.Embed(title="🎫 Loterie du Serveur", color=discord.Color.gold())
        embed.add_field(name="💰 Jackpot", value=f"{lottery_data['pot']:,} {CURRENCY_NAME}s", inline=True)
        embed.add_field(name="🎟️ Tickets vendus", value=str(len(lottery_data['tickets'])), inline=True)
        embed.add_field(name="💵 Prix du ticket", value=f"{self.ticket_price} {CURRENCY_NAME}s", inline=True)

        if lottery_data['draw_time']:
            draw_time = datetime.fromisoformat(lottery_data['draw_time'])
            embed.add_field(name="⏰ Prochain tirage", value=draw_time.strftime("%H:%M"), inline=False)
        else:
            embed.add_field(name="ℹ️ Tirage", value="Automatique toutes les 24h", inline=False)

        embed.set_footer(text="Utilise /buyticket pour acheter un ticket!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='buyticket', description='Acheter un ticket de loterie!')
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    async def buy_ticket(self, interaction: discord.Interaction):
        """Acheter un ticket de loterie! 🎫"""

        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        if profile['balance'] < self.ticket_price:
            return await interaction.response.send_message(f"❌ Pas assez de {CURRENCY_NAME}s! (Coût: {self.ticket_price})")

        if str(interaction.user.id) in lottery_data['tickets']:
            return await interaction.response.send_message("❌ Tu as déjà un ticket pour ce tirage!")

        profile['balance'] -= self.ticket_price
        lottery_data['tickets'][str(interaction.user.id)] = interaction.user.display_name
        lottery_data['pot'] += self.ticket_price

        if not lottery_data['draw_time']:
            lottery_data['draw_time'] = (datetime.now() + timedelta(hours=24)).isoformat()
save_lottery_data()

        embed = discord.Embed(
            title="🎫 Ticket Acheté!"
            description=f"Ton ticket pour la loterie a été acheté!\n\n**Jackpot actuel:** {lottery_data['pot']:,} {CURRENCY_NAME}s"
            color=discord.Color.green()
        )
        embed.add_field(name="Tickets totaux", value=str(len(lottery_data['tickets'])))

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='drawlottery', description='Tirer au sort le gagnant! (Admin seulement)')
    @app_commands.checks.has_permissions(administrator=True)
    async def draw_lottery(self, interaction: discord.Interaction):
        """Tirer au sort le gagnant! (Admin seulement)"""

        if not lottery_data['tickets']:
            return await interaction.response.send_message("❌ Aucun ticket vendu!")

        winner_id = random.choice(list(lottery_data['tickets'].keys()))
        winner = await self.bot.fetch_user(int(winner_id))

        profile = get_user_profile(int(winner_id), interaction.guild.id)
        profile['balance'] += lottery_data['pot']
        profile['gambling_profit'] += (lottery_data['pot'] - self.ticket_price)
save_lottery_data()

        embed = discord.Embed(
            title="🎉 GAGNANT DE LA LOTERIE!"
            description=f"**{winner.mention}** a gagné **{lottery_data['pot']:,} {CURRENCY_NAME}s**!"
            color=discord.Color.gold()
        )
        embed.add_field(name="Tickets participants", value=str(len(lottery_data['tickets'])))
        embed.set_thumbnail(url=winner.display_avatar.url)

        await interaction.response.send_message(embed=embed)

        # Reset
        lottery_data['pot'] = 0
        lottery_data['tickets'] = {}
        lottery_data['draw_time'] = None
        save_lottery_data()

    # Groupe de commandes setlottery
    setlottery_group = app_commands.Group(name="setlottery", description="Configurer la loterie (Admin)")

    @setlottery_group.command(name='price', description='Définir le prix du ticket de loterie')
    @app_commands.describe(price='Le nouveau prix du ticket')
    @app_commands.checks.has_permissions(administrator=True)
    async def setlottery_price(self, interaction: discord.Interaction, price: int):
        """Définir le prix du ticket de loterie"""

        if price <= 0:
            return await interaction.response.send_message("❌ Le prix doit être positif!")

        self.ticket_price = price
        save_lottery_data()

        embed = discord.Embed(
            title="✅ Prix du ticket modifié!"
            description=f"Le nouveau prix du ticket de loterie est: **{price:,} {CURRENCY_NAME}s**"
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    @setlottery_group.command(name='jackpot', description='Définir le jackpot de la loterie')
    @app_commands.describe(montant='Le montant du jackpot à définir')
    @app_commands.checks.has_permissions(administrator=True)
    async def setlottery_jackpot(self, interaction: discord.Interaction, montant: int):
        """Définir le jackpot de la loterie"""

        if montant < 0:
            return await interaction.response.send_message("❌ Le jackpot doit être positif ou nul!")

        old_pot = lottery_data['pot']
        lottery_data['pot'] = montant
        save_lottery_data()

        embed = discord.Embed(
            title="✅ Jackpot modifié!"
            description=f"**Ancien jackpot:** {old_pot:,} {CURRENCY_NAME}s\n**Nouveau jackpot:** {montant:,} {CURRENCY_NAME}s"
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)

    @setlottery_group.command(name='reset', description='Réinitialiser complètement la loterie')
    @app_commands.checks.has_permissions(administrator=True)
    async def setlottery_reset(self, interaction: discord.Interaction):
        """Réinitialiser complètement la loterie"""

        old_pot = lottery_data['pot']
        old_tickets = len(lottery_data['tickets'])

        # Reset complet
        lottery_data['pot'] = 0
        lottery_data['tickets'] = {}
        lottery_data['draw_time'] = None
        save_lottery_data()

        embed = discord.Embed(
            title="🔄 Loterie réinitialisée!"
            description=f"**Ancien jackpot:** {old_pot:,} {CURRENCY_NAME}s\n**Anciens tickets:** {old_tickets}\n\nLa loterie a été complètement réinitialisée!"
            color=discord.Color.orange()
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Lottery(bot))
