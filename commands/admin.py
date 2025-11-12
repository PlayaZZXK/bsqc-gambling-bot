import discord
from discord import app_commands
from discord.ext import commands
import sys
sys.path.append('..')
from bot import OWNER_ID, CURRENCY_NAME
from database import db

# Rôles autorisés à exécuter les commandes admin
ADMIN_ROLE_IDS = [
    1333483851053535293,
    1333483900537671710,
    1333483947023138826,
    1333483976119287809,
    1345775821893402818
]

def has_admin_role():
    """Vérifier si l'utilisateur a un des rôles admin autorisés"""
    async def predicate(interaction: discord.Interaction) -> bool:
        # Le owner peut toujours utiliser les commandes
        if interaction.user.id == OWNER_ID:
            return True

        # Vérifier si l'utilisateur a un des rôles autorisés
        if interaction.guild and hasattr(interaction.user, 'roles'):
            user_role_ids = [role.id for role in interaction.user.roles]
            if any(role_id in ADMIN_ROLE_IDS for role_id in user_role_ids):
                return True

        # Si aucun rôle autorisé, refuser
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande!", ephemeral=True)
        return False

    return app_commands.check(predicate)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='forcesave', description='Créer un backup de la base de données (Admin)')
    @has_admin_role()
    async def forcesave(self, interaction: discord.Interaction):
        """Créer un backup immédiat de la base de données SQLite"""

        await interaction.response.defer()

        try:
            # Créer un backup de la base de données
            backup_path = db.backup_database()

            embed = discord.Embed(
                title="✅ Backup créé avec succès!",
                description="Un backup de la base de données SQLite a été créé.",
                color=discord.Color.green()
            )
            embed.add_field(name="Fichier", value=backup_path, inline=False)
            embed.add_field(name="Type", value="Backup complet SQLite", inline=True)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de backup!",
                description=f"Une erreur est survenue: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name='botstats', description='Statistiques du bot (Admin)')
    @has_admin_role()
    async def botstats_cmd(self, interaction: discord.Interaction):
        """Afficher les statistiques du bot depuis la base de données"""

        # Récupérer les stats depuis SQLite
        stats = db.get_global_stats()

        embed = discord.Embed(
            title="📊 Statistiques du Bot",
            color=discord.Color.blue()
        )

        embed.add_field(name="🏰 Serveurs", value=f"{stats['total_guilds']}", inline=True)
        embed.add_field(name="👥 Utilisateurs", value=f"{stats['total_users']}", inline=True)
        embed.add_field(name="💰 Balance Totale", value=f"{stats['total_balance']:,} Skulls", inline=True)
        embed.add_field(name="🎲 Parties jouées", value=f"{stats['total_games']:,}", inline=True)
        embed.add_field(name="💸 Total parié", value=f"{stats['total_wagered']:,} Skulls", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='resetskulls', description='Réinitialiser les Skulls de plusieurs membres (Admin)')
    @app_commands.describe(
        members='Les membres à réinitialiser (séparez par des espaces)',
        montant='Le nouveau montant de Skulls à donner'
    )
    @has_admin_role()
    async def resetskulls(self, interaction: discord.Interaction, members: str, montant: int):
        """Réinitialiser les Skulls de plusieurs membres"""

        if montant < 0:
            return await interaction.response.send_message("❌ Le montant doit être positif ou nul!", ephemeral=True)

        await interaction.response.defer()

        # Parser les mentions/IDs des membres
        member_list = []
        parts = members.split()

        for part in parts:
            # Essayer de parser les mentions (@user) ou IDs
            user_id = None
            if part.startswith('<@') and part.endswith('>'):
                # Mention format <@123456> ou <@!123456>
                user_id = int(part.strip('<@!>'))
            elif part.isdigit():
                # ID direct
                user_id = int(part)

            if user_id:
                try:
                    member = await interaction.guild.fetch_member(user_id)
                    if member and not member.bot:
                        member_list.append(member)
                except:
                    pass

        if not member_list:
            return await interaction.followup.send("❌ Aucun membre valide trouvé! Utilise des mentions (@user) ou des IDs.", ephemeral=True)

        # Réinitialiser les Skulls pour chaque membre
        reset_count = 0
        results = []

        for member in member_list:
            try:
                # Obtenir le profil actuel
                profile = db.get_user_profile(member.id, interaction.guild.id)
                old_balance = profile['balance']

                # Calculer la différence
                difference = montant - old_balance

                # Mettre à jour la balance
                db.modify_balance(member.id, interaction.guild.id, difference, f"admin reset by {interaction.user.name}")
                reset_count += 1
                results.append(f"✅ {member.mention}: {old_balance:,} → {montant:,} {CURRENCY_NAME}s")

            except Exception as e:
                results.append(f"❌ {member.mention}: Erreur ({str(e)})")

        # Créer l'embed de résumé
        embed = discord.Embed(
            title=f"🔄 Reset Skulls - {reset_count}/{len(member_list)} réussis",
            description=f"**Nouveau montant:** {montant:,} {CURRENCY_NAME}s\n\n" + "\n".join(results[:10]),
            color=discord.Color.green() if reset_count > 0 else discord.Color.red()
        )

        if len(results) > 10:
            embed.set_footer(text=f"... et {len(results) - 10} autres membres")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
