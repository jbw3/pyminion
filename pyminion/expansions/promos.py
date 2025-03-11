import logging
from typing import TYPE_CHECKING, Any

from pyminion.core import (
    AbstractDeck,
    Action,
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
    PlayerCardGameEffect,
)
from pyminion.player import Player

if TYPE_CHECKING:
    from pyminion.game import Game


logger = logging.getLogger()


class Envoy(Action):
    """
    Reveal the top 5 cards of your deck. The player to your left chooses one.
    Discard that one and put the rest into your hand.

    """

    def __init__(self):
        super().__init__(name="Envoy", cost=4, type=(CardType.Action,))

    def play(self, player: Player, game: "Game", generic_play: bool = True) -> None:

        super().play(player, game, generic_play)

        revealed = AbstractDeck()
        player.draw(5, revealed, silent=True)
        player.reveal(revealed, game)

        if len(revealed) == 0:
            return

        if len(revealed) == 1:
            discard_card = revealed.cards[0]
        else:
            left_player = game.get_left_player(player)
            discard_cards = left_player.decider.discard_decision(
                f"Enter a card for {player.player_id} to discard: ",
                self,
                revealed.cards,
                player,
                game,
                min_num_discard=1,
                max_num_discard=1,
            )
            assert len(discard_cards) == 1
            discard_card = discard_cards[0]

        player.discard(game, discard_card, revealed)
        revealed.move_to(player.hand)


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

    def on_gain_trigger(
        self, player: Player, card: Card, game: "Game", deck: "AbstractDeck"
    ) -> bool:
        return card.name == self.name

    def on_gain(
        self, player: Player, card: Card, game: "Game", deck: "AbstractDeck"
    ) -> None:
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


class Sauna(Action):
    """
    +1 Card
    +1 Action

    You may play an Avanto from your hand.
    This turn, when you play a Silver, you may trash a card from your hand.

    """

    class TrashEffect(PlayerCardGameEffect):
        def __init__(self, player: Player, card: Card):
            super().__init__("Sauna: Trash")
            self.player = player
            self.card = card

        def get_action(self) -> EffectAction:
            return EffectAction.Other

        def is_triggered(self, player: Player, card: Card, game: "Game") -> bool:
            return (
                player is self.player and card.name == "Silver" and len(player.hand) > 0
            )

        def handler(self, player: Player, card: Card, game: "Game") -> None:
            trash_cards = player.decider.trash_decision(
                "Enter card to trash (if desired): ",
                self.card,
                player.hand.cards,
                player,
                game,
                min_num_trash=0,
                max_num_trash=1,
            )
            assert 0 <= len(trash_cards) <= 1

            if len(trash_cards) > 0:
                trash_card = trash_cards[0]
                player.trash(trash_card, game)

            game.effect_registry.unregister_play_effect(self.get_id())

    def __init__(self):
        super().__init__(
            name="Sauna", cost=4, type=(CardType.Action,), actions=1, draw=1
        )

    def play(self, player: Player, game: "Game", generic_play: bool = True) -> None:
        super().play(player, game, generic_play)

        avanto_cards = [c for c in player.hand if c.name == "Avanto"]
        if len(avanto_cards) > 0:
            play_avanto = player.decider.binary_decision(
                "Do you want to play an Avanto? (y/n): ",
                self,
                player,
                game,
            )

            if play_avanto:
                avanto_card = avanto_cards[0]
                player.hand.remove(avanto_card)
                player.playmat.add(avanto_card)
                player.exact_play(avanto_card, game, generic_play=False)

        trash_effect = Sauna.TrashEffect(player, self)
        game.effect_registry.register_play_effect(trash_effect)

        unregister_effect = FuncPlayerGameEffect(
            f"{self.name}: Unregister trash",
            EffectAction.Last,
            lambda p, g: g.effect_registry.unregister_play_effect(
                trash_effect.get_id()
            ),
            lambda p, g: p is player,
        )
        game.effect_registry.register_turn_end_effect(unregister_effect)

    def get_pile_starting_count(self, game: "Game") -> int:
        return 5


class Avanto(Action):
    """
    +3 Cards

    You may play a Sauna from your hand.

    """

    def __init__(self):
        super().__init__(name="Avanto", cost=5, type=(CardType.Action,), draw=3)

    def play(self, player: Player, game: "Game", generic_play: bool = True) -> None:
        super().play(player, game, generic_play)

        sauna_cards = [c for c in player.hand if c.name == "Sauna"]
        if len(sauna_cards) > 0:
            play_sauna = player.decider.binary_decision(
                "Do you want to play a Sauna? (y/n): ",
                self,
                player,
                game,
            )

            if play_sauna:
                sauna_card = sauna_cards[0]
                player.hand.remove(sauna_card)
                player.playmat.add(sauna_card)
                player.exact_play(sauna_card, game, generic_play=False)

    def get_pile_starting_count(self, game: "Game") -> int:
        return 5


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


class WalledVillage(Action):
    """
    +1 Card, +2 Actions

    At the start of Clean-up, if you have this and no more than one other
    Action card in play, you may put this onto your deck.

    """

    def __init__(self):
        super().__init__(
            name="Walled Village", cost=4, type=(CardType.Action,), actions=2, draw=1
        )

    def play(self, player: Player, game: "Game", generic_play: bool = True) -> None:
        self._play(player, game, 1, generic_play)

    def multi_play(
        self,
        player: Player,
        game: "Game",
        multi_play_card: Card,
        state: Any,
        generic_play: bool = True,
    ) -> Any:
        if state is None:
            count = 1
        else:
            count = int(state) + 1

        self._play(player, game, count, generic_play)

        return count

    def _play(
        self, player: Player, game: "Game", count: int, generic_play: bool = True
    ) -> None:
        super().play(player, game, generic_play)

        if count == 1:
            cleanup_effect = FuncPlayerGameEffect(
                "Walled Village: Topdeck",
                EffectAction.Other,
                self.on_cleanup,
                self.on_cleanup_trigger,
            )
            game.effect_registry.register_cleanup_phase_start_effect(cleanup_effect)

            cleanup_effect_id = cleanup_effect.get_id()
            unregister_effect = FuncPlayerGameEffect(
                f"{self.name}: Unregister Topdeck Effect",
                EffectAction.Last,
                lambda p, g: g.effect_registry.unregister_cleanup_phase_start_effect(
                    cleanup_effect_id
                ),
                lambda p, g: p is player,
            )
            game.effect_registry.register_turn_end_effect(unregister_effect)

    def on_cleanup_trigger(self, player: Player, game: "Game") -> bool:
        num_action_cards = sum(
            1 for c in player.playmat.cards if CardType.Action in c.type
        )
        return num_action_cards <= 2

    def on_cleanup(self, player: Player, game: "Game") -> None:
        topdeck = player.decider.binary_decision(
            prompt=f"Topdeck {self.name}? y/n: ",
            card=self,
            player=player,
            game=game,
        )
        if topdeck:
            player.playmat.remove(self)
            player.deck.add(self)
            logger.info(f"{player} topdecks {self.name}")


envoy = Envoy()
marchland = Marchland()
sauna = Sauna()
avanto = Avanto()
stash = Stash()
walled_village = WalledVillage()


promos_set = Expansion(
    "Promos",
    [
        envoy,
        marchland,
        [sauna, avanto],
        stash,
        walled_village,
    ],
)
