import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI, add_xp
from database import db

# Stockage des paris actifs
active_bets = {}

class Betting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='createbet', description='Créer un nouveau pari communautaire (Admin seulement)')
    @app_commands.checks.has_permissions(administrator=True)
    async def create_bet(self, interaction: discord.Interaction):
        """Créer un nouveau pari communautaire (Admin seulement) 📋"""

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            # Titre du pari
            await interaction.response.send_message("📋 **Quel est le titre du pari?**\nExemple: `Qui va gagner le match?`")
            title_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            title = title_msg.content

            # Options de pari
            await interaction.followup.send("📝 **Combien d'options de pari? (2-10)**")
            num_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            num_options = int(num_msg.content)

            if num_options < 2 or num_options > 10:
                await interaction.followup.send("❌ Le nombre d'options doit être entre 2 et 10!")
                return

            options = []
            for i in range(num_options):
                # Nom de l'option
                await interaction.followup.send(f"**Option {i+1} - Nom:**\nExemple: `Team A`, `Oui`, etc.")
                option_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                option_name = option_msg.content

                # Côte de l'option
                await interaction.followup.send(f"**Option {i+1} - Côte:**\nExemple: `2.5` (multiplie la mise par 2.5)")
                odds_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                odds = float(odds_msg.content)

                if odds <= 1.0:
                    await interaction.followup.send("❌ La côte doit être supérieure à 1.0!")
                    return

                options.append({"name": option_name, "odds": odds, "bets": {}})

            # Créer le pari
            bet_id = f"{interaction.guild.id}_{datetime.now().timestamp()}"
            active_bets[bet_id] = {
                "title": title,
                "options": options,
                "creator": interaction.user.id,
                "guild": interaction.guild.id,
                "channel": interaction.channel.id,
                "active": True,
                "created_at": datetime.now().isoformat()
            }

            # Afficher le pari
            embed = discord.Embed(
                title=f"🎲 {title}",
                description=f"ID du pari: `{bet_id}`\nCréé par {interaction.user.mention}",
                color=discord.Color.blue()
            )

            for i, option in enumerate(options, 1):
                embed.add_field(
                    name=f"Option {i}: {option['name']}",
                    value=f"**Côte:** {option['odds']}x\n**Parier:** `/placebet {bet_id} {i} <montant>`",
                    inline=False
                )

            embed.set_footer(text="Utilisez /placebet pour parier!")

            await interaction.followup.send(embed=embed)

        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Temps écoulé! Création du pari annulée.")
        except ValueError:
            await interaction.followup.send("❌ Valeur invalide! Création du pari annulée.")

    @app_commands.command(name='placebet', description='Placer un pari sur une option')
    @app_commands.describe(
        bet_id='L\'ID du pari',
        option_num='Le numéro de l\'option sur laquelle parier',
        montant='Le montant à miser'
    )
    async def place_bet(self, interaction: discord.Interaction, bet_id: str, option_num: int, montant: int):
        """Placer un pari sur une option 💰"""

        if bet_id not in active_bets:
            await interaction.response.send_message("❌ Ce pari n'existe pas!")
            return

        bet = active_bets[bet_id]

        if not bet['active']:
            await interaction.response.send_message("❌ Ce pari est fermé!")
            return

        if option_num < 1 or option_num > len(bet['options']):
            await interaction.response.send_message(f"❌ Option invalide! Choisis entre 1 et {len(bet['options'])}")
            return

        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif!")
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        if profile['balance'] < montant:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de {CURRENCY_NAME}s! (Tu as: {profile['balance']:,})")
            return

        # Placer le pari
        option = bet['options'][option_num - 1]
        user_id = str(interaction.user.id)

        if user_id in option['bets']:
            await interaction.response.send_message("❌ Tu as déjà parié sur cette option!")
            return

        # Déduire la mise
        db.modify_balance(interaction.user.id, interaction.guild.id, -montant, "bet placed")
        option['bets'][user_id] = montant

        potential_win = int(montant * option['odds'])

        embed = discord.Embed(
            title="✅ Pari placé!",
            description=f"**Pari:** {bet['title']}\n**Option:** {option['name']}\n**Mise:** {montant:,} {CURRENCY_NAME}s",
            color=discord.Color.green()
        )
        embed.add_field(name="Gain potentiel", value=f"{potential_win:,} {CURRENCY_NAME}s", inline=True)
        embed.add_field(name="Côte", value=f"{option['odds']}x", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='closebet', description='Fermer un pari et distribuer les gains (Admin seulement)')
    @app_commands.describe(
        bet_id='L\'ID du pari à fermer',
        winning_option='Le numéro de l\'option gagnante'
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def close_bet(self, interaction: discord.Interaction, bet_id: str, winning_option: int):
        """Fermer un pari et distribuer les gains (Admin seulement) 🏆"""

        if bet_id not in active_bets:
            await interaction.response.send_message("❌ Ce pari n'existe pas!")
            return

        bet = active_bets[bet_id]

        if not bet['active']:
            await interaction.response.send_message("❌ Ce pari est déjà fermé!")
            return

        if winning_option < 1 or winning_option > len(bet['options']):
            await interaction.response.send_message(f"❌ Option invalide! Choisis entre 1 et {len(bet['options'])}")
            return

        # Fermer le pari
        bet['active'] = False
        winning_opt = bet['options'][winning_option - 1]

        # Distribuer les gains
        winners = []
        total_distributed = 0

        for user_id, bet_amount in winning_opt['bets'].items():
            profile = get_user_profile(int(user_id), interaction.guild.id)
            winnings = int(bet_amount * winning_opt['odds'])

            # Mise à jour DB
            db.modify_balance(int(user_id), interaction.guild.id, winnings, "bet won")
            db.update_user_profile(
                int(user_id),
                interaction.guild.id,
                gambling_profit=profile['gambling_profit'] + (winnings - bet_amount),
                games_won=profile['games_won'] + 1,
                games_played=profile['games_played'] + 1
            )

            add_xp(int(user_id), interaction.guild.id, 30)

            winners.append((user_id, bet_amount, winnings))
            total_distributed += winnings

        # Mettre à jour les perdants
        for i, option in enumerate(bet['options']):
            if i != winning_option - 1:
                for user_id, bet_amount in option['bets'].items():
                    profile = get_user_profile(int(user_id), interaction.guild.id)
                    db.update_user_profile(
                        int(user_id),
                        interaction.guild.id,
                        gambling_profit=profile['gambling_profit'] - bet_amount,
                        games_lost=profile['games_lost'] + 1,
                        games_played=profile['games_played'] + 1
                    )

        # Annonce des résultats
        embed = discord.Embed(
            title=f"🏆 Résultats du pari",
            description=f"**{bet['title']}**\n\n**Option gagnante:** {winning_opt['name']} ({winning_opt['odds']}x)",
            color=discord.Color.gold()
        )

        if winners:
            winners_text = ""
            for user_id, bet_amount, winnings in winners[:10]:  # Max 10 gagnants affichés
                user = self.bot.get_user(int(user_id))
                username = user.display_name if user else f"User {user_id}"
                profit = winnings - bet_amount
                winners_text += f"**{username}:** Misé {bet_amount:,} → Gagné {winnings:,} (+{profit:,})\n"

            embed.add_field(name=f"🎉 Gagnants ({len(winners)})", value=winners_text or "Aucun", inline=False)
            embed.add_field(name="Total distribué", value=f"{total_distributed:,} {CURRENCY_NAME}s", inline=False)
        else:
            embed.add_field(name="🎉 Gagnants", value="Aucun pari sur l'option gagnante!", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='viewbet', description='Voir les détails d\'un pari actif')
    @app_commands.describe(bet_id='L\'ID du pari à consulter')
    async def view_bet(self, interaction: discord.Interaction, bet_id: str):
        """Voir les détails d'un pari actif 📊"""

        if bet_id not in active_bets:
            await interaction.response.send_message("❌ Ce pari n'existe pas!")
            return

        bet = active_bets[bet_id]

        embed = discord.Embed(
            title=f"🎲 {bet['title']}",
            description=f"ID: `{bet_id}`\nStatut: {'🟢 Actif' if bet['active'] else '🔴 Fermé'}",
            color=discord.Color.blue() if bet['active'] else discord.Color.red()
        )

        for i, option in enumerate(bet['options'], 1):
            total_bet = sum(option['bets'].values())
            num_bettors = len(option['bets'])

            embed.add_field(
                name=f"Option {i}: {option['name']}",
                value=f"**Côte:** {option['odds']}x\n"
                      f"**Parieurs:** {num_bettors}\n"
                      f"**Total misé:** {total_bet:,} {CURRENCY_NAME}s",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='activebets', description='Voir tous les paris actifs du serveur')
    async def active_bets_list(self, interaction: discord.Interaction):
        """Voir tous les paris actifs du serveur 📋"""

        guild_bets = [
            (bet_id, bet) for bet_id, bet in active_bets.items()
            if bet['guild'] == interaction.guild.id and bet['active']
        ]

        if not guild_bets:
            await interaction.response.send_message("❌ Aucun pari actif sur ce serveur!")
            return

        embed = discord.Embed(
            title="📋 Paris Actifs",
            color=discord.Color.blue()
        )

        for bet_id, bet in guild_bets[:10]:  # Max 10 paris
            total_bets = sum(len(opt['bets']) for opt in bet['options'])
            embed.add_field(
                name=bet['title'],
                value=f"ID: `{bet_id}`\n"
                      f"Options: {len(bet['options'])} | Parieurs: {total_bets}\n"
                      f"`/viewbet {bet_id}` pour plus d'infos",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Betting(bot))
