import logging
from typing import TYPE_CHECKING

from pyminion.core import (
    Card,
    CardType,
    Expansion,
    Treasure,
    Victory,
    plural,
)
from pyminion.effects import (
    EffectAction,
    FuncPlayerCardGameDeckEffect,
    FuncPlayerGameEffect,
)
from pyminion.player import Player

if TYPE_CHECKING:
    from pyminion.core import AbstractDeck
    from pyminion.game import Game


logger = logging.getLogger()


class Marchland(Victory):
    """
    Worth 1VP per 3 Victory cards you have (round down).

    When you gain this, +1 Buy, and discard any number of cards for +$1 each.

    """

    def __init__(self):
        super().__init__("Marchland", 5, (CardType.Victory,))

    def score(self, player: Player) -> int:
        count = sum(
            1 for card in player.get_all_cards() if CardType.Victory in card.type
        )
        vp = count // 3
        return vp

    def on_gain_trigger(self, player: Player, card: Card, game: "Game", deck: "AbstractDeck") -> bool:
        return card.name == self.name

    def on_gain(self, player: Player, card: Card, game: "Game", deck: "AbstractDeck") -> None:
        player.state.buys += 1
        if len(player.hand) > 0:
            discard_cards = player.decider.discard_decision(
                "Enter the cards you would like to discard for +$1 each: ",
                self,
                player.hand.cards,
                player,
                game,
            )
            player.state.money += len(discard_cards)
            for card in discard_cards:
                player.discard(game, card)

    def set_up(self, game: "Game") -> None:
        effect = FuncPlayerCardGameDeckEffect(
            "Marchland: Gain",
            EffectAction.HandRemoveCards,
            self.on_gain,
            self.on_gain_trigger,
        )
        game.effect_registry.register_gain_effect(effect)


class Stash(Treasure):
    """
    +$2

    When shuffling this, you may look through your remaining deck,
    and may put this anywhere in the shuffled cards.

    """

    def __init__(self):
        super().__init__(name="Stash", cost=5, type=(CardType.Treasure,), money=2)

    def on_shuffle_trigger(self, player: Player, game: "Game") -> bool:
        count = sum(1 for c in player.deck if c.name == self.name)
        return count > 0

    def on_shuffle(self, player: Player, game: "Game") -> None:
        count = sum(1 for c in player.deck if c.name == self.name)

        for _ in range(count):
            player.deck.remove(self)

        len_deck = len(player.deck)
        if len_deck == 0:
            for _ in range(count):
                player.deck.add(self)
        else:
            for _ in range(count):
                len_deck = len(player.deck)
                index = player.decider.deck_position_decision(
                    prompt=f"Enter the deck position to put Stash (bottom = 1, top = {len_deck+1}): ",
                    card=self,
                    player=player,
                    game=game,
                    num_deck_cards=len_deck,
                )
                assert 0 <= index <= len_deck

                player.deck.cards.insert(index, self)

        p = plural("Stash", count)
        logger.info(f"{player} puts {count} {p} in their deck")

    def set_up(self, game: "Game") -> None:
        effect = FuncPlayerGameEffect(
            "Stash: Put in deck",
            EffectAction.Other,
            self.on_shuffle,
            self.on_shuffle_trigger,
        )
        game.effect_registry.register_shuffle_effect(effect)


marchland = Marchland()
stash = Stash()


promos_set = Expansion(
    "Promos",
    [
        marchland,
        stash,
    ],
)
