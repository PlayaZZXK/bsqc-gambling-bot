import discord
from discord import app_commands
from discord.ext import commands
import sys
sys.path.append('..')
from bot import CURRENCY_NAME, CURRENCY_EMOJI

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description='Voir toutes les commandes disponibles!')
    @app_commands.describe(category='Catégorie: economy, games, betting, stats')
    async def help_command(self, interaction: discord.Interaction, category: str = None):
        """Voir toutes les commandes disponibles! 📚"""

        if category is None:
            # Menu principal
            embed = discord.Embed(
                title=f"{CURRENCY_EMOJI} SKULL CASINO - Commandes",
                description=f"Monnaie: {CURRENCY_NAME}s {CURRENCY_EMOJI}",
                color=discord.Color.purple()
            )

            embed.add_field(
                name="💰 Économie",
                value="`/help economy` - Commandes d'économie",
                inline=False
            )

            embed.add_field(
                name="🎰 Jeux",
                value="`/help games` - Tous les jeux disponibles",
                inline=False
            )

            embed.add_field(
                name="🎲 Paris",
                value="`/help betting` - Système de paris communautaires",
                inline=False
            )

            embed.add_field(
                name="🏆 Stats & Classements",
                value="`/help stats` - Statistiques et leaderboards",
                inline=False
            )

            embed.set_footer(text="Utilise /help <catégorie> pour plus de détails!")

        elif category.lower() in ['economy', 'eco', 'economie']:
            embed = discord.Embed(
                title="💰 Commandes d'Économie",
                color=discord.Color.gold()
            )

            commands_list = [
                ("`/balance` / `/bal`", "Voir ton solde de Skulls"),
                ("`/daily`", "Réclamer tes 100 Skulls quotidiens (24h cooldown)"),
                ("`/work`", "Travailler pour gagner de l'argent (1h cooldown)"),
                ("`/give <@user> <montant>`", "Donner des Skulls à quelqu'un"),
                ("`/rob <@user>`", "Tenter de voler quelqu'un (2h cooldown)"),
                ("`/stats` / `/profile`", "Voir tes statistiques complètes"),
                ("`/rank`", "Voir ton classement dans le serveur"),
            ]

            for cmd, desc in commands_list:
                embed.add_field(name=cmd, value=desc, inline=False)

        elif category.lower() in ['games', 'jeux', 'game']:
            embed = discord.Embed(
                title="🎰 Tous les Jeux",
                description="Usage: `/jeu montant` + options selon le jeu",
                color=discord.Color.blue()
            )

            games = [
                ("**Jeux Classiques**", ""),
                ("`/coinflip <choix> <montant>`", "Pile ou face (×2)"),
                ("`/dice <choix> <montant>`", "Dés (×2 ou ×6)"),
                ("`/slots <montant>`", "Machine à sous (×10 max)"),
                ("`/blackjack <montant>`", "Blackjack interactif (×2)"),
                ("`/roulette <choix> <montant>`", "Roulette (×2 ou ×36)"),
                ("", ""),
                ("**Jeux Modernes**", ""),
                ("`/crash <montant>`", "Cash out avant le crash!"),
                ("`/mines <montant> [nb_mines]`", "Démineur (5 mines par défaut)"),
                ("`/plinko <montant>`", "Balle qui tombe (×10 max)"),
                ("`/wheel <montant>`", "Roue de la fortune (×50 max)"),
                ("`/cups <choix> <montant>`", "Jeu des gobelets (×2)"),
                ("", ""),
                ("**PvP & Autres**", ""),
                ("`/higherlower <choix> <montant>`", "Carte plus haute/basse (×2)"),
                ("`/rps <choix> <montant>`", "Pierre-Papier-Ciseaux (×2)"),
                ("`/duel <@user> <montant>`", "Défi coinflip PvP"),
                ("`/lottery` / `/buyticket`", "Loterie du serveur"),
            ]

            for cmd, desc in games:
                if cmd and desc:
                    embed.add_field(name=cmd, value=desc, inline=False)
                elif cmd:
                    embed.add_field(name=cmd, value="━━━━━━━━━━━━━━", inline=False)

        elif category.lower() in ['betting', 'bet', 'paris']:
            embed = discord.Embed(
                title="🎲 Système de Paris",
                description="Crée des paris personnalisés avec côtes libres!",
                color=discord.Color.green()
            )

            betting_cmds = [
                ("`/createbet`", "Créer un nouveau pari (Admin seulement)"),
                ("`/activebets`", "Voir tous les paris actifs"),
                ("`/viewbet <id>`", "Voir les détails d'un pari"),
                ("`/placebet <id> <option> <montant>`", "Placer un pari sur une option"),
                ("`/closebet <id> <option_gagnante>`", "Fermer un pari et distribuer (Admin)"),
            ]

            for cmd, desc in betting_cmds:
                embed.add_field(name=cmd, value=desc, inline=False)

            embed.add_field(
                name="📝 Exemple",
                value="1. Admin fait `/createbet`\n"
                      "2. Joueurs font `/placebet abc123 1 500`\n"
                      "3. Admin ferme avec `/closebet abc123 1`",
                inline=False
            )

        elif category.lower() in ['stats', 'leaderboard', 'lb', 'classement']:
            embed = discord.Embed(
                title="🏆 Stats & Classements",
                color=discord.Color.orange()
            )

            stats_cmds = [
                ("`/stats` / `/profile`", "Tes statistiques personnelles complètes"),
                ("`/rank`", "Ton rang dans le serveur"),
                ("`/leaderboard` / `/lb`", "Top 10 des plus riches (total)"),
                ("`/gamblingtop` / `/gtop`", "Top 10 meilleurs gamblers (profits nets sans daily/gifts)"),
            ]

            for cmd, desc in stats_cmds:
                embed.add_field(name=cmd, value=desc, inline=False)

            embed.add_field(
                name="📊 Stats incluses",
                value="• Balance & Total gagné\n"
                      "• Profit net de gambling\n"
                      "• Parties jouées/gagnées/perdues\n"
                      "• Ratio gains/pertes\n"
                      "• Niveau & XP\n"
                      "• Streak daily",
                inline=False
            )

        else:
            embed = discord.Embed(
                title="❌ Catégorie inconnue",
                description="Catégories disponibles: `economy`, `games`, `betting`, `stats`",
                color=discord.Color.red()
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='info', description='Informations sur le bot')
    async def info(self, interaction: discord.Interaction):
        """Informations sur le bot"""

        total_users = len(set(self.bot.get_all_members()))
        total_guilds = len(self.bot.guilds)

        embed = discord.Embed(
            title=f"{CURRENCY_EMOJI} SKULL CASINO",
            description="Bot de gambling complet avec 14 jeux!",
            color=discord.Color.purple()
        )

        embed.add_field(name="🎰 Jeux", value="14 jeux différents", inline=True)
        embed.add_field(name="👥 Utilisateurs", value=f"{total_users}", inline=True)
        embed.add_field(name="🏰 Serveurs", value=f"{total_guilds}", inline=True)

        embed.add_field(name="💀 Monnaie", value=f"{CURRENCY_NAME}s", inline=True)
        embed.add_field(name="⚙️ Commandes", value="Slash commands (/)", inline=True)
        embed.add_field(name="🐍 Python", value="discord.py", inline=True)

        embed.add_field(
            name="🎮 Fonctionnalités",
            value="• 14 jeux de gambling\n"
                  "• Système d'économie complet\n"
                  "• Paris communautaires\n"
                  "• Statistiques détaillées\n"
                  "• Classements multiples\n"
                  "• Système de niveaux\n"
                  "• Sauvegardes automatiques",
            inline=False
        )

        embed.set_footer(text="Utilise /help pour voir les commandes!")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
