import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import sys
import random
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI, add_xp, OWNER_ID, add_balance, MAX_NHL_BET
from database import db

# Dictionnaire pour stocker les résultats prédéfinis des paris
predefined_results = {}

# Rôles autorisés à exécuter les commandes admin
ADMIN_ROLE_IDS = [
    1333483851053535293,
    1333483900537671710,
    1333483947023138826,
    1333483976119287809,
    1345775821893402818
]

# Liste des équipes de la NHL
NHL_TEAMS = [
    "Ducks", "Coyotes", "Bruins", "Sabres", "Flames", "Hurricanes", "Blackhawks",
    "Avalanche", "Blue Jackets", "Stars", "Red Wings", "Oilers", "Panthers",
    "Kings", "Wild", "Canadiens", "Predators", "Devils", "Islanders", "Rangers",
    "Senators", "Flyers", "Penguins", "Sharks", "Kraken", "Blues", "Lightning",
    "Maple Leafs", "Canucks", "Golden Knights", "Capitals"
]

def has_admin_role():
    """Vérifier si l'utilisateur a un des rôles admin autorisés"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id == OWNER_ID:
            return True
        if interaction.guild and hasattr(interaction.user, 'roles'):
            user_role_ids = [role.id for role in interaction.user.roles]
            if any(role_id in ADMIN_ROLE_IDS for role_id in user_role_ids):
                return True
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande!", ephemeral=True)
        return False
    return app_commands.check(predicate)

# Stockage des paris actifs
active_bets = {}

# Stockage de la configuration NHL auto-bet par serveur
nhl_auto_bet_config = {}

class Betting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nhl_auto_bet_task = None

    async def cog_load(self):
        """Démarrer la tâche automatique NHL au chargement du cog"""
        if self.nhl_auto_bet_task is None:
            self.nhl_auto_bet_task = self.bot.loop.create_task(self.nhl_auto_bet_loop())
            print("[NHL AUTO-BET] Système automatique NHL démarré!")

    async def cog_unload(self):
        """Arrêter la tâche automatique NHL au déchargement du cog"""
        if self.nhl_auto_bet_task:
            self.nhl_auto_bet_task.cancel()
            print("[NHL AUTO-BET] Système automatique NHL arrêté!")

    async def nhl_auto_bet_loop(self):
        """Boucle qui crée automatiquement des paris NHL 5h après la fermeture du précédent"""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            try:
                # Créer des paris NHL pour chaque serveur configuré
                for guild_id, config in nhl_auto_bet_config.items():
                    if config.get('enabled', False):
                        await self.create_nhl_auto_bet(guild_id, config)

                # Attendre 20 heures (15h de pari + 5h de pause) avant le prochain pari
                await asyncio.sleep(72000)  # 20 heures = 72000 secondes

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[NHL AUTO-BET ERROR] {e}")
                await asyncio.sleep(3600)  # Attendre 1 heure en cas d'erreur

    async def create_nhl_auto_bet(self, guild_id, config):
        """Créer un pari NHL automatique pour un serveur"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return

            channel_id = config.get('channel_id')
            channel = guild.get_channel(channel_id)
            if not channel:
                return

            # Sélectionner 2 équipes différentes au hasard
            team1, team2 = random.sample(NHL_TEAMS, 2)

            # Générer des cotes aléatoires (entre 1.5 et 3.0)
            odds1 = round(random.uniform(1.5, 3.0), 2)
            odds2 = round(random.uniform(1.5, 3.0), 2)

            # Créer le pari avec durée de 15 heures
            bet_id = f"{guild_id}_nhl_{datetime.now().timestamp()}"
            close_time = datetime.now() + timedelta(hours=15)

            active_bets[bet_id] = {
                "title": "Qui va gagner le match?",
                "options": [
                    {"name": team1, "odds": odds1, "bets": {}},
                    {"name": team2, "odds": odds2, "bets": {}}
                ],
                "creator": self.bot.user.id,
                "guild": guild_id,
                "channel": channel_id,
                "active": True,
                "created_at": datetime.now().isoformat(),
                "close_time": close_time.isoformat(),
                "auto_nhl": True
            }

            # Créer l'embed du pari
            embed = discord.Embed(
                title="🏒 Qui va gagner le match?",
                description=f"**{team1}** vs **{team2}**\n\nID du pari: `{bet_id}`\nFermeture automatique: <t:{int(close_time.timestamp())}:R>",
                color=discord.Color.blue()
            )

            embed.add_field(
                name=f"🔵 {team1}",
                value=f"**Côte:** {odds1}x\n**Parier:** `/placebet {bet_id} 1 <montant>`",
                inline=True
            )

            embed.add_field(
                name=f"🔴 {team2}",
                value=f"**Côte:** {odds2}x\n**Parier:** `/placebet {bet_id} 2 <montant>`",
                inline=True
            )

            embed.set_footer(text=f"🏒 Pari NHL automatique • Fermeture dans 15 heures • Max: {MAX_NHL_BET:,} Skulls")

            await channel.send(embed=embed)

            # Programmer la fermeture automatique après 15 heures
            self.bot.loop.create_task(self.auto_close_nhl_bet(bet_id, 15 * 3600))

            print(f"[NHL AUTO-BET] Pari créé: {team1} vs {team2} dans {guild.name}")

        except Exception as e:
            print(f"[NHL AUTO-BET ERROR] Erreur création pari: {e}")

    async def auto_close_nhl_bet(self, bet_id, delay):
        """Fermer automatiquement un pari NHL après un délai"""
        await asyncio.sleep(delay)

        if bet_id not in active_bets:
            return

        bet = active_bets[bet_id]
        if not bet.get('active', False):
            return

        # Vérifier si un résultat a été prédéfini
        if bet_id in predefined_results:
            winning_option = predefined_results[bet_id]
            del predefined_results[bet_id]  # Nettoyer après utilisation
        else:
            # Choisir un gagnant basé sur les cotes (pondéré)
            # Plus la cote est basse, plus l'équipe a de chances de gagner
            odds1 = bet['options'][0]['odds']
            odds2 = bet['options'][1]['odds']

            # Convertir les cotes en probabilités
            # Probabilité inverse des cotes (cote plus basse = plus probable)
            prob1 = 1 / odds1
            prob2 = 1 / odds2
            total_prob = prob1 + prob2

            # Normaliser les probabilités pour qu'elles totalisent 100%
            prob1_normalized = prob1 / total_prob

            # Tirer au sort avec les probabilités pondérées
            winning_option = 1 if random.random() < prob1_normalized else 2

        # Fermer le pari
        bet['active'] = False
        winning_opt = bet['options'][winning_option - 1]

        guild = self.bot.get_guild(bet['guild'])
        if not guild:
            return

        channel = guild.get_channel(bet['channel'])
        if not channel:
            return

        # Distribuer les gains
        winners = []
        total_distributed = 0

        for user_id, bet_amount in winning_opt['bets'].items():
            profile = get_user_profile(int(user_id), guild.id)
            winnings = int(bet_amount * winning_opt['odds'])

            # Mise à jour DB
            db.modify_balance(int(user_id), guild.id, winnings, "nhl bet won")
            db.update_user_profile(
                int(user_id),
                guild.id,
                gambling_profit=profile['gambling_profit'] + (winnings - bet_amount),
                games_won=profile['games_won'] + 1,
                games_played=profile['games_played'] + 1
            )

            add_xp(int(user_id), guild.id, 30)

            winners.append((user_id, bet_amount, winnings))
            total_distributed += winnings

        # Mettre à jour les perdants
        for i, option in enumerate(bet['options']):
            if i != winning_option - 1:
                for user_id, bet_amount in option['bets'].items():
                    profile = get_user_profile(int(user_id), guild.id)
                    db.update_user_profile(
                        int(user_id),
                        guild.id,
                        gambling_profit=profile['gambling_profit'] - bet_amount,
                        games_lost=profile['games_lost'] + 1,
                        games_played=profile['games_played'] + 1
                    )

        # Annonce des résultats
        team1 = bet['options'][0]['name']
        team2 = bet['options'][1]['name']
        winner_team = winning_opt['name']

        embed = discord.Embed(
            title="🏒 Résultats du match NHL",
            description=f"**{team1}** vs **{team2}**\n\n🏆 **Gagnant:** {winner_team} ({winning_opt['odds']}x)",
            color=discord.Color.gold()
        )

        if winners:
            winners_text = ""
            for user_id, bet_amount, winnings in winners[:10]:  # Max 10 gagnants affichés
                user = self.bot.get_user(int(user_id))
                username = user.display_name if user else f"User {user_id}"
                profit = winnings - bet_amount
                winners_text += f"**{username}:** Misé {bet_amount:,} → Gagné {winnings:,} (+{profit:,})\n"

            embed.add_field(name=f"🎉 Gagnants ({len(winners)})", value=winners_text, inline=False)
            embed.add_field(name="Total distribué", value=f"{total_distributed:,} {CURRENCY_NAME}s", inline=False)
        else:
            embed.add_field(name="🎉 Gagnants", value="Aucun pari sur l'équipe gagnante!", inline=False)

        await channel.send(embed=embed)
        print(f"[NHL AUTO-BET] Pari fermé automatiquement: {winner_team} a gagné!")

    @app_commands.command(name='createbet', description='Créer un nouveau pari communautaire (Admin seulement)')
    @has_admin_role()
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

        # Vérifier la limite NHL si c'est un pari NHL auto
        if bet.get('auto_nhl', False) and montant > MAX_NHL_BET:
            await interaction.response.send_message(f"❌ Pour les paris NHL, la mise maximum est de {MAX_NHL_BET:,} {CURRENCY_NAME}s!")
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
    @has_admin_role()
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

    @app_commands.command(name='setupnhlbet', description='Configurer le système de paris NHL automatiques (Admin seulement)')
    @app_commands.describe(
        channel='Le salon où poster les paris NHL automatiques',
        enabled='Activer ou désactiver le système'
    )
    @has_admin_role()
    async def setup_nhl_bet(self, interaction: discord.Interaction, channel: discord.TextChannel, enabled: bool = True):
        """Configurer le système de paris NHL automatiques 🏒"""

        nhl_auto_bet_config[interaction.guild.id] = {
            'channel_id': channel.id,
            'enabled': enabled
        }

        status = "✅ activé" if enabled else "❌ désactivé"

        embed = discord.Embed(
            title="🏒 Configuration NHL Auto-Bet",
            description=f"Le système de paris NHL automatiques a été {status}!",
            color=discord.Color.green() if enabled else discord.Color.red()
        )

        embed.add_field(name="Salon", value=channel.mention, inline=False)
        embed.add_field(name="Fréquence", value="Toutes les 24 heures", inline=True)
        embed.add_field(name="Durée du pari", value="15 heures", inline=True)
        embed.add_field(
            name="ℹ️ Informations",
            value="Le bot créera automatiquement un pari NHL toutes les 24 heures avec 2 équipes différentes.\n"
                  "Les paris se fermeront automatiquement après 15 heures et le gagnant sera tiré au sort.",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

        # Si activé, créer immédiatement un premier pari
        if enabled:
            await interaction.followup.send("🏒 Création du premier pari NHL dans quelques secondes...")
            await asyncio.sleep(3)
            await self.create_nhl_auto_bet(interaction.guild.id, nhl_auto_bet_config[interaction.guild.id])

    @app_commands.command(name='nhlbetstatus', description='Voir le statut du système de paris NHL automatiques')
    async def nhl_bet_status(self, interaction: discord.Interaction):
        """Voir le statut du système de paris NHL automatiques 📊"""

        config = nhl_auto_bet_config.get(interaction.guild.id)

        if not config:
            await interaction.response.send_message(
                "❌ Le système de paris NHL n'est pas configuré sur ce serveur!\n"
                "Utilisez `/setupnhlbet` pour le configurer.",
                ephemeral=True
            )
            return

        enabled = config.get('enabled', False)
        channel_id = config.get('channel_id')
        channel = interaction.guild.get_channel(channel_id)

        embed = discord.Embed(
            title="🏒 Statut NHL Auto-Bet",
            color=discord.Color.green() if enabled else discord.Color.red()
        )

        embed.add_field(name="Statut", value="✅ Activé" if enabled else "❌ Désactivé", inline=True)
        embed.add_field(name="Salon", value=channel.mention if channel else "❌ Introuvable", inline=True)
        embed.add_field(name="Fréquence", value="Toutes les 24 heures", inline=True)
        embed.add_field(name="Durée du pari", value="15 heures", inline=True)

        # Compter les paris NHL actifs
        nhl_bets = [bet for bet_id, bet in active_bets.items()
                    if bet.get('auto_nhl', False) and bet.get('guild') == interaction.guild.id and bet.get('active', False)]

        embed.add_field(name="Paris NHL actifs", value=str(len(nhl_bets)), inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='forcenhlbet', description='Forcer la création d\'un pari NHL immédiatement (Admin seulement)')
    @has_admin_role()
    async def force_nhl_bet(self, interaction: discord.Interaction):
        """Forcer la création d'un pari NHL immédiatement 🏒"""

        config = nhl_auto_bet_config.get(interaction.guild.id)

        if not config:
            await interaction.response.send_message(
                "❌ Le système de paris NHL n'est pas configuré!\n"
                "Utilisez `/setupnhlbet` pour le configurer.",
                ephemeral=True
            )
            return

        if not config.get('enabled', False):
            await interaction.response.send_message(
                "❌ Le système de paris NHL est désactivé!\n"
                "Utilisez `/setupnhlbet` pour l'activer.",
                ephemeral=True
            )
            return

        await interaction.response.send_message("🏒 Création d'un pari NHL...")
        await self.create_nhl_auto_bet(interaction.guild.id, config)
        await interaction.followup.send("✅ Pari NHL créé avec succès!")

    @app_commands.command(name='setresultbet', description='Prédéfinir le résultat d\'un pari (Admin seulement)')
    @app_commands.describe(
        bet_id='L\'ID du pari',
        winning_option='Numéro de l\'option gagnante (1, 2, 3, etc.)'
    )
    @has_admin_role()
    async def set_result_bet(self, interaction: discord.Interaction, bet_id: str, winning_option: int):
        """Prédéfinir le résultat d'un pari (sera appliqué à la fermeture) 🎯"""

        if bet_id not in active_bets:
            await interaction.response.send_message("❌ Ce pari n'existe pas!", ephemeral=True)
            return

        bet = active_bets[bet_id]

        if not bet['active']:
            await interaction.response.send_message("❌ Ce pari est déjà fermé!", ephemeral=True)
            return

        if winning_option < 1 or winning_option > len(bet['options']):
            await interaction.response.send_message(
                f"❌ Option invalide! Le pari a {len(bet['options'])} options (1-{len(bet['options'])}).",
                ephemeral=True
            )
            return

        # Stocker le résultat prédéfini (ne ferme PAS le pari)
        predefined_results[bet_id] = winning_option
        winning_opt = bet['options'][winning_option - 1]

        embed = discord.Embed(
            title="✅ Résultat prédéfini",
            description=f"**{bet['title']}**\n\n**Option gagnante définie:** {winning_opt['name']} ({winning_opt['odds']}x)",
            color=discord.Color.green()
        )

        embed.add_field(
            name="ℹ️ Information",
            value="Le pari reste **actif** jusqu'à sa fermeture automatique.\n"
                  "Le résultat sera appliqué quand le pari se terminera.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        print(f"[BETTING] Résultat prédéfini par {interaction.user.name}: Option {winning_option} pour bet {bet_id}")

async def setup(bot):
    await bot.add_cog(Betting(bot))
