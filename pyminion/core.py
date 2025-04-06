from collections import Counter
from enum import Enum, unique
import logging
import random
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator

from pyminion.exceptions import CardNotFound, EmptyPile, InsufficientActions

if TYPE_CHECKING:
    from pyminion.game import Game
    from pyminion.player import Player


logger = logging.getLogger()


class Cost:
    """
    The cost of a card in money and/or potions.

    """
    def __init__(self, money: int = 0, potions: int = 0):
        assert money >= 0
        assert 0 <= potions <= 1
        self._money = money
        self._potions = potions

    def __repr__(self) -> str:
        return f"Cost({self._money}, {self._potions})"

    def __str__(self) -> str:
        s = ""
        if self._money > 0 or self._potions == 0:
            s += f"${self._money}"
        if self._potions > 0:
            s += "P"
        return s

    def __format__(self, format_spec: str) -> str:
        s = str(self)
        fs = f"{s:{format_spec}}"
        return fs

    def __hash__(self) -> int:
        h = hash((self._money, self._potions))
        return h

    @staticmethod
    def _to_tuple(obj: "int|Cost") -> tuple[int, int]:
        if isinstance(obj, int):
            return (obj, 0)
        return (obj._money, obj._potions)

    def __eq__(self, other: "int|Cost") -> bool:
        if isinstance(other, int):
            return self._money == other and self._potions == 0
        else:
            return self._money == other._money and self._potions == other._potions

    def __ne__(self, other: "int|Cost") -> bool:
        if isinstance(other, int):
            return self._money != other or self._potions != 0
        else:
            return self._money != other._money or self._potions != other._potions

    def __lt__(self, other: "int|Cost") -> bool:
        other_money, other_potions = self._to_tuple(other)
        return (
            self._money < other_money and self._potions <= other_potions
        ) or (
            self._money == other_money and self._potions < other_potions
        )

    def __le__(self, other: "int|Cost") -> bool:
        other_money, other_potions = self._to_tuple(other)
        return self._money <= other_money and self._potions <= other_potions

    def __gt__(self, other: "int|Cost") -> bool:
        other_money, other_potions = self._to_tuple(other)
        return (
            self._money > other_money and self._potions >= other_potions
        ) or (
            self._money == other_money and self._potions > other_potions
        )

    def __ge__(self, other: "int|Cost") -> bool:
        other_money, other_potions = self._to_tuple(other)
        return self._money >= other_money and self._potions >= other_potions

    def __add__(self, other: int) -> "Cost":
        new_money = max(0, self._money + other)
        new_cost = Cost(new_money, self._potions)
        return new_cost

    def __radd__(self, other: int) -> "Cost":
        return self + other

    def __sub__(self, other: int) -> "Cost":
        new_money = max(0, self._money - other)
        new_cost = Cost(new_money, self._potions)
        return new_cost

    @property
    def money(self):
        return self._money

    @property
    def potions(self):
        return self._potions


class Buyable:
    """
    Base class representing things that can be bought (e.g. cards, events)

    """
    def __init__(self, name: str, cost: int|Cost):
        self.name = name
        if isinstance(cost, int):
            self._base_cost = Cost(cost)
        else:
            self._base_cost = cost

    @property
    def base_cost(self) -> Cost:
        return self._base_cost

    def get_cost(self, player: "Player", game: "Game") -> Cost:
        return self._base_cost

    def buy(self, player: "Player", game: "Game", source: "AbstractDeck|None"=None) -> None:
        pass


@unique
class CardType(Enum):
    """
    Enum class for all card types that are currently used in the implemented expansions

    """
    Treasure = 1
    Victory = 2
    Curse = 3
    Action = 4
    Attack = 5
    Reaction = 6
    Duration = 7
    Command = 8


class Card(Buyable):

    """
    Base class representing a dominion card

    """

    def __init__(self, name: str, cost: int|Cost, type: tuple[CardType, ...]):
        super().__init__(name, cost)
        self.type = type

    def __repr__(self) -> str:
        return self.name

    def get_cost(self, player: "Player", game: "Game") -> Cost:
        if game.card_cost_reduction > 0:
            return self._base_cost - game.card_cost_reduction
        return self._base_cost

    def buy(self, player: "Player", game: "Game", source: "AbstractDeck|None"=None) -> None:
        if source is None:
            source = game.supply.get_pile_by_card(self.name)

        if player.possessing_player is None:
            source.remove(self)
            player.discard_pile.add(self)
            player.current_turn_gains.append((game.current_phase, self))
            game.effect_registry.on_buy(player, self, game, player.discard_pile)
        else:
            player.possessing_player.gain(self, game, destination=player.possessing_player.discard_pile, source=source)

    def get_pile_starting_count(self, game: "Game") -> int:
        return 10

    def set_up(self, game: "Game") -> None:
        pass


class ScoreCard(Card):
    def __init__(self, name: str, cost: int|Cost, type: tuple[CardType, ...]):
        super().__init__(name, cost, type)

    def score(self, player: "Player") -> int:
        """
        Specific score method unique to card

        """
        raise NotImplementedError(f"Score method must be implemented for {self.name}")


class Victory(ScoreCard):
    def __init__(self, name: str, cost: int|Cost, type: tuple[CardType, ...]):
        super().__init__(name, cost, type)

    def get_pile_starting_count(self, game: "Game") -> int:
        num_players = len(game.players)
        if num_players == 1:
            return 5
        elif num_players == 2:
            return 8
        else:
            return 12


class Treasure(Card):
    def __init__(self, name: str, cost: int|Cost, type: tuple[CardType, ...], money: int):
        super().__init__(name, cost, type)
        self.money = money

    def play(self, player: "Player", game: "Game") -> None:
        """
        Specific play method unique to each treasure card

        """
        player.playmat.add(self)
        player.hand.remove(self)
        player.state.money += self.money


class Action(Card):
    def __init__(
        self,
        name: str,
        cost: int|Cost,
        type: tuple[CardType, ...],
        actions: int = 0,
        draw: int = 0,
        money: int = 0,
        buys: int = 0,
        discard: int = 0,
    ):
        super().__init__(name, cost, type)
        self.actions = actions
        self.draw = draw
        self.money = money
        self.buys = buys
        self.discard = discard

    def play(self, player: "Player", game: "Game", generic_play: bool = True) -> None:
        """
        Specific play method unique to each action card

        """
        logger.info(f"{player} plays {self}")

        if generic_play:
            self.generic_play(player)

        if self.draw > 0:
            player.draw(self.draw)

        player.state.actions += self.actions
        player.state.money += self.money
        player.state.buys += self.buys

        if self.discard > 0 and len(player.hand) > 0:
            if len(player.hand) <= self.discard:
                discard_cards = player.hand.cards[:]
            else:
                discard_cards = player.decider.discard_decision(
                    prompt=f"Discard {self.discard} card(s) from your hand: ",
                    buyable=self,
                    valid_cards=player.hand.cards,
                    player=player,
                    game=game,
                    min_num_discard=self.discard,
                    max_num_discard=self.discard,
                )
                assert len(discard_cards) == self.discard

            for discard_card in discard_cards:
                player.discard(game, discard_card)

    def generic_play(self, player: "Player") -> None:
        """
        Generic play method that gets executes for all action cards

        """
        if player.state.actions < 1:
            raise InsufficientActions(
                f"{player.player_id}: Not enough actions to play {self.name}"
            )

        player.playmat.add(self)
        player.hand.remove(self)
        player.state.actions -= 1

    def multi_play(self, player: "Player", game: "Game", multi_play_card: Card, state: Any, generic_play: bool = True) -> Any:
        """
        Called by "Throne Room variants" to play a card multiple times.
        By default this just calls self.play() but can be overridden by derived
        cards to implement different behavior.

        """
        self.play(player, game, generic_play)
        return None


class DeckCounter(Counter):
    def __str__(self):
        return ", ".join(f"{value} {key}" for key, value in (self).items())


class AbstractDeck:
    """
    Base class representing a generic list of dominion cards

    """

    def __init__(
            self,
            cards: list[Card]|None = None,
            on_add: Callable[[Card], None]|None = None,
            on_remove: Callable[[Card], None]|None = None,
    ):
        if cards:
            self.cards = cards
        else:
            self.cards = []
        self.on_add = on_add
        self.on_remove = on_remove

    def __repr__(self):
        return str(DeckCounter(self.cards))

    def __len__(self) -> int:
        return len(self.cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(self.cards)

    def add(self, card: Card) -> None:
        self.cards.append(card)
        if self.on_add is not None:
            self.on_add(card)

    def remove(self, card: Card) -> Card:
        self.cards.remove(card)
        if self.on_remove is not None:
            self.on_remove(card)
        return card

    def move_to(self, destination: "AbstractDeck") -> None:
        if destination.on_add is None and self.on_remove is None:
            destination.cards += self.cards
            self.cards = []
        else:
            cards = self.cards[:] # copy cards that are being moved
            destination.cards += self.cards
            self.cards = []

            if destination.on_add is not None:
                for card in cards:
                    destination.on_add(card)

            if self.on_remove is not None:
                for card in cards:
                    self.on_remove(card)


class Deck(AbstractDeck):
    def __init__(
            self,
            cards: list[Card]|None = None,
            on_add: Callable[[Card], None]|None = None,
            on_remove: Callable[[Card], None]|None = None,
            on_shuffle: Callable[[], None]|None = None,
    ):
        super().__init__(cards, on_add, on_remove)
        self.on_shuffle = on_shuffle

    def draw(self) -> Card:
        drawn_card = self.cards.pop()
        if self.on_remove is not None:
            self.on_remove(drawn_card)
        return drawn_card

    def shuffle(self) -> None:
        random.shuffle(self.cards)
        if self.on_shuffle is not None:
            self.on_shuffle()


class DiscardPile(AbstractDeck):
    def __init__(self, cards: list[Card]|None = None):
        super().__init__(cards)


class Hand(AbstractDeck):
    def __init__(
            self,
            cards: list[Card]|None = None,
            on_add: Callable[[Card], None]|None = None,
            on_remove: Callable[[Card], None]|None = None,
    ):
        super().__init__(cards, on_add, on_remove)


class Pile(AbstractDeck):
    def __init__(self, cards: list[Card], name: str|None = None):
        super().__init__(cards)
        assert len(cards) > 0

        self._unique_cards: list[Card] = []
        all_names: set[str] = set()
        unique_names: list[str] = []
        for card in cards:
            card_name = card.name
            if card_name not in all_names:
                unique_names.append(card_name)
                all_names.add(card_name)
                self._unique_cards.append(card)
        unique_names.reverse()

        if name is not None:
            self._name = name
        else:
            self._name = "/".join(unique_names)

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_cards(self) -> list[Card]:
        return self._unique_cards

    def add_bottom(self, card: Card) -> None:
        """
        Add a card to the bottom of the pile.

        """
        self.cards.insert(0, card)

    def remove(self, card: Card) -> Card:
        if len(self.cards) < 1:
            raise EmptyPile(f"{self.name} pile is empty, cannot gain card")
        if card.name != self.cards[-1].name:
            raise CardNotFound(f"Cannot gain {card.name} as it is not the top card of the pile")

        self.cards.pop()
        if self.on_remove is not None:
            self.on_remove(card)
        return card

    def get_top(self) -> Card:
        """
        Returns the top card of the pile without removing it.

        """
        if len(self.cards) < 1:
            raise EmptyPile(f"{self.name} pile is empty, cannot get top card")

        return self.cards[-1]


class Playmat(AbstractDeck):
    def __init__(self, cards: list[Card]|None = None):
        super().__init__(cards)


class Trash(AbstractDeck):
    def __init__(self, cards: list[Card]|None = None):
        super().__init__(cards)


class Event(Buyable):
    """
    Base class representing a dominion event

    """

    def __repr__(self) -> str:
        return self.name


class Expansion:
    """
    Contains the cards in an expansion.

    """
    def __init__(
        self,
        name: str,
        kingdom_cards: list[Card|list[Card]],
        events: list[Event]|None = None,
    ):
        self._name = name
        self._kingdom_cards = [
            [c] if isinstance(c, Card) else c for c in kingdom_cards
        ]
        self._events = [] if events is None else events

    @property
    def name(self) -> str:
        return self._name

    @property
    def kingdom_cards(self) -> list[list[Card]]:
        return self._kingdom_cards

    @property
    def events(self) -> list[Event]:
        return self._events


def plural(word: str, count: int) -> str:
    """
    Makes a word plural if needed based on the count.

    """
    if count == 1:
        return word

    if word[-2:] == "sh":
        end = "es"
    else:
        end = "s"

    return word + end


def get_action_cards(cards: Iterable[Card]) -> Iterator[Action]:
    """
    Returns an iterator over the action cards in a Card iterable.

    """
    for card in cards:
        if CardType.Action in card.type:
            assert isinstance(card, Action)
            yield card


def get_treasure_cards(cards: Iterable[Card]) -> Iterator[Treasure]:
    """
    Returns an iterator over the treasure cards in a Card iterable.

    """
    for card in cards:
        if CardType.Treasure in card.type:
            assert isinstance(card, Treasure)
            yield card


def get_victory_cards(cards: Iterable[Card]) -> Iterator[Victory]:
    """
    Returns an iterator over the victory cards in a Card iterable.

    """
    for card in cards:
        if CardType.Victory in card.type:
            assert isinstance(card, Victory)
            yield card


def get_score_cards(cards: Iterable[Card]) -> Iterator[ScoreCard]:
    """
    Returns an iterator over the victory and curse cards in a Card iterable.

    """
    for card in cards:
        if CardType.Victory in card.type or CardType.Curse in card.type:
            assert isinstance(card, ScoreCard)
            yield card
