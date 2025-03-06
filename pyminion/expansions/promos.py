from typing import TYPE_CHECKING

from pyminion.core import (
    Card,
    CardType,
    Expansion,
    Victory,
)
from pyminion.effects import (
    EffectAction,
    FuncPlayerCardGameDeckEffect,
)
from pyminion.player import Player

if TYPE_CHECKING:
    from pyminion.core import AbstractDeck
    from pyminion.game import Game


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


marchland = Marchland()


promos_set = Expansion(
    "Promos",
    [
        marchland,
    ],
)
