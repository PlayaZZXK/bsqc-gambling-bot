#!/usr/bin/env python3
"""
Script de démarrage du bot Discord Gambling
Lance ce fichier pour démarrer le bot!
"""

import os
import sys

def check_dependencies():
    """Vérifier que toutes les dépendances sont installées"""
    try:
        import discord
        print("✅ discord.py installé")
    except ImportError:
        print("❌ discord.py non installé!")
        print("Installer avec: pip install -r requirements.txt")
        sys.exit(1)

def check_structure():
    """Vérifier que tous les fichiers nécessaires existent"""
    required_files = [
        'bot.py',
        'requirements.txt',
        'commands/economy.py',
        'commands/leaderboard.py',
        'commands/betting.py',
        'commands/stats.py',
        'games/coinflip.py',
        'games/dice.py',
        'games/slots.py',
        'games/blackjack.py',
        'games/roulette.py',
        'games/crash.py',
        'games/mines.py',
        'games/plinko.py',
        'games/wheel.py',
        'games/cups.py',
        'games/higherlower.py',
        'games/rps.py',
        'games/lottery.py',
        'games/coinflip_pvp.py'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print("❌ Fichiers manquants:")
        for f in missing:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("✅ Tous les fichiers présents")

def create_directories():
    """Créer les dossiers nécessaires"""
    os.makedirs('data', exist_ok=True)
    os.makedirs('commands', exist_ok=True)
    os.makedirs('games', exist_ok=True)
    print("✅ Dossiers créés/vérifiés")

def main():
    print("=" * 50)
    print("💀 SKULL CASINO - Bot Discord Gambling 🎰")
    print("=" * 50)
    print()
    
    print("Vérification des dépendances...")
    check_dependencies()
    
    print("\nVérification de la structure...")
    check_structure()
    
    print("\nCréation/vérification des dossiers...")
    create_directories()
    
    print("\n" + "=" * 50)
    print("✅ Tout est prêt!")
    print("=" * 50)
    print()
    
    print("⚠️  IMPORTANT: Assure-toi d'avoir configuré ton token dans bot.py!")
    print()
    
    response = input("Lancer le bot maintenant? (y/n): ")
    
    if response.lower() in ['y', 'yes', 'oui', 'o']:
        print("\n🚀 Démarrage du bot...\n")
        os.system('python bot.py')
    else:
        print("\n👋 À plus tard!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt du script...")
        sys.exit(0)
