import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from typing import List, Dict, Optional, Tuple
from enum import Enum
import sys
sys.path.append('..')
from bot import get_user_profile, CURRENCY_NAME, CURRENCY_EMOJI, add_xp
from database import db

# Emojis pour les cartes
SUIT_EMOJIS = {
    'hearts': '♥️',
    'diamonds': '♦️',
    'clubs': '♣️',
    'spades': '♠️'
}

CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

class HandRank(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank}{SUIT_EMOJIS[self.suit]}"

    def __repr__(self):
        return str(self)

class Deck:
    def __init__(self):
        self.cards = []
        self.reset()

    def reset(self):
        """Créer un nouveau deck de 52 cartes"""
        self.cards = []
        for suit in ['hearts', 'diamonds', 'clubs', 'spades']:
            for rank in CARD_VALUES.keys():
                self.cards.append(Card(rank, suit))
        random.shuffle(self.cards)

    def deal(self, count: int = 1) -> List[Card]:
        """Distribuer des cartes"""
        dealt = self.cards[:count]
        self.cards = self.cards[count:]
        return dealt

class PokerPlayer:
    def __init__(self, user: discord.Member, chips: int):
        self.user = user
        self.chips = chips
        self.hand: List[Card] = []
        self.current_bet = 0
        self.total_bet = 0
        self.is_folded = False
        self.is_all_in = False

    def reset_for_new_hand(self):
        """Reset pour une nouvelle main"""
        self.hand = []
        self.current_bet = 0
        self.total_bet = 0
        self.is_folded = False
        self.is_all_in = False

class PokerGame:
    def __init__(self, guild_id: int, creator: discord.Member, buyin: int,
                 wait_time: int, min_players: int, max_players: int = 8):
        self.guild_id = guild_id
        self.creator = creator
        self.buyin = buyin
        self.wait_time = wait_time
        self.min_players = max(1, min_players)
        self.max_players = min(8, max_players)

        self.players: List[PokerPlayer] = []
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.dealer_position = 0
        self.current_player_index = 0

        self.is_started = False
        self.is_finished = False
        self.lobby_message: Optional[discord.Message] = None
        self.game_message: Optional[discord.Message] = None

    def add_player(self, user: discord.Member) -> bool:
        """Ajouter un joueur à la table"""
        if len(self.players) >= self.max_players:
            return False
        if any(p.user.id == user.id for p in self.players):
            return False

        self.players.append(PokerPlayer(user, self.buyin))
        return True

    def remove_player(self, user_id: int) -> bool:
        """Retirer un joueur de la table"""
        for i, player in enumerate(self.players):
            if player.user.id == user_id:
                self.players.pop(i)
                return True
        return False

    def get_active_players(self) -> List[PokerPlayer]:
        """Joueurs actifs (non fold, non all-in)"""
        return [p for p in self.players if not p.is_folded and not p.is_all_in and p.chips > 0]

    def get_players_in_hand(self) -> List[PokerPlayer]:
        """Joueurs toujours dans la main (non fold)"""
        return [p for p in self.players if not p.is_folded]

    def start_new_hand(self):
        """Commencer une nouvelle main"""
        # Reset deck et cartes
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0

        # Reset joueurs
        for player in self.players:
            player.reset_for_new_hand()

        # Distribuer 2 cartes à chaque joueur
        for player in self.players:
            player.hand = self.deck.deal(2)

    def evaluate_hand(self, player: PokerPlayer) -> Tuple[HandRank, List[int]]:
        """Évaluer la main d'un joueur (5 meilleures cartes parmi 7)"""
        all_cards = player.hand + self.community_cards

        # Générer toutes les combinaisons de 5 cartes
        from itertools import combinations
        best_rank = HandRank.HIGH_CARD
        best_values = []

        for combo in combinations(all_cards, 5):
            rank, values = self._evaluate_5_cards(list(combo))
            if rank.value > best_rank.value or (rank.value == best_rank.value and values > best_values):
                best_rank = rank
                best_values = values

        return best_rank, best_values

    def _evaluate_5_cards(self, cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """Évaluer une main de 5 cartes"""
        ranks = sorted([CARD_VALUES[c.rank] for c in cards], reverse=True)
        suits = [c.suit for c in cards]

        is_flush = len(set(suits)) == 1
        is_straight = self._is_straight(ranks)

        # Compter les occurrences
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1

        counts = sorted(rank_counts.values(), reverse=True)
        unique_ranks = sorted(rank_counts.keys(), key=lambda x: (rank_counts[x], x), reverse=True)

        # Royal Flush
        if is_flush and is_straight and ranks[0] == 14:
            return HandRank.ROYAL_FLUSH, ranks

        # Straight Flush
        if is_flush and is_straight:
            return HandRank.STRAIGHT_FLUSH, ranks

        # Four of a Kind
        if counts == [4, 1]:
            return HandRank.FOUR_OF_KIND, unique_ranks

        # Full House
        if counts == [3, 2]:
            return HandRank.FULL_HOUSE, unique_ranks

        # Flush
        if is_flush:
            return HandRank.FLUSH, ranks

        # Straight
        if is_straight:
            return HandRank.STRAIGHT, ranks

        # Three of a Kind
        if counts == [3, 1, 1]:
            return HandRank.THREE_OF_KIND, unique_ranks

        # Two Pair
        if counts == [2, 2, 1]:
            return HandRank.TWO_PAIR, unique_ranks

        # Pair
        if counts == [2, 1, 1, 1]:
            return HandRank.PAIR, unique_ranks

        # High Card
        return HandRank.HIGH_CARD, ranks

    def _is_straight(self, ranks: List[int]) -> bool:
        """Vérifier si c'est une suite"""
        # Suite normale
        if ranks[0] - ranks[4] == 4 and len(set(ranks)) == 5:
            return True
        # Suite A-2-3-4-5 (As bas)
        if set(ranks) == {14, 5, 4, 3, 2}:
            return True
        return False

    def determine_winners(self) -> List[Tuple[PokerPlayer, HandRank, List[int]]]:
        """Déterminer le(s) gagnant(s)"""
        players_in = self.get_players_in_hand()

        if len(players_in) == 1:
            return [(players_in[0], None, [])]

        # Évaluer toutes les mains
        evaluated = []
        for player in players_in:
            rank, values = self.evaluate_hand(player)
            evaluated.append((player, rank, values))

        # Trier par meilleure main
        evaluated.sort(key=lambda x: (x[1].value, x[2]), reverse=True)

        # Trouver tous les joueurs avec la meilleure main
        best_rank = evaluated[0][1]
        best_values = evaluated[0][2]
        winners = [e for e in evaluated if e[1] == best_rank and e[2] == best_values]

        return winners

class JoinButton(discord.ui.Button):
    def __init__(self, game: PokerGame):
        super().__init__(style=discord.ButtonStyle.green, label="Join Table", emoji="🎰")
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        if self.game.is_started:
            await interaction.response.send_message("❌ La partie a déjà commencé!", ephemeral=True)
            return

        # Vérifier le balance
        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < self.game.buyin:
            await interaction.response.send_message(
                f"❌ Tu n'as pas assez de {CURRENCY_NAME}s! (Requis: {self.game.buyin:,}, Tu as: {profile['balance']:,})",
                ephemeral=True
            )
            return

        # Ajouter le joueur
        if self.game.add_player(interaction.user):
            # Déduire le buy-in
            db.modify_balance(interaction.user.id, interaction.guild.id, -self.game.buyin, "poker buy-in")

            await interaction.response.send_message(f"✅ Tu as rejoint la table! ({self.game.buyin:,} {CURRENCY_NAME}s)", ephemeral=True)

            # Mettre à jour le lobby
            await self.update_lobby()
        else:
            await interaction.response.send_message("❌ Tu es déjà à la table ou la table est pleine!", ephemeral=True)

    async def update_lobby(self):
        """Mettre à jour le message du lobby"""
        if self.game.lobby_message:
            embed = create_lobby_embed(self.game)
            await self.game.lobby_message.edit(embed=embed)

class LeaveButton(discord.ui.Button):
    def __init__(self, game: PokerGame):
        super().__init__(style=discord.ButtonStyle.red, label="Leave Table", emoji="🚪")
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        if self.game.is_started:
            await interaction.response.send_message("❌ Tu ne peux pas quitter une partie en cours!", ephemeral=True)
            return

        if self.game.remove_player(interaction.user.id):
            # Rembourser le buy-in
            db.modify_balance(interaction.user.id, interaction.guild.id, self.game.buyin, "poker refund")

            await interaction.response.send_message("✅ Tu as quitté la table! (Remboursé)", ephemeral=True)

            # Mettre à jour le lobby
            if self.game.lobby_message:
                embed = create_lobby_embed(self.game)
                await self.game.lobby_message.edit(embed=embed)
        else:
            await interaction.response.send_message("❌ Tu n'es pas à cette table!", ephemeral=True)

class LobbyView(discord.ui.View):
    def __init__(self, game: PokerGame):
        super().__init__(timeout=None)
        self.add_item(JoinButton(game))
        self.add_item(LeaveButton(game))

class BettingView(discord.ui.View):
    def __init__(self, game: PokerGame, player: PokerPlayer, cog):
        super().__init__(timeout=25)  # Timer de 25 secondes
        self.game = game
        self.player = player
        self.cog = cog
        self.action_taken = False

        # Calculer les options disponibles
        to_call = game.current_bet - player.current_bet

        # Fold (toujours disponible)
        fold_btn = discord.ui.Button(style=discord.ButtonStyle.danger, label="Fold", emoji="❌")
        fold_btn.callback = self.fold_callback
        self.add_item(fold_btn)

        # Check (si pas de mise à suivre)
        if to_call == 0:
            check_btn = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Check", emoji="✋")
            check_btn.callback = self.check_callback
            self.add_item(check_btn)

        # Call (s'il y a une mise à suivre)
        if to_call > 0 and player.chips >= to_call:
            call_btn = discord.ui.Button(style=discord.ButtonStyle.primary, label=f"Call {to_call}", emoji="📞")
            call_btn.callback = self.call_callback
            self.add_item(call_btn)

        # Raise (si on peut miser)
        if player.chips > to_call:
            min_raise = max(game.current_bet * 2, to_call + 10)
            if player.chips >= min_raise:
                raise_btn = discord.ui.Button(style=discord.ButtonStyle.success, label="Raise", emoji="⬆️")
                raise_btn.callback = self.raise_callback
                self.add_item(raise_btn)

        # All-in (toujours disponible si on a des chips)
        if player.chips > 0:
            allin_btn = discord.ui.Button(style=discord.ButtonStyle.danger, label=f"All-in ({player.chips})", emoji="🔥")
            allin_btn.callback = self.allin_callback
            self.add_item(allin_btn)

    async def fold_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message("❌ Ce n'est pas ton tour!", ephemeral=True)
            return

        self.player.is_folded = True
        self.action_taken = True
        await interaction.response.send_message(f"{self.player.user.mention} a fold!", ephemeral=False)
        self.stop()

    async def check_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message("❌ Ce n'est pas ton tour!", ephemeral=True)
            return

        self.action_taken = True
        await interaction.response.send_message(f"{self.player.user.mention} a check!", ephemeral=False)
        self.stop()

    async def call_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message("❌ Ce n'est pas ton tour!", ephemeral=True)
            return

        to_call = self.game.current_bet - self.player.current_bet
        if self.player.chips >= to_call:
            self.player.chips -= to_call
            self.player.current_bet += to_call
            self.player.total_bet += to_call
            self.game.pot += to_call

            self.action_taken = True
            await interaction.response.send_message(f"{self.player.user.mention} a call {to_call} {CURRENCY_NAME}s!", ephemeral=False)
            self.stop()
        else:
            await interaction.response.send_message("❌ Tu n'as pas assez de chips!", ephemeral=True)

    async def raise_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message("❌ Ce n'est pas ton tour!", ephemeral=True)
            return

        # Demander le montant (pour simplifier, on raise le minimum)
        to_call = self.game.current_bet - self.player.current_bet
        min_raise = max(self.game.current_bet, 10)
        raise_amount = min_raise

        if self.player.chips >= to_call + raise_amount:
            total_bet = to_call + raise_amount
            self.player.chips -= total_bet
            self.player.current_bet += total_bet
            self.player.total_bet += total_bet
            self.game.pot += total_bet
            self.game.current_bet = self.player.current_bet

            self.action_taken = True
            await interaction.response.send_message(
                f"{self.player.user.mention} a raise de {raise_amount} {CURRENCY_NAME}s! (Total: {self.player.current_bet})",
                ephemeral=False
            )
            self.stop()
        else:
            await interaction.response.send_message("❌ Tu n'as pas assez de chips!", ephemeral=True)

    async def allin_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message("❌ Ce n'est pas ton tour!", ephemeral=True)
            return

        all_in_amount = self.player.chips
        self.player.current_bet += all_in_amount
        self.player.total_bet += all_in_amount
        self.game.pot += all_in_amount
        self.player.chips = 0
        self.player.is_all_in = True

        if self.player.current_bet > self.game.current_bet:
            self.game.current_bet = self.player.current_bet

        self.action_taken = True
        await interaction.response.send_message(
            f"🔥 {self.player.user.mention} fait ALL-IN avec {all_in_amount} {CURRENCY_NAME}s!",
            ephemeral=False
        )
        self.stop()

    async def on_timeout(self):
        """Auto-fold si timeout"""
        if not self.action_taken:
            self.player.is_folded = True
            # Le message sera envoyé par le système de jeu

def create_lobby_embed(game: PokerGame) -> discord.Embed:
    """Créer l'embed du lobby"""
    embed = discord.Embed(
        title="🎰 Table de Poker - Lobby",
        description=f"**Créateur:** {game.creator.mention}\n"
                    f"**Buy-in:** {game.buyin:,} {CURRENCY_NAME}s\n"
                    f"**Joueurs:** {len(game.players)}/{game.max_players}",
        color=discord.Color.green()
    )

    if game.players:
        players_list = "\n".join([f"{i+1}. {p.user.mention}" for i, p in enumerate(game.players)])
        embed.add_field(name="Joueurs à la table", value=players_list, inline=False)

    embed.set_footer(text=f"La partie commence dans {game.wait_time} secondes ou quand la table est pleine!")

    return embed

def create_game_embed(game: PokerGame, phase: str) -> discord.Embed:
    """Créer l'embed du jeu"""
    embed = discord.Embed(
        title=f"🎰 Poker - {phase}",
        color=discord.Color.gold()
    )

    # Cartes communes
    if game.community_cards:
        cards_str = " ".join([str(card) for card in game.community_cards])
        embed.add_field(name="Cartes communes", value=cards_str, inline=False)

    # Pot
    embed.add_field(name="💰 Pot", value=f"{game.pot:,} {CURRENCY_NAME}s", inline=True)
    embed.add_field(name="🎯 Mise actuelle", value=f"{game.current_bet:,}", inline=True)

    # Joueurs
    players_info = []
    for i, player in enumerate(game.players):
        status = ""
        if player.is_folded:
            status = "❌ Fold"
        elif player.is_all_in:
            status = "🔥 All-in"
        elif i == game.current_player_index and not game.is_finished:
            status = "👉 À toi"

        players_info.append(
            f"{player.user.mention}: {player.chips:,} {CURRENCY_NAME}s {status}"
        )

    embed.add_field(name="Joueurs", value="\n".join(players_info), inline=False)

    return embed

class Poker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games: Dict[int, PokerGame] = {}  # channel_id -> game

    @app_commands.command(name='playpoker', description='Créer une table de poker Texas Hold\'em')
    @app_commands.describe(
        buyin='Mise d\'entrée (en Skulls)',
        wait_time='Temps d\'attente avant de commencer (secondes, défaut: 60)',
        min_players='Nombre minimum de joueurs (défaut: 2)',
        max_players='Nombre maximum de joueurs (défaut: 8)'
    )
    async def play_poker(
        self,
        interaction: discord.Interaction,
        buyin: int,
        wait_time: int = 60,
        min_players: int = 2,
        max_players: int = 8
    ):
        """Créer une table de poker"""

        # Validations
        if buyin < 10:
            await interaction.response.send_message("❌ Le buy-in minimum est de 10 Skulls!", ephemeral=True)
            return

        if wait_time < 10 or wait_time > 300:
            await interaction.response.send_message("❌ Le temps d'attente doit être entre 10 et 300 secondes!", ephemeral=True)
            return

        if min_players < 1 or min_players > 8:
            await interaction.response.send_message("❌ Le nombre de joueurs doit être entre 1 et 8!", ephemeral=True)
            return

        if max_players < min_players or max_players > 8:
            await interaction.response.send_message("❌ Le nombre maximum doit être ≥ minimum et ≤ 8!", ephemeral=True)
            return

        # Vérifier qu'il n'y a pas déjà une partie dans ce channel
        if interaction.channel_id in self.active_games:
            await interaction.response.send_message("❌ Une partie est déjà en cours dans ce salon!", ephemeral=True)
            return

        # Vérifier le balance du créateur
        profile = get_user_profile(interaction.user.id, interaction.guild.id)
        if profile['balance'] < buyin:
            await interaction.response.send_message(
                f"❌ Tu n'as pas assez de {CURRENCY_NAME}s! (Requis: {buyin:,}, Tu as: {profile['balance']:,})",
                ephemeral=True
            )
            return

        # Créer la partie
        game = PokerGame(
            guild_id=interaction.guild.id,
            creator=interaction.user,
            buyin=buyin,
            wait_time=wait_time,
            min_players=min_players,
            max_players=max_players
        )

        # Ajouter le créateur
        game.add_player(interaction.user)
        db.modify_balance(interaction.user.id, interaction.guild.id, -buyin, "poker buy-in")

        # Créer le lobby
        embed = create_lobby_embed(game)
        view = LobbyView(game)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        game.lobby_message = message

        # Enregistrer la partie
        self.active_games[interaction.channel_id] = game

        # Attendre puis commencer (ou jusqu'à ce que la table soit pleine)
        elapsed = 0
        while elapsed < wait_time:
            await asyncio.sleep(1)
            elapsed += 1

            # Démarrer si la table est pleine
            if len(game.players) >= max_players:
                break

        # Vérifier qu'on a assez de joueurs
        if len(game.players) < min_players:
            # Annuler et rembourser
            for player in game.players:
                db.modify_balance(player.user.id, interaction.guild.id, buyin, "poker cancelled")

            await interaction.channel.send(f"❌ Partie annulée - pas assez de joueurs! (Minimum: {min_players})")
            del self.active_games[interaction.channel_id]
            return

        # Commencer la partie!
        game.is_started = True
        await self.start_poker_game(interaction.channel, game)

    async def start_poker_game(self, channel: discord.TextChannel, game: PokerGame):
        """Commencer la partie de poker"""

        await channel.send(f"🎰 **La partie de poker commence!** Bonne chance à tous!")

        # Distribuer les cartes
        game.start_new_hand()

        # Envoyer les cartes privées à chaque joueur
        for player in game.players:
            try:
                cards_str = " ".join([str(card) for card in player.hand])
                await player.user.send(f"🎴 **Tes cartes:** {cards_str}")
            except:
                pass  # Si le joueur a bloqué les DMs

        # Phase Pre-flop
        await self.play_betting_round(channel, game, "Pre-Flop")

        # Vérifier si la main est terminée
        if len(game.get_players_in_hand()) == 1:
            await self.end_hand(channel, game)
            return

        # Flop (3 cartes)
        game.community_cards.extend(game.deck.deal(3))
        await self.play_betting_round(channel, game, "Flop")

        if len(game.get_players_in_hand()) == 1:
            await self.end_hand(channel, game)
            return

        # Turn (1 carte)
        game.community_cards.extend(game.deck.deal(1))
        await self.play_betting_round(channel, game, "Turn")

        if len(game.get_players_in_hand()) == 1:
            await self.end_hand(channel, game)
            return

        # River (1 carte)
        game.community_cards.extend(game.deck.deal(1))
        await self.play_betting_round(channel, game, "River")

        # Showdown
        await self.end_hand(channel, game)

    async def play_betting_round(self, channel: discord.TextChannel, game: PokerGame, phase: str):
        """Jouer un tour de mises"""

        # Reset current bets pour ce tour
        for player in game.players:
            player.current_bet = 0
        game.current_bet = 0

        # Déterminer l'ordre des joueurs (après le dealer)
        active_players = game.get_active_players()
        if not active_players:
            return

        # Continuer jusqu'à ce que tous aient misé la même somme
        betting_complete = False
        round_count = 0

        while not betting_complete and len(game.get_active_players()) > 1:
            round_count += 1

            for i, player in enumerate(game.players):
                # Skip si fold ou all-in
                if player.is_folded or player.is_all_in:
                    continue

                # Afficher l'état actuel
                embed = create_game_embed(game, phase)
                embed.set_footer(text=f"C'est au tour de {player.user.display_name}")

                # Créer les boutons d'action
                view = BettingView(game, player, self)
                msg = await channel.send(f"{player.user.mention}, c'est ton tour! (25 secondes)", embed=embed, view=view)

                # Attendre l'action du joueur (timeout 25s)
                await view.wait()

                # Vérifier si le joueur a timeout (auto-fold)
                if not view.action_taken and player.is_folded:
                    await channel.send(f"⏱️ {player.user.mention} n'a pas joué à temps et a été fold automatiquement!")

                # Supprimer le message
                try:
                    await msg.delete()
                except:
                    pass

                # Vérifier si tout le monde a fold
                if len(game.get_players_in_hand()) == 1:
                    return

            # Vérifier si le tour de mises est terminé
            # On vérifie les joueurs qui sont toujours dans la main (pas fold)
            players_in_hand = game.get_players_in_hand()

            # Si tout le monde a fold sauf 1, c'est terminé (déjà géré plus haut)
            if len(players_in_hand) <= 1:
                betting_complete = True
            else:
                # Vérifier que tous les joueurs qui peuvent encore jouer ont misé la même somme
                # Les joueurs all-in n'ont pas besoin de matcher
                players_who_can_bet = [p for p in players_in_hand if not p.is_all_in]

                if len(players_who_can_bet) == 0:
                    # Tout le monde est all-in, on passe à la prochaine phase
                    betting_complete = True
                elif len(players_who_can_bet) == 1:
                    # Un seul joueur peut encore jouer, le tour est terminé
                    betting_complete = True
                else:
                    # Vérifier que tous ont misé la même somme
                    bets = [p.current_bet for p in players_who_can_bet]
                    if len(set(bets)) == 1:
                        betting_complete = True
                    elif round_count > 20:  # Sécurité
                        betting_complete = True

    async def end_hand(self, channel: discord.TextChannel, game: PokerGame):
        """Terminer la main et distribuer le pot"""

        winners = game.determine_winners()

        # Partager le pot
        pot_share = game.pot // len(winners)

        embed = discord.Embed(
            title="🏆 Résultats du Poker",
            description=f"**Pot total:** {game.pot:,} {CURRENCY_NAME}s",
            color=discord.Color.gold()
        )

        # Afficher les cartes communes
        if game.community_cards:
            cards_str = " ".join([str(card) for card in game.community_cards])
            embed.add_field(name="🎴 Cartes communes", value=cards_str, inline=False)

        # Afficher les mains de tous les joueurs qui n'ont pas fold
        players_in = game.get_players_in_hand()
        if len(players_in) > 1:
            hands_text = []
            for player in players_in:
                hand_str = " ".join([str(card) for card in player.hand])
                rank, values = game.evaluate_hand(player)
                rank_name = rank.name.replace('_', ' ').title()
                hands_text.append(f"{player.user.mention}: {hand_str} - {rank_name}")

            embed.add_field(name="👥 Mains des joueurs", value="\n".join(hands_text), inline=False)

        # Afficher les gagnants
        winners_text = []
        for winner, rank, values in winners:
            # Redonner les chips au joueur (balance Skulls)
            db.modify_balance(winner.user.id, game.guild_id, pot_share, "poker win")

            # Mettre à jour les stats
            profile = get_user_profile(winner.user.id, game.guild_id)
            db.update_user_profile(
                winner.user.id,
                game.guild_id,
                games_played=profile['games_played'] + 1,
                games_won=profile['games_won'] + 1
            )

            # XP
            add_xp(winner.user.id, game.guild_id, 50)

            rank_name = rank.name.replace('_', ' ').title() if rank else "Tout le monde a fold"
            hand_str = " ".join([str(card) for card in winner.hand])
            winners_text.append(f"🏆 {winner.user.mention}\n**Main:** {hand_str}\n**Rang:** {rank_name}\n**Gain:** +{pot_share:,} {CURRENCY_NAME}s")

        # Mettre à jour les stats des perdants aussi
        for player in game.players:
            if not any(w[0].user.id == player.user.id for w in winners):
                profile = get_user_profile(player.user.id, game.guild_id)
                db.update_user_profile(
                    player.user.id,
                    game.guild_id,
                    games_played=profile['games_played'] + 1,
                    games_lost=profile['games_lost'] + 1
                )
                # XP pour participation
                add_xp(player.user.id, game.guild_id, 10)

        embed.add_field(name="🎉 Gagnant(s)", value="\n\n".join(winners_text), inline=False)

        await channel.send(embed=embed)

        # Nettoyer
        game.is_finished = True
        if channel.id in self.active_games:
            del self.active_games[channel.id]

async def setup(bot):
    await bot.add_cog(Poker(bot))
