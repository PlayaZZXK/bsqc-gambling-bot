"""
Script pour forcer le refresh des commandes Discord du Gambling Bot
Lance ce script si les commandes n'apparaissent pas dans Discord
"""

import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import sys

# Importer le token et client ID depuis config
try:
    from bot import TOKEN, APPLICATION_ID
except:
    print("❌ Impossible d'importer TOKEN et APPLICATION_ID depuis bot.py")
    print("Assure-toi que bot.py contient ces variables")
    sys.exit(1)

async def refresh_commands():
    """Supprime et re-enregistre toutes les commandes"""

    # Créer un bot temporaire
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)

    try:
        print("🔄 Connexion au bot...")
        await bot.login(TOKEN)

        print("🗑️  Suppression de TOUTES les commandes globales...")
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()

        print("✅ Commandes globales supprimées")
        print("\n⏳ Attends 5 secondes...")
        await asyncio.sleep(5)

        print("\n🔄 Maintenant, redémarre le bot avec:")
        print("   python bot.py")
        print("\n⏰ Les commandes apparaîtront dans Discord dans ~1 minute")

    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(refresh_commands())
