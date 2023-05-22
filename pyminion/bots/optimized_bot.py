from typing import TYPE_CHECKING, List, Literal, Optional, Union, overload

from pyminion.bots.bot import Bot, BotDecider
from pyminion.core import CardType, Card, DeckCounter, Treasure, Victory
from pyminion.decider import Decider
from pyminion.exceptions import InvalidBotImplementation
from pyminion.expansions.base import duchy, estate, gold, silver
from pyminion.expansions.intrigue import Baron, Courtier, Lurker, Minion, Nobles, Pawn
from pyminion.player import Player

if TYPE_CHECKING:
    from pyminion.game import Game


class OptimizedBotDecider(BotDecider):
    """
    Implements opinionated logic for playing and reacting to all cards in the base set.

    The intention is to inherit from this class to make concrete bot implementations.
    If inheriting from this bot, it is possible to change the way that a single card is executed
    by overwriting the card specific method at the bottom of this file.

    """

    @staticmethod
    def get_best_victory_card(valid_cards: List[Card], player: Player) -> Union[Victory, None]:
        """
        Get the victory card that has the highest score.

        """

        best_score = 0
        best_victory = None
        for card in valid_cards:
            if CardType.Victory in card.type:
                assert isinstance(card, Victory)
                score = card.score(player)
                if best_victory is None or score > best_score:
                    best_victory = card
                    best_score = score

        return best_victory

    @staticmethod
    def sort_for_discard(cards: List[Card], actions: int, player: Player, game: "Game") -> List[Card]:
        """
        Sort list of cards from best discard candidate to worst discard candidate.
        First sort cards from lowest cost to highest cost. Then rearrange depending on remaining actions.
        If player has no remaining actions, prioritize discarding victory then action, then treasures.
        If player has remaining actions, prioritize discarding victory then treasure and action equally.

        """

        sorted_cards = sorted(cards, key=lambda card: card.get_cost(player, game))
        victory_cards = [
            card
            for card in sorted_cards
            if CardType.Victory in card.type or CardType.Curse in card.type
        ]
        non_victory_cards = [
            card
            for card in sorted_cards
            if CardType.Victory not in card.type and CardType.Curse not in card.type
        ]
        treasure_cards = [card for card in non_victory_cards if CardType.Treasure in card.type]
        action_cards = [
            card for card in non_victory_cards if CardType.Treasure not in card.type
        ]
        if actions == 0:
            return victory_cards + action_cards + treasure_cards
        else:
            return victory_cards + non_victory_cards

    def determine_trash_cards(
        self, valid_cards: List[Card], player: Player, game: "Game"
    ) -> List[Card]:
        """
        Determine which cards should be trashed:

        Always trash Curse
        Trash Estate if number of provinces in supply >= 5
        Trash Copper if money in deck > 3 (keep enough to buy silver)
        Finally, sort the cards as to prioritize trashing estate over copper

        """

        deck_money = player.get_deck_money()
        trash_cards = []
        for card in valid_cards:
            if CardType.Curse in card.type:
                trash_cards.append(card)
            elif (
                card.name == "Estate"
                and game.supply.pile_length(pile_name="Province") >= 5
            ):
                trash_cards.append(card)
            elif card.name == "Copper" and deck_money > 3:
                trash_cards.append(card)
                deck_money -= 1

        sorted_trash_cards = self.sort_for_discard(
            cards=trash_cards,
            actions=1,
            player=player,
            game=game,
        )

        return sorted_trash_cards

    def determine_optional_trash_cards(
        self, valid_cards: List[Card], player: Player, game: "Game"
    ) -> List[Card]:
        """
        Determine if there are any cards that would be ideal to trash:

        Always trash Curse
        Trash Estate if number of provinces in supply >= 5
        Trash Copper if money in deck > 3 (keep enough to buy silver)

        """

        trash_estate = game.supply.pile_length("Province") >= 5
        trash_copper = player.get_deck_money() > 3
        trash_cards: List[Card] = []
        for card in valid_cards:
            if CardType.Curse in card.type:
                trash_cards.append(card)
            elif trash_estate and card.name == "Estate":
                trash_cards.append(card)
            elif trash_copper and card.name == "Copper":
                trash_cards.append(card)

        sorted_trash_cards = self.sort_for_discard(
            cards=trash_cards,
            actions=player.state.actions,
            player=player,
            game=game,
        )

        return sorted_trash_cards

    def binary_decision(
        self,
        prompt: str,
        card: Card,
        player: "Player",
        game: "Game",
        relevant_cards: Optional[List[Card]] = None,
    ) -> bool:
        if card.name == "Moneylender":
            return self.moneylender(player=player, game=game)
        elif card.name == "Vassal":
            return self.vassal(player=player, game=game, relevant_cards=relevant_cards)
        elif card.name == "Sentry":
            return self.sentry(player=player, game=game, relevant_cards=relevant_cards, binary=True)
        elif card.name == "Library":
            return self.library(player=player, game=game, relevant_cards=relevant_cards)
        elif card.name == "Moat":
            return self.moat(player=player, game=game, relevant_cards=relevant_cards)
        elif card.name == "Diplomat":
            return self.diplomat(player, game, binary=True)
        elif card.name == "Masquerade":
            return self.masquerade(player, game, binary=True)
        elif card.name == "Mill":
            return self.mill(player, game, binary=True)
        elif card.name == "Mining Village":
            return self.mining_village(player, game)
        else:
            return super().binary_decision(prompt, card, player, game, relevant_cards)

    def multiple_option_decision(
        self,
        card: "Card",
        options: List[str],
        player: "Player",
        game: "Game",
        num_choices: int = 1,
        unique: bool = True,
    ) -> List[int]:
        if card.name == "Baron":
            ret = self.baron(player, game)
            return [ret]
        elif card.name == "Courtier":
            return self.courtier(player, game, num_choices=num_choices, options=True)
        elif card.name == "Lurker":
            ret = self.lurker(player, game, options=True)
            return [ret]
        elif card.name == "Minion":
            ret = self.minion(player, game)
            return [ret]
        elif card.name == "Nobles":
            ret = self.nobles(player, game)
            return [ret]
        elif card.name == "Pawn":
            return self.pawn(player, game)
        elif card.name == "Steward":
            ret = self.steward(player, game, options=True)
            return [ret]
        elif card.name == "Torturer":
            ret = self.torturer(player, game, options=True)
            return [ret]
        else:
            return super().multiple_option_decision(card, options, player, game, num_choices, unique)

    def discard_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_discard: int = 0,
        max_num_discard: int = -1,
    ) -> List["Card"]:
        if card.name == "Cellar":
            return self.cellar(player=player, game=game, valid_cards=valid_cards)
        elif card.name == "Poacher":
            return self.poacher(player=player, game=game, valid_cards=valid_cards, num_discard=min_num_discard)
        elif card.name == "Militia":
            return self.militia(player=player, game=game, valid_cards=valid_cards, num_discard=min_num_discard)
        elif card.name == "Sentry":
            return self.sentry(player=player, game=game, valid_cards=valid_cards, discard=True)
        elif card.name == "Diplomat":
            return self.diplomat(player, game, valid_cards, min_num_discard, discard=True)
        elif card.name == "Mill":
            return self.mill(player, game, discard=True)
        elif card.name == "Torturer":
            return self.torturer(player, game, discard=True)
        else:
            return super().discard_decision(prompt, card, valid_cards, player, game, min_num_discard, max_num_discard)

    def trash_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_trash: int = 0,
        max_num_trash: int = -1,
    ) -> List["Card"]:
        if card.name == "Remodel":
            ret = self.remodel(player=player, game=game, valid_cards=valid_cards, trash=True)
            return [ret]
        elif card.name == "Mine":
            ret = self.mine(player=player, game=game, valid_cards=valid_cards, trash=True)
            return [ret]
        elif card.name == "Chapel":
            return self.chapel(player=player, game=game, valid_cards=valid_cards)
        elif card.name == "Sentry":
            return self.sentry(player=player, game=game, valid_cards=valid_cards, trash=True)
        elif card.name == "Lurker":
            ret = self.lurker(player, game, valid_cards, trash=True)
            return [ret]
        elif card.name == "Masquerade":
            ret = self.masquerade(player, game, valid_cards, trash=True)
            return [ret]
        elif card.name == "Replace":
            ret = self.replace(player, game, trash=True)
            return [ret]
        elif card.name == "Steward":
            return self.steward(player, game, trash=True)
        elif card.name == "Trading Post":
            return self.trading_post(player, game)
        elif card.name == "Upgrade":
            ret = self.upgrade(player, game, trash=True)
            return [ret]
        else:
            return super().trash_decision(prompt, card, valid_cards, player, game, min_num_trash, max_num_trash)

    def gain_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_gain: int = 0,
        max_num_gain: int = -1,
    ) -> List["Card"]:
        if card.name == "Artisan":
            ret = self.artisan(player=player, game=game, gain=True)
            return [ret]
        elif card.name == "Workshop":
            ret = self.workshop(player=player, game=game)
            return [ret]
        elif card.name == "Remodel":
            ret = self.remodel(player=player, game=game, valid_cards=valid_cards, gain=True)
            return [ret]
        elif card.name == "Mine":
            ret = self.mine(player=player, game=game, valid_cards=valid_cards, gain=True)
            return [ret]
        elif card.name == "Ironworks":
            ret = self.ironworks(player, game, valid_cards)
            return [ret]
        elif card.name == "Lurker":
            ret = self.lurker(player, game, valid_cards, gain=True)
            return [ret]
        elif card.name == "Replace":
            ret = self.replace(player, game, gain=True)
            return [ret]
        elif card.name == "Swindler":
            ret = self.swindler(player, game)
            return [ret]
        elif card.name == "Upgrade":
            ret = self.upgrade(player, game, gain=True)
            return [ret]
        else:
            return super().gain_decision(prompt, card, valid_cards, player, game, min_num_gain, max_num_gain)

    def topdeck_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_topdeck: int = 0,
        max_num_topdeck: int = -1,
    ) -> List["Card"]:
        if card.name == "Artisan":
            ret = self.artisan(player=player, game=game, valid_cards=valid_cards, topdeck=True)
            return [ret]
        elif card.name == "Harbinger":
            ret = self.harbinger(player=player, game=game, valid_cards=valid_cards)
            return [] if ret is None else [ret]
        elif card.name == "Bureaucrat":
            ret = self.bureaucrat(player=player, game=game, valid_cards=valid_cards)
            return [ret]
        elif card.name == "Courtyard":
            ret = self.courtyard(player, game, valid_cards)
            return [ret]
        elif card.name == "Patrol":
            return self.patrol(player, game, valid_cards)
        elif card.name == "Secret Passage":
            ret = self.secret_passage(player, game, topdeck=True)
            return [ret]
        else:
            return super().topdeck_decision(prompt, card, valid_cards, player, game, min_num_topdeck, max_num_topdeck)

    def deck_position_decision(
        self,
        prompt: str,
        card: "Card",
        player: "Player",
        game: "Game",
        num_deck_cards: int,
    ) -> int:
        if card.name == "Secret Passage":
            return self.secret_passage(player, game, pos=True)
        else:
            return super().deck_position_decision(prompt, card, player, game, num_deck_cards)

    def reveal_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_reveal: int = 0,
        max_num_reveal: int = -1,
    ) -> List["Card"]:
        if card.name == "Courtier":
            ret = self.courtier(player, game, valid_cards=valid_cards, reveal=True)
            return [ret]
        else:
            return super().reveal_decision(prompt, card, valid_cards, player, game, min_num_reveal, max_num_reveal)

    def pass_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_pass: int = 0,
        max_num_pass: int = -1,
    ) -> List["Card"]:
        if card.name == "Masquerade":
            ret = self.masquerade(player, game, valid_cards, pass_=True)
            return [ret]
        else:
            return super().pass_decision(prompt, card, valid_cards, player, game, min_num_pass, max_num_pass)

    def name_card_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_name: int = 0,
        max_num_name: int = -1,
    ) -> List["Card"]:
        if card.name == "Wishing Well":
            ret = self.wishing_well(player, game)
            return [ret]
        else:
            return super().name_card_decision(prompt, card, valid_cards, player, game, min_num_name, max_num_name)

    def multi_play_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        required: bool = True,
    ) -> Optional["Card"]:
        if card.name == "Throne Room":
            return self.throne_room(player=player, game=game, valid_cards=valid_cards)
        else:
            return super().multi_play_decision(prompt, card, valid_cards, player, game, required)

    # CARD SPECIFIC IMPLEMENTATIONS

    def moneylender(self, player: "Player", game: "Game") -> bool:
        return True

    def vassal(self, player: "Player", game: "Game", relevant_cards: Optional[List[Card]]) -> bool:
        return True

    @overload
    def sentry(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        relevant_cards: Optional[List[Card]] = None,
        trash: Literal[True] = True,
        discard: Literal[False] = False,
        binary: Literal[False] = False,
    ) -> List[Card]:
        ...

    @overload
    def sentry(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        relevant_cards: Optional[List[Card]] = None,
        trash: Literal[False] = False,
        discard: Literal[True] = True,
        binary: Literal[False] = False,
    ) -> List[Card]:
        ...

    @overload
    def sentry(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        relevant_cards: Optional[List[Card]] = None,
        trash: Literal[False] = False,
        discard: Literal[False] = False,
        binary: Literal[True] = True,
    ) -> bool:
        ...

    def sentry(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        relevant_cards: Optional[List[Card]] = None,
        trash: bool = False,
        discard: bool = False,
        binary: bool = False,
    ) -> Union[List[Card], bool]:
        if trash:
            if not valid_cards:
                return []
            return self.determine_trash_cards(
                valid_cards=valid_cards, player=player, game=game
            )
        if discard:
            if not valid_cards:
                return []
            return [
                card
                for card in valid_cards
                if card.name == "Copper"
                or CardType.Victory in card.type
                or CardType.Curse in card.type
            ]
        if binary:
            return False

        raise InvalidBotImplementation(
            "Either gain, topdeck or binary must be true when playing sentry"
        )

    def library(self, player: "Player", game: "Game", relevant_cards: Optional[List[Card]]) -> bool:
        if player.state.actions == 0:
            return True
        else:
            return False

    def cellar(self, player: "Player", game: "Game", valid_cards: List[Card]) -> List[Card]:
        return [
            card
            for card in valid_cards
            if card.name == "Copper" or CardType.Victory in card.type or CardType.Curse in card.type
        ]

    def moat(self, player: "Player", game: "Game", relevant_cards: Optional[List[Card]]) -> bool:
        return True

    def poacher(
        self, player: "Player", game: "Game", valid_cards: List[Card], num_discard: Optional[int]
    ) -> List[Card]:
        if not num_discard:
            return []
        discard_order = self.sort_for_discard(
            cards=valid_cards, actions=player.state.actions, player=player, game=game
        )
        return discard_order[:num_discard]

    def militia(
        self, player: "Player", game: "Game", valid_cards: List[Card], num_discard: Optional[int]
    ) -> List[Card]:
        if not num_discard:
            return []
        discard_order = self.sort_for_discard(
            cards=valid_cards, actions=player.state.actions, player=player, game=game
        )
        return discard_order[:num_discard]

    def remodel(
        self, player: "Player", game: "Game", valid_cards: List[Card], trash: bool = False, gain: bool = False
    ) -> Card:
        if trash:
            min_price_card = min(valid_cards, key=lambda card: card.get_cost(player, game))
            return min_price_card

        if gain:
            max_price_card = max(valid_cards, key=lambda card: card.get_cost(player, game))
            return max_price_card

        raise InvalidBotImplementation(
            "Either gain or trash must be true when playing remodel"
        )

    def mine(
        self, player: "Player", game: "Game", valid_cards: List[Card], trash: bool = False, gain: bool = False
    ) -> Card:
        if trash:
            min_price_card = min(valid_cards, key=lambda card: card.get_cost(player, game))
            return min_price_card

        if gain:
            max_price_card = max(valid_cards, key=lambda card: card.get_cost(player, game))
            return max_price_card

        raise InvalidBotImplementation(
            "Either gain or trash must be true when playing mine"
        )

    def chapel(self, player: "Player", game: "Game", valid_cards: List[Card]) -> List[Card]:
        trash_cards = self.determine_trash_cards(
            valid_cards=valid_cards, player=player, game=game
        )
        while len(trash_cards) > 4:
            trash_cards.pop()
        return trash_cards

    def artisan(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        gain: bool = False,
        topdeck: bool = False,
    ) -> Card:
        if topdeck:
            for card in player.hand.cards:
                if CardType.Action in card.type and player.state.actions == 0:
                    return card
            else:
                return player.hand.cards[-1]
        if gain:
            if game.supply.pile_length(pile_name="Province") < 5:
                return duchy
            else:
                return silver

        raise InvalidBotImplementation(
            "Either gain or topdeck must be true when playing artisan"
        )

    def workshop(
        self,
        player: "Player",
        game: "Game",
    ) -> Card:
        if game.supply.pile_length(pile_name="Province") < 3:
            return estate
        else:
            return silver

    def harbinger(
        self,
        player: "Player",
        game: "Game",
        valid_cards: List[Card],
    ) -> Optional[Card]:
        # Do not topdeck victory cards
        best_topdeck = [card for card in valid_cards if CardType.Victory not in card.type]
        if not best_topdeck:
            return None
        # Topdeck highest price card if price > 2
        max_price_card = max(best_topdeck, key=lambda card: card.get_cost(player, game))
        if max_price_card.get_cost(player, game) > 2:
            return max_price_card
        else:
            return None

    def bureaucrat(
        self,
        player: "Player",
        game: "Game",
        valid_cards: List[Card],
    ) -> Card:
        sorted_cards = sorted(valid_cards, key=lambda card: card.get_cost(player, game))
        return sorted_cards[0]

    def throne_room(self, player: "Player", game: "Game", valid_cards: List[Card]) -> Card:
        # Double play most expensive card
        max_price_card = max(valid_cards, key=lambda card: card.get_cost(player, game))
        return max_price_card

    def baron(
        self,
        player: "Player",
        game: "Game",
    ) -> int:
        return Baron.Choice.DiscardEstate

    @overload
    def courtier(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        num_choices: int = 0,
        reveal: Literal[True] = True,
        options: Literal[False] = False,
    ) -> Card:
        ...

    @overload
    def courtier(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        num_choices: int = 0,
        reveal: Literal[False] = False,
        options: Literal[True] = True,
    ) -> List[int]:
        ...

    def courtier(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        num_choices: int = 0,
        reveal: bool = False,
        options: bool = False,
    ) -> Union[Card, List[int]]:
        if reveal:
            assert valid_cards is not None
            # find the card with the most types
            num_types = 0
            reveal_card = valid_cards[0]
            for c in valid_cards:
                if len(c.type) > num_types:
                    num_types = len(c.type)
                    reveal_card = c
            return reveal_card
        elif options:
            assert num_choices > 0
            counter = DeckCounter(player.get_all_cards())
            gold_count = counter[gold]
            has_actions = any(CardType.Action in c.type for c in player.hand.cards)

            # prioritize choices
            choices: List[int] = []
            if has_actions:
                choices.append(Courtier.Choice.Action)
            if gold_count < 4:
                choices.append(Courtier.Choice.GainGold)
            choices.append(Courtier.Choice.Money)

            # add remaining choices
            for c in Courtier.Choice:
                if c.value not in choices:
                    choices.append(c.value)

            choices = choices[:num_choices]
            return choices
        else:
            raise InvalidBotImplementation(
                "Either reveal or options must be true when playing courier"
            )

    def courtyard(
        self,
        player: "Player",
        game: "Game",
        valid_cards: List[Card],
    ) -> Card:
        if player.state.actions == 0:
            for card in valid_cards:
                if CardType.Action in card.type:
                    return card

        return valid_cards[-1]

    @overload
    def diplomat(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Union[List[Card], None] = None,
        num_discard: int = 0,
        binary: Literal[True] = True,
        discard: Literal[False] = False,
    ) -> bool:
        ...

    @overload
    def diplomat(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Union[List[Card], None] = None,
        num_discard: int = 0,
        binary: Literal[False] = False,
        discard: Literal[True] = True,
    ) -> List[Card]:
        ...

    def diplomat(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Union[List[Card], None] = None,
        num_discard: int = 0,
        binary: bool = False,
        discard: bool = False,
    ) -> Union[bool, List[Card]]:
        if binary:
            return True
        elif discard:
            assert valid_cards is not None
            discard_order = self.sort_for_discard(
                cards=valid_cards, actions=player.state.actions, player=player, game=game
            )
            return discard_order[:num_discard]
        else:
            raise InvalidBotImplementation(
                "Either binary or discard must be true when playing diplomat"
            )

    def ironworks(
        self,
        player: "Player",
        game: "Game",
        valid_cards: List[Card],
    ) -> Card:
        best_victory = self.get_best_victory_card(valid_cards, player)
        if game.supply.pile_length(pile_name="Province") < 3 and best_victory is not None:
            return best_victory
        else:
            return silver

    @overload
    def lurker(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Union[List[Card], None] = None,
        options: Literal[True] = True,
        trash: Literal[False] = False,
        gain: Literal[False] = False,
    ) -> int:
        ...

    @overload
    def lurker(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Union[List[Card], None] = None,
        options: Literal[False] = False,
        trash: Literal[True] = True,
        gain: Literal[False] = False,
    ) -> Card:
        ...

    @overload
    def lurker(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Union[List[Card], None] = None,
        options: Literal[False] = False,
        trash: Literal[False] = False,
        gain: Literal[True] = True,
    ) -> Card:
        ...

    def lurker(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Union[List[Card], None] = None,
        options: bool = False,
        trash: bool = False,
        gain: bool = False,
    ) -> Union[int, Card]:
        if options:
            if any(CardType.Action in c.type for c in game.trash.cards):
                return Lurker.Choice.GainAction
            else:
                return Lurker.Choice.TrashAction
        elif trash or gain:
            assert valid_cards is not None
            max_price_card = max(valid_cards, key=lambda card: card.get_cost(player, game))
            return max_price_card
        else:
            raise InvalidBotImplementation(
                "Either options, trash, or gain must be true when playing lurker"
            )

    @overload
    def masquerade(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        pass_: Literal[True] = True,
        binary: Literal[False] = False,
        trash: Literal[False] = False,
    ) -> Card:
        ...

    @overload
    def masquerade(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        pass_: Literal[False] = False,
        binary: Literal[True] = True,
        trash: Literal[False] = False,
    ) -> bool:
        ...

    @overload
    def masquerade(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        pass_: Literal[False] = False,
        binary: Literal[False] = False,
        trash: Literal[True] = True,
    ) -> Card:
        ...

    def masquerade(
        self,
        player: "Player",
        game: "Game",
        valid_cards: Optional[List[Card]] = None,
        pass_: bool = False,
        binary: bool = False,
        trash: bool = False,
    ) -> Union[bool, Card]:
        if pass_:
            assert valid_cards is not None
            cards = self.determine_trash_cards(valid_cards, player, game)
            return cards[0]
        elif binary:
            cards = self.determine_optional_trash_cards(player.hand.cards, player, game)
            return len(cards) > 0
        elif trash:
            assert valid_cards is not None
            cards = self.determine_trash_cards(valid_cards, player, game)
            return cards[0]
        else:
            raise InvalidBotImplementation(
                "Either pass_, binary, or trash must be true when playing masquerade"
            )

    @overload
    def mill(
        self,
        player: "Player",
        game: "Game",
        binary: Literal[True] = True,
        discard: Literal[False] = False,
    ) -> bool:
        ...

    @overload
    def mill(
        self,
        player: "Player",
        game: "Game",
        binary: Literal[False] = False,
        discard: Literal[True] = True,
    ) -> List[Card]:
        ...

    def mill(
        self,
        player: "Player",
        game: "Game",
        binary: bool = False,
        discard: bool = False,
    ) -> Union[bool, List[Card]]:
        actions = player.state.actions
        cards = self.sort_for_discard(player.hand.cards, actions, player, game)
        cards = cards[:2]
        if binary:
            if len(cards) < 2:
                return False
            money = 0
            for card in cards:
                if CardType.Treasure in card.type:
                    assert isinstance(card, Treasure)
                    money += card.money
            # discard cards if they provide less money than the
            # +$2 mill will give for discarding
            return money < 2
        elif discard:
            return cards
        else:
            raise InvalidBotImplementation(
                "Either binary or discard must be true when playing mill"
            )

    def mining_village(
        self,
        player: "Player",
        game: "Game",
    ) -> bool:
        return game.supply.pile_length("Province") < 3

    def minion(
        self,
        player: "Player",
        game: "Game",
    ) -> int:
        has_action_cards = False
        hand_money = 0
        for card in player.hand.cards:
            if CardType.Action in card.type:
                has_action_cards = True
            if CardType.Treasure in card.type:
                assert isinstance(card, Treasure)
                hand_money += card.money

        # don't discard hand if we can play more actions or if we have money in hand
        if (has_action_cards and player.state.actions > 0) or hand_money >= 3:
            return Minion.Choice.Money
        return Minion.Choice.DiscardDrawAttack

    def nobles(
        self,
        player: "Player",
        game: "Game",
    ) -> int:
        action_card_count = sum(1 for c in player.hand.cards if CardType.Action in c.type)
        if action_card_count > player.state.actions:
            return Nobles.Choice.Actions
        return Nobles.Choice.Cards

    def patrol(
        self,
        player: "Player",
        game: "Game",
        valid_cards: List[Card],
    ) -> List[Card]:
        cards = sorted(
            valid_cards,
            key=lambda card: card.get_cost(player, game),
        )
        return cards

    def pawn(
        self,
        player: "Player",
        game: "Game",
    ) -> List[int]:
        action_card_count = 0
        total_money = player.state.money
        for card in player.hand.cards:
            if CardType.Action in card.type:
                action_card_count += 1
            if CardType.Treasure in card.type:
                assert isinstance(card, Treasure)
                total_money += card.money

        choices: List[int] = []
        if action_card_count > player.state.actions:
            choices.append(Pawn.Choice.Action)

        if total_money < 2:
            choices.append(Pawn.Choice.Money)
        elif total_money > 8:
            choices.append(Pawn.Choice.Buy)

        if len(choices) < 2:
            choices.append(Pawn.Choice.Card)
        if len(choices) < 2:
            choices.append(Pawn.Choice.Money)

        return choices

    def replace(
        self,
        player: "Player",
        game: "Game",
        trash: bool = False,
        gain: bool = False,
    ) -> Card:
        pass # TODO

    @overload
    def secret_passage(
        self,
        player: "Player",
        game: "Game",
        topdeck: Literal[True] = True,
        pos: Literal[False] = False,
    ) -> Card:
        ...

    @overload
    def secret_passage(
        self,
        player: "Player",
        game: "Game",
        topdeck: Literal[False] = False,
        pos: Literal[True] = True,
    ) -> int:
        ...

    def secret_passage(
        self,
        player: "Player",
        game: "Game",
        topdeck: bool = False,
        pos: bool = False,
    ) -> Union[Card, int]:
        pass # TODO

    @overload
    def steward(
        self,
        player: "Player",
        game: "Game",
        options: Literal[True] = True,
        trash: Literal[False] = False,
    ) -> int:
        ...

    @overload
    def steward(
        self,
        player: "Player",
        game: "Game",
        options: Literal[False] = False,
        trash: Literal[True] = True,
    ) -> List[Card]:
        ...

    def steward(
        self,
        player: "Player",
        game: "Game",
        options: bool = False,
        trash: bool = False,
    ) -> Union[int, List[Card]]:
        pass # TODO

    def swindler(
        self,
        player: "Player",
        game: "Game",
    ) -> Card:
        pass # TODO

    @overload
    def torturer(
        self,
        player: "Player",
        game: "Game",
        options: Literal[True] = True,
        discard: Literal[False] = False,
    ) -> int:
        ...

    @overload
    def torturer(
        self,
        player: "Player",
        game: "Game",
        options: Literal[False] = False,
        discard: Literal[True] = True,
    ) -> List[Card]:
        ...

    def torturer(
        self,
        player: "Player",
        game: "Game",
        options: bool = False,
        discard: bool = False,
    ) -> Union[int, List[Card]]:
        pass # TODO

    def trading_post(
        self,
        player: "Player",
        game: "Game",
    ) -> List[Card]:
        pass # TODO

    def upgrade(
        self,
        player: "Player",
        game: "Game",
        trash: bool = False,
        gain: bool = False,
    ) -> Card:
        pass # TODO

    def wishing_well(
        self,
        player: "Player",
        game: "Game",
    ) -> Card:
        pass # TODO


class OptimizedBot(Bot):
    """
    Bot with logic for playing and reacting to all cards.

    """

    def __init__(
        self,
        decider: Optional[Decider] = None,
        player_id: str = "bot",
    ):
        decider = decider if decider else OptimizedBotDecider()
        super().__init__(decider=decider, player_id=player_id)
