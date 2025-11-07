import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI, add_xp
from database import db

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='balance', description='Voir ton solde de Skulls')
    @app_commands.describe(member='Le membre dont tu veux voir le solde (optionnel)')
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        """Voir ton solde de Skulls"""
        if member is None:
            member = interaction.user

        profile = get_user_profile(member.id, interaction.guild.id)

        embed = discord.Embed(
            title=f"{CURRENCY_EMOJI} Portefeuille de {member.display_name}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Balance", value=f"{profile['balance']:,} {CURRENCY_NAME}s", inline=False)
        embed.add_field(name="Niveau", value=f"Niveau {profile['level']} ({profile['xp']}/100 XP)", inline=True)
        embed.add_field(name="Total gagné", value=f"{profile['total_earned']:,} {CURRENCY_NAME}s", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='daily', description='Réclamer tes 100 Skulls quotidiens!')
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id)  # 1 fois par 24h
    async def daily(self, interaction: discord.Interaction):
        """Réclamer tes 100 Skulls quotidiens! 💀"""
        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        # Vérifier le streak
        now = datetime.now()
        last_daily = profile.get('last_daily')

        if last_daily:
            last_daily = datetime.fromisoformat(last_daily)
            diff = (now - last_daily).total_seconds()

            # Si moins de 48h, streak continue
            if diff < 172800:  # 48h
                profile['daily_streak'] += 1
            else:
                profile['daily_streak'] = 1
        else:
            profile['daily_streak'] = 1

        # Bonus de streak
        base_reward = 100
        streak_bonus = min(profile['daily_streak'] * 10, 200)  # Max +200
        total_reward = base_reward + streak_bonus

        # Mettre à jour dans la base de données
        db.modify_balance(interaction.user.id, interaction.guild.id, total_reward, "daily reward")
        db.update_user_profile(
            interaction.user.id,
            interaction.guild.id,
            total_earned=profile['total_earned'] + total_reward,
            last_daily=now.isoformat(),
            daily_streak=profile['daily_streak']
        )

        # Mettre à jour le profil local pour l'affichage
        profile['balance'] += total_reward
        profile['total_earned'] += total_reward

        # XP
        leveled_up = add_xp(interaction.user.id, interaction.guild.id, 20)
        if leveled_up:
            profile = get_user_profile(interaction.user.id, interaction.guild.id)  # Refresh pour le nouveau level

        embed = discord.Embed(
            title=f"{CURRENCY_EMOJI} Daily Récompense!",
            description=f"Tu as reçu **{total_reward} {CURRENCY_NAME}s**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Streak", value=f"🔥 {profile['daily_streak']} jours!", inline=True)
        embed.add_field(name="Nouveau solde", value=f"{profile['balance']:,} {CURRENCY_NAME}s", inline=True)

        if leveled_up:
            embed.add_field(name="🎉 Level Up!", value=f"Niveau {profile['level']}!", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='give', description='Donner des Skulls à quelqu\'un')
    @app_commands.describe(
        member='Le membre à qui donner',
        montant='Le montant à donner'
    )
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    async def give(self, interaction: discord.Interaction, member: discord.Member, montant: int):
        """Donner des Skulls à quelqu'un"""
        if member.bot:
            await interaction.response.send_message("❌ Tu ne peux pas donner des Skulls à un bot!", ephemeral=True)
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message("❌ Tu ne peux pas te donner des Skulls à toi-même!", ephemeral=True)
            return

        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif!", ephemeral=True)
            return

        sender_profile = get_user_profile(interaction.user.id, interaction.guild.id)

        if sender_profile['balance'] < montant:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de {CURRENCY_NAME}s! (Tu as: {sender_profile['balance']:,})", ephemeral=True)
            return

        receiver_profile = get_user_profile(member.id, interaction.guild.id)

        # Transaction - ATOMIQUE avec SQLite!
        db.modify_balance(interaction.user.id, interaction.guild.id, -montant, f"gift to {member.id}")
        db.modify_balance(member.id, interaction.guild.id, montant, f"gift from {interaction.user.id}")
        db.update_user_profile(
            member.id,
            interaction.guild.id,
            total_earned=receiver_profile['total_earned'] + montant
        )

        embed = discord.Embed(
            title=f"{CURRENCY_EMOJI} Cadeau envoyé!",
            description=f"{interaction.user.mention} a donné **{montant:,} {CURRENCY_NAME}s** à {member.mention}!",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='giveadmin', description='Donner des Skulls à quelqu\'un (Admin seulement)')
    @app_commands.describe(
        member='Le membre à qui donner',
        montant='Le montant à donner'
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def give_admin(self, interaction: discord.Interaction, member: discord.Member, montant: int):
        """Donner des Skulls à quelqu'un sans restrictions (Admin seulement)"""
        if member.bot:
            await interaction.response.send_message("❌ Tu ne peux pas donner des Skulls à un bot!", ephemeral=True)
            return

        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif!", ephemeral=True)
            return

        receiver_profile = get_user_profile(member.id, interaction.guild.id)

        # Donner l'argent directement sans déduire du balance de l'admin
        db.modify_balance(member.id, interaction.guild.id, montant, f"admin gift from {interaction.user.id}")
        db.update_user_profile(
            member.id,
            interaction.guild.id,
            total_earned=receiver_profile['total_earned'] + montant
        )

        embed = discord.Embed(
            title=f"{CURRENCY_EMOJI} Admin Gift!",
            description=f"{interaction.user.mention} a donné **{montant:,} {CURRENCY_NAME}s** à {member.mention}!",
            color=discord.Color.purple()
        )
        embed.set_footer(text="👑 Commande Admin")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='work', description='Travailler pour gagner de l\'argent')
    @app_commands.checks.cooldown(1, 3600, key=lambda i: i.user.id)  # 1 fois par heure
    async def work(self, interaction: discord.Interaction):
        """Travailler pour gagner de l'argent"""
        import random

        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        # Gains aléatoires entre 50 et 150
        earnings = random.randint(50, 150)

        # Mettre à jour dans la base de données
        new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, earnings, "work")
        db.update_user_profile(
            interaction.user.id,
            interaction.guild.id,
            total_earned=profile['total_earned'] + earnings
        )

        # Mettre à jour profil local pour affichage
        profile['balance'] = new_balance

        # XP
        leveled_up = add_xp(interaction.user.id, interaction.guild.id, 10)
        if leveled_up:
            profile = get_user_profile(interaction.user.id, interaction.guild.id)

        jobs = [
            "creusé des tombes",
            "vendu des os",
            "hanté une maison",
            "fait peur aux vivants",
            "ramassé des âmes perdues"
        ]

        embed = discord.Embed(
            title="💼 Travail terminé!",
            description=f"Tu as {random.choice(jobs)} et gagné **{earnings} {CURRENCY_NAME}s**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Nouveau solde", value=f"{profile['balance']:,} {CURRENCY_NAME}s", inline=False)

        if leveled_up:
            embed.add_field(name="🎉 Level Up!", value=f"Niveau {profile['level']}!", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='rob', description='Tenter de voler quelqu\'un')
    @app_commands.describe(member='Le membre à voler')
    @app_commands.checks.cooldown(1, 7200, key=lambda i: i.user.id)  # 1 fois toutes les 2h
    async def rob(self, interaction: discord.Interaction, member: discord.Member):
        """Tenter de voler quelqu'un"""
        import random

        if member.bot:
            await interaction.response.send_message("❌ Tu ne peux pas voler un bot!", ephemeral=True)
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message("❌ Tu ne peux pas te voler toi-même!", ephemeral=True)
            return

        thief_profile = get_user_profile(interaction.user.id, interaction.guild.id)
        victim_profile = get_user_profile(member.id, interaction.guild.id)

        # Vérifier que la victime a de l'argent
        if victim_profile['balance'] < 100:
            await interaction.response.send_message(f"❌ {member.display_name} est trop pauvre pour être volé!", ephemeral=True)
            return

        # 50% de chance de réussir
        success = random.choice([True, False])

        if success:
            # Vol entre 10% et 30% de la balance de la victime
            stolen = int(victim_profile['balance'] * random.uniform(0.1, 0.3))
            stolen = max(50, min(stolen, 500))  # Entre 50 et 500

            # Transaction - ATOMIQUE avec SQLite!
            db.modify_balance(member.id, interaction.guild.id, -stolen, f"robbed by {interaction.user.id}")
            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, stolen, f"robbed {member.id}")
            db.update_user_profile(
                interaction.user.id,
                interaction.guild.id,
                total_earned=thief_profile['total_earned'] + stolen
            )

            embed = discord.Embed(
                title="💰 Vol réussi!",
                description=f"Tu as volé **{stolen} {CURRENCY_NAME}s** à {member.mention}!",
                color=discord.Color.green()
            )
            embed.add_field(name="Ton nouveau solde", value=f"{new_balance:,} {CURRENCY_NAME}s", inline=False)
        else:
            # Échec - pénalité
            penalty = random.randint(50, 100)
            penalty = min(penalty, thief_profile['balance'])

            new_balance = db.modify_balance(interaction.user.id, interaction.guild.id, -penalty, "rob failed")

            embed = discord.Embed(
                title="🚨 Vol échoué!",
                description=f"Tu t'es fait prendre! Tu perds **{penalty} {CURRENCY_NAME}s** d'amende!",
                color=discord.Color.red()
            )
            embed.add_field(name="Ton nouveau solde", value=f"{new_balance:,} {CURRENCY_NAME}s", inline=False)

        await interaction.response.send_message(embed=embed)

    @daily.error
    @give.error
    @work.error
    @rob.error
    async def cooldown_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            remaining = error.retry_after
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)

            if hours > 0:
                time_str = f"{hours}h {minutes}m"
            else:
                time_str = f"{minutes}m"

            await interaction.response.send_message(f"⏰ Cooldown! Réessaye dans **{time_str}**", ephemeral=True)

    @give_admin.error
    async def give_admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu dois être administrateur pour utiliser cette commande!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Economy(bot))
