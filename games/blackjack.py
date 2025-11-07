import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI, add_xp
from database import db

class BlackjackView(discord.ui.View):
    def __init__(self, interaction, amount, deck, player_hand, dealer_hand, profile):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.amount = amount
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.profile = profile
        self.game_over = False
    
    def calculate_hand(self, hand):
        value = 0
        aces = 0
        for card in hand:
            if card in ['J', 'Q', 'K']:
                value += 10
            elif card == 'A':
                aces += 1
                value += 11
            else:
                value += int(card)
        
        while value > 21 and aces:
            value -= 10
            aces -= 1
        
        return value
    
    def format_hand(self, hand, hide_first=False):
        card_emoji = {
            'A': '🅰️', '2': '2️⃣', '3': '3️⃣', '4': '4️⃣', '5': '5️⃣'
            '6': '6️⃣', '7': '7️⃣', '8': '8️⃣', '9': '9️⃣', '10': '🔟'
            'J': '👨', 'Q': '👸', 'K': '🤴'
        }
        
        if hide_first:
            return f"🎴 {card_emoji.get(hand[1], hand[1])}"
        return ' '.join([card_emoji.get(card, card) for card in hand])
    
    async def end_game(self, interaction, won, reason):
        self.game_over = True
        
        for item in self.children:
            item.disabled = True
        
        player_value = self.calculate_hand(self.player_hand)
        dealer_value = self.calculate_hand(self.dealer_hand)
        
        if won:
            profit = self.amount
            self.profile['balance'] += self.amount * 2  # Récupère mise + gain
            self.profile['gambling_profit'] += profit
            self.profile['games_won'] += 1
            color = discord.Color.green()
            title = "🎉 Gagné!"
        else:
            self.profile['gambling_profit'] -= self.amount
            self.profile['games_lost'] += 1
            color = discord.Color.red()
            title = "💔 Perdu!"
        
        self.profile['games_played'] += 1
        self.profile['total_wagered'] += self.amount

        xp_gain = 25 if won else 10
        leveled_up = add_xp(interaction.user.id, interaction.guild.id, xp_gain)
embed = discord.Embed(title=title, description=reason, color=color)
        embed.add_field(
            name="Ta main"
            value=f"{self.format_hand(self.player_hand)}\n**Valeur: {player_value}**"
            inline=True
        )
        embed.add_field(
            name="Main du croupier"
            value=f"{self.format_hand(self.dealer_hand)}\n**Valeur: {dealer_value}**"
            inline=True
        )
        
        if won:
            embed.add_field(name="Gain", value=f"+{profit:,} {CURRENCY_NAME}s", inline=False)
        else:
            embed.add_field(name="Perte", value=f"-{self.amount:,} {CURRENCY_NAME}s", inline=False)
        
        embed.add_field(name="Nouveau solde", value=f"{self.profile['balance']:,} {CURRENCY_NAME}s", inline=False)
        
        if leveled_up:
            embed.add_field(name="🎉 Level Up!", value=f"Niveau {self.profile['level']}!", inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    @discord.ui.button(label="Hit (Tirer)", style=discord.ButtonStyle.primary, emoji="🎴")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("❌ Ce n'est pas ton jeu!", ephemeral=True)
            return
        
        # Tirer une carte
        self.player_hand.append(self.deck.pop())
        player_value = self.calculate_hand(self.player_hand)
        
        if player_value > 21:
            await self.end_game(interaction, False, "💥 Bust! Tu as dépassé 21!")
        else:
            embed = discord.Embed(title="♠️ Blackjack", color=discord.Color.blue())
            embed.add_field(
                name="Ta main"
                value=f"{self.format_hand(self.player_hand)}\n**Valeur: {player_value}**"
                inline=True
            )
            embed.add_field(
                name="Main du croupier"
                value=f"{self.format_hand(self.dealer_hand, hide_first=True)}\n**Valeur: ?**"
                inline=True
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Stand (Rester)", style=discord.ButtonStyle.success, emoji="✋")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("❌ Ce n'est pas ton jeu!", ephemeral=True)
            return
        
        # Le croupier joue
        while self.calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        
        player_value = self.calculate_hand(self.player_hand)
        dealer_value = self.calculate_hand(self.dealer_hand)
        
        if dealer_value > 21:
            await self.end_game(interaction, True, "🎉 Le croupier a bust! Tu gagnes!")
        elif player_value > dealer_value:
            await self.end_game(interaction, True, "🎉 Ta main est meilleure! Tu gagnes!")
        elif player_value < dealer_value:
            await self.end_game(interaction, False, "💔 La main du croupier est meilleure...")
        else:
            # Égalité - rendre la mise
            self.profile['balance'] += self.amount
for item in self.children:
                item.disabled = True
            
            embed = discord.Embed(title="🤝 Égalité!", description="Mise rendue!", color=discord.Color.orange())
            embed.add_field(
                name="Ta main"
                value=f"{self.format_hand(self.player_hand)}\n**Valeur: {player_value}**"
                inline=True
            )
            embed.add_field(
                name="Main du croupier"
                value=f"{self.format_hand(self.dealer_hand)}\n**Valeur: {dealer_value}**"
                inline=True
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='blackjack', description='Jouer au Blackjack! ♠️')
    @app_commands.describe(montant='Le montant à miser')
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def blackjack(self, interaction: discord.Interaction, montant: int):
        """Jouer au Blackjack! ♠️"""

        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif!", ephemeral=True)
            return

        profile = get_user_profile(interaction.user.id, interaction.guild.id)

        if profile['balance'] < montant:
            await interaction.response.send_message(f"❌ Tu n'as pas assez de {CURRENCY_NAME}s! (Tu as: {profile['balance']:,})", ephemeral=True)
            return

        # Déduire la mise
        profile['balance'] -= montant
# Créer le deck
        cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] * 4
        random.shuffle(cards)

        # Distribuer les cartes
        player_hand = [cards.pop(), cards.pop()]
        dealer_hand = [cards.pop(), cards.pop()]

        # Créer la vue
        view = BlackjackView(interaction, montant, cards, player_hand, dealer_hand, profile)

        player_value = view.calculate_hand(player_hand)

        # Vérifier blackjack naturel
        if player_value == 21:
            dealer_value = view.calculate_hand(dealer_hand)
            if dealer_value == 21:
                # Égalité
                profile['balance'] += montant
embed = discord.Embed(
                    title="🤝 Double Blackjack! Égalité!"
                    description="Vous avez tous les deux 21!"
                    color=discord.Color.orange()
                )
            else:
                # Blackjack naturel - bonus 2.5x
                winnings = int(montant * 2.5)
                profit = int(montant * 1.5)
                profile['balance'] += winnings
                profile['gambling_profit'] += profit
                profile['games_won'] += 1
                profile['games_played'] += 1
                profile['total_wagered'] += montant

                add_xp(interaction.user.id, interaction.guild.id, 50)
embed = discord.Embed(
                    title="♠️ BLACKJACK NATUREL! ♠️"
                    description=f"21 dès la distribution! Bonus ×2.5!\n\n**Gain: +{profit:,} {CURRENCY_NAME}s**"
                    color=discord.Color.gold()
                )

            embed.add_field(
                name="Ta main"
                value=f"{view.format_hand(player_hand)}\n**Valeur: {player_value}**"
                inline=True
            )
            embed.add_field(
                name="Main du croupier"
                value=f"{view.format_hand(dealer_hand)}\n**Valeur: {dealer_value}**"
                inline=True
            )

            await interaction.response.send_message(embed=embed)
            return

        # Jeu normal
        embed = discord.Embed(title="♠️ Blackjack", color=discord.Color.blue())
        embed.add_field(
            name="Ta main"
            value=f"{view.format_hand(player_hand)}\n**Valeur: {player_value}**"
            inline=True
        )
        embed.add_field(
            name="Main du croupier"
            value=f"{view.format_hand(dealer_hand, hide_first=True)}\n**Valeur: ?**"
            inline=True
        )
        embed.set_footer(text=f"Mise: {montant:,} {CURRENCY_NAME}s")

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Blackjack(bot))
