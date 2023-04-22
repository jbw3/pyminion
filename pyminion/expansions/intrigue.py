from enum import IntEnum, unique
import logging
from typing import TYPE_CHECKING, List

from pyminion.core import AbstractDeck, Action, Card, CardType, Treasure, Victory
from pyminion.player import Player
from pyminion.exceptions import EmptyPile
from pyminion.expansions.base import curse, duchy, estate, gold, silver

if TYPE_CHECKING:
    from pyminion.game import Game


logger = logging.getLogger()


class Baron(Action):
    """
    +1 Buy

    You may discard an Estate for +4 money. If you don't, gain an Estate.

    """

    @unique
    class Choice(IntEnum):
        DiscardEstate = 0
        GainEstate = 1

    def __init__(self):
        super().__init__(name="Baron", cost=4, type=(CardType.Action,))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")
        if generic_play:
            super().generic_play(player)

        player.state.buys += 1

        discard_estate = False
        if estate in player.hand.cards:
            options = [
                "Discard estate for +4 money",
                "Gain an estate",
            ]
            responses = player.decider.multiple_option_decision(self, options, player, game)
            assert len(responses) == 1
            response = responses[0]

            discard_estate = (response == Baron.Choice.DiscardEstate)

        if discard_estate:
            player.discard(estate)
            player.state.money += 4
        elif game.supply.pile_length(estate.name) > 0:
            player.gain(estate, game.supply)


class Conspirator(Action):
    """
    +2 Money

    If you've played 3 or more Actions this turn (counting this), +1 Card and +1 Action.

    """

    def __init__(self):
        super().__init__(name="Conspirator", cost=4, type=(CardType.Action,), money=2)

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")
        if generic_play:
            super().generic_play(player)

        player.state.money += 2

        if player.actions_played_this_turn >= 3:
            player.draw(1)
            player.state.actions += 1


class Courtier(Action):
    """
    Reveal a card from your hand. For each type it has (Action, Attack, etc.),
    choose one: +1 Action; or +1 Buy; or +3 Money; or gain a Gold. The choices
    must be different.

    """

    @unique
    class Choice(IntEnum):
        Action = 0
        Buy = 1
        Money = 2
        GainGold = 3

    def __init__(self):
        super().__init__(name="Courtier", cost=5, type=(CardType.Action,))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")
        if generic_play:
            super().generic_play(player)

        hand_len = len(player.hand)

        if hand_len == 0:
            return

        if hand_len == 1:
            reveal_card = player.hand.cards[0]
        else:
            reveal_cards = player.decider.reveal_decision(
                prompt="Reveal a card from your hand: ",
                card=self,
                valid_cards=player.hand.cards,
                player=player,
                game=game,
                min_num_reveal = 1,
                max_num_reveal = 1,
            )
            assert len(reveal_cards) == 1
            reveal_card = reveal_cards[0]

        logger.info(f"{player} reveals {reveal_card}")

        num_choices = min(len(reveal_card.type), 4)

        if num_choices == 4:
            choices = [c.value for c in Courtier.Choice]
        else:
            options = [
                "+1 Action",
                "+1 Buy",
                "+3 Money",
                "Gain a Gold",
            ]
            choices = player.decider.multiple_option_decision(
                card=self,
                options=options,
                player=player,
                game=game,
                num_choices=num_choices,
                unique=True,
            )
            assert len(choices) == num_choices

        for choice in choices:
            if choice == Courtier.Choice.Action:
                player.state.actions += 1
            elif choice == Courtier.Choice.Buy:
                player.state.buys += 1
            elif choice == Courtier.Choice.Money:
                player.state.money += 3
            elif choice == Courtier.Choice.GainGold:
                player.gain(gold, game.supply)
            else:
                raise ValueError(f"Unknown courtier choice '{choice}'")


class Courtyard(Action):
    """
    +3 Cards

    Put a card from your hand onto your deck.

    """

    def __init__(self):
        super().__init__(name="Courtyard", cost=2, type=(CardType.Action,))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")
        if generic_play:
            super().generic_play(player)

        player.draw(3)

        topdeck_cards = player.decider.topdeck_decision(
            prompt="Enter the card you would like to topdeck: ",
            card=self,
            valid_cards=player.hand.cards,
            player=player,
            game=game,
            min_num_topdeck=1,
            max_num_topdeck=1,
        )
        assert len(topdeck_cards) == 1
        topdeck_card = topdeck_cards[0]

        player.hand.remove(topdeck_card)
        player.deck.add(topdeck_card)


class Duke(Victory):
    """
    Worth 1VP per Duchy you have.

    """

    def __init__(self):
        super().__init__("Duke", 5, (CardType.Victory,))

    def score(self, player: Player) -> int:
        vp = 0
        for card in player.get_all_cards():
            if card.name == duchy.name:
                vp += 1
        return vp


class Harem(Treasure, Victory):
    def __init__(self):
        Treasure.__init__(
            self,
            name="Harem",
            cost=6,
            type=(CardType.Treasure, CardType.Victory),
            money=2,
        )

    def play(self, player: Player, game: "Game") -> None:
        player.playmat.add(self)
        player.hand.remove(self)
        player.state.money += self.money

    def score(self, player: Player) -> int:
        vp = 2
        return vp


class Ironworks(Action):
    """
    Gain a card costing up to $4.
    If the gained card is an...

    Action card, +1 Action
    Treasure card, +$1
    Victory card, +1 Card

    """

    def __init__(self):
        super().__init__(name="Ironworks", cost=4, type=(CardType.Action,))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")
        if generic_play:
            super().generic_play(player)

        gain_cards = player.decider.gain_decision(
            prompt="Gain a card costing up to 4 money: ",
            card=self,
            valid_cards=[
                card for card in game.supply.avaliable_cards() if card.cost <= 4
            ],
            player=player,
            game=game,
            min_num_gain=1,
            max_num_gain=1,
        )
        assert len(gain_cards) == 1
        gain_card = gain_cards[0]
        assert gain_card.cost <= 4

        player.gain(card=gain_card, supply=game.supply)

        if CardType.Action in gain_card.type:
            player.state.actions += 1

        if CardType.Treasure in gain_card.type:
            player.state.money += 1

        if CardType.Victory in gain_card.type:
            player.draw(1)


class Lurker(Action):
    """
    +1 Action

    Choose one: Trash an Action card from the Supply, or gain an Action card from the trash.

    """

    @unique
    class Choice(IntEnum):
        TrashAction = 0
        GainAction = 1

    def __init__(self):
        super().__init__(name="Lurker", cost=2, type=(CardType.Action,), actions=1)

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")
        if generic_play:
            super().generic_play(player)

        player.state.actions += 1

        supply_action_cards = [
            c for c in game.supply.avaliable_cards() if CardType.Action in c.type
        ]
        trash_action_cards = [
            c for c in game.trash.cards if CardType.Action in c.type
        ]

        if len(supply_action_cards) > 0 or len(trash_action_cards) > 0:
            if len(supply_action_cards) == 0:
                choice = Lurker.Choice.GainAction
            elif len(trash_action_cards) == 0:
                choice = Lurker.Choice.TrashAction
            else:
                options = [
                    "Trash an Action card from the Supply",
                    "Gain an Action card from the trash",
                ]
                choices = player.decider.multiple_option_decision(
                    card=self,
                    options=options,
                    player=player,
                    game=game,
                )
                assert len(choices) == 1
                choice = choices[0]

            if choice == Lurker.Choice.TrashAction:
                trash_cards = player.decider.trash_decision(
                    prompt="Choose a card from the Supply to trash",
                    card=self,
                    valid_cards=supply_action_cards,
                    player=player,
                    game=game,
                    min_num_trash=1,
                    max_num_trash=1,
                )
                assert len(trash_cards) == 1
                trash_card = trash_cards[0]

                game.supply.trash_card(trash_card, game.trash)

            elif choice == Lurker.Choice.GainAction:
                gain_cards = player.decider.gain_decision(
                    prompt="Choose a card to gain from the trash",
                    card=self,
                    valid_cards=trash_action_cards,
                    player=player,
                    game=game,
                    min_num_gain=1,
                    max_num_gain=1,
                )
                assert len(gain_cards) == 1
                gain_card = gain_cards[0]

                game.trash.remove(gain_card)
                player.discard_pile.add(gain_card)

            else:
                raise ValueError(f"Unknown lurker choice '{choice}'")


class Masquerade(Action):
    """
    +2 Cards

    Each player with any cards in hand passes one to the next such player to
    their left, at once. Then you may trash a card from your hand.

    """

    def __init__(self):
        super().__init__(name="Masquerade", cost=3, type=(CardType.Action,), draw=2)

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        player.draw(2)

        # get players who have at least 1 card in their hand
        valid_players = [p for p in game.players if len(p.hand) > 0]

        # prompt each player to choose a card to pass
        passed_cards: List[Card] = []
        for p in valid_players:
            pass_cards = player.decider.pass_decision(
                prompt="Pick a card to pass to the player on your left: ",
                card=self,
                valid_cards=p.hand.cards,
                player=player,
                game=game,
                min_num_pass=1,
                max_num_pass=1,
            )
            assert len(pass_cards) == 1
            pass_card = pass_cards[0]

            passed_cards.append(pass_card)

        # pass the cards
        for idx, p in enumerate(valid_players):
            c = passed_cards[idx]
            p.hand.remove(c)
            next_idx = (idx + 1) % len(valid_players)
            next_player = valid_players[next_idx]
            next_player.hand.add(c)
            logger.info(f"{p} passes {c} to {next_player}")

        trash = player.decider.binary_decision(
            prompt="Would you like to trash a card from your hand?",
            card=self,
            player=player,
            game=game,
        )

        if trash:
            trash_cards = player.decider.trash_decision(
                prompt="Choose a card from your hand to trash",
                card=self,
                valid_cards=player.hand.cards,
                player=player,
                game=game,
                min_num_trash=1,
                max_num_trash=1,
            )
            assert len(trash_cards) == 1
            trash_card = trash_cards[0]

            player.trash(trash_card, game.trash)


class Mill(Action, Victory):
    """
    +1 card, +1 action

    You may discard 2 cards, for +$2.

    """

    def __init__(self):
        Action.__init__(self, "Mill", 4, (CardType.Action, CardType.Victory), actions=1, draw=1)

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        player.draw(1)
        player.state.actions += 1

        discard = player.decider.binary_decision(
            prompt="Do you want to discard 2 cards for +2 money?",
            card=self,
            player=player,
            game=game,
        )

        if discard:
            hand_len = len(player.hand)
            if hand_len <= 2:
                discard_cards = player.hand.cards[:]
            else:
                discard_cards = player.decider.discard_decision(
                    prompt="Enter the cards you would like to discard: ",
                    card=self,
                    valid_cards=player.hand.cards,
                    player=player,
                    game=game,
                    min_num_discard=2,
                    max_num_discard=2,
                )
                assert len(discard_cards) == 2

            if len(discard_cards) == 2:
                player.state.money += 2

            for c in discard_cards:
                player.discard(c)

    def score(self, player: Player) -> int:
        vp = 1
        return vp


class Minion(Action):
    """
    +1 action

    Choose one: +$2; or discard your hand, +4 Cards, and each other player
    with at least 5 cards in hand discards their hand and draws 4 cards.

    """

    @unique
    class Choice(IntEnum):
        Money = 0
        DiscardDrawAttack = 1

    def __init__(self):
        super().__init__(name="Minion", cost=5, type=(CardType.Action, CardType.Attack), actions=1)

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        player.state.actions += 1

        # opponents react to the card before the choice is made
        is_attacked: List[bool] = []
        for opponent in game.players:
            if opponent is not player:
                ret = opponent.is_attacked(player, self, game)
                is_attacked.append(ret)

        options = [
            "+2 Money",
            "Discard your hand, draw 4 cards, and each other player with at least 5 cards discards their hand and draws 4 cards",
        ]
        choices = player.decider.multiple_option_decision(
            card=self,
            options=options,
            player=player,
            game=game,
        )
        assert len(choices) == 1
        choice = choices[0]

        if choice == Minion.Choice.Money:
            player.state.money += 2
        elif choice == Minion.Choice.DiscardDrawAttack:
            for _ in range(len(player.hand.cards)):
                player.discard(player.hand.cards[0])
            player.draw(4)

            i = 0
            for opponent in game.players:
                if opponent is not player and is_attacked[i]:
                    if len(opponent.hand) >= 5:
                        for _ in range(len(opponent.hand.cards)):
                            opponent.discard(opponent.hand.cards[0])
                        opponent.draw(4)
                    i += 1
        else:
            raise ValueError(f"Unknown minion choice '{choice}'")


class Nobles(Action, Victory):
    """
    Choose one: +3 Cards; or +2 Actions.

    """

    @unique
    class Choice(IntEnum):
        Cards = 0
        Actions = 1

    def __init__(self):
        Action.__init__(self, "Nobles", 6, (CardType.Action, CardType.Victory))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        options = [
            "+3 Cards",
            "+2 Actions",
        ]
        choices = player.decider.multiple_option_decision(
            card=self,
            options=options,
            player=player,
            game=game,
        )
        assert len(choices) == 1
        choice = choices[0]

        if choice == Nobles.Choice.Cards:
            player.draw(3)
        elif choice == Nobles.Choice.Actions:
            player.state.actions += 2
        else:
            raise ValueError(f"Unknown nobles choice '{choice}'")

    def score(self, player: Player) -> int:
        vp = 2
        return vp


class Pawn(Action):
    """
    Choose two: +1 Card; +1 Action; +1 Buy; +1 Money.
    The choices must be different.

    """

    @unique
    class Choice(IntEnum):
        Card = 0
        Action = 1
        Buy = 2
        Money = 3

    def __init__(self):
        super().__init__(name="Pawn", cost=2, type=(CardType.Action,))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        options = [
            "+1 Card",
            "+1 Action",
            "+1 Buy",
            "+1 Money",
        ]
        choices = player.decider.multiple_option_decision(
            card=self,
            options=options,
            player=player,
            game=game,
            num_choices=2,
            unique=True,
        )
        assert len(choices) == 2

        for choice in choices:
            if choice == Pawn.Choice.Card:
                player.draw(1)
            elif choice == Pawn.Choice.Action:
                player.state.actions += 1
            elif choice == Pawn.Choice.Buy:
                player.state.buys += 1
            elif choice == Pawn.Choice.Money:
                player.state.money += 1
            else:
                raise ValueError(f"Unknown pawn choice '{choice}'")


class ShantyTown(Action):
    """
    +2 Actions

    Reveal your hand.
    If you have no Action cards in hand, +2 Cards.

    """

    def __init__(self):
        super().__init__(name="Shanty Town", cost=3, type=(CardType.Action,), actions=2)

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        player.state.actions += 2

        if not any(CardType.Action in c.type for c in player.hand.cards):
            player.draw(2)


class Steward(Action):
    """
    Choose one: +2 Cards; or +2 money; or trash 2 cards from your hand.

    """

    @unique
    class Choice(IntEnum):
        Cards = 0
        Money = 1
        Trash = 2

    def __init__(self):
        super().__init__(name="Steward", cost=3, type=(CardType.Action,))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        options = [
            "+2 Cards",
            "+2 Money",
            "Trash 2 cards from your hand",
        ]
        choices = player.decider.multiple_option_decision(
            card=self,
            options=options,
            player=player,
            game=game,
        )
        assert len(choices) == 1
        choice = choices[0]

        if choice == Steward.Choice.Cards:
            player.draw(2)
        elif choice == Steward.Choice.Money:
            player.state.money += 2
        elif choice == Steward.Choice.Trash:
            trash_cards = self._get_trash_cards(player, game)
            for card in trash_cards:
                player.trash(card, game.trash)
        else:
            raise ValueError(f"Unknown steward choice '{choice}'")

    def _get_trash_cards(self, player: Player, game: "Game") -> List[Card]:

        if len(player.hand) <= 2:
            return player.hand.cards[:]

        trash_cards = player.decider.trash_decision(
            prompt="Enter 2 cards you would like to trash from your hand: ",
            card=self,
            valid_cards=player.hand.cards,
            player=player,
            game=game,
            min_num_trash=2,
            max_num_trash=2,
        )
        assert len(trash_cards) == 2

        return trash_cards


class Swindler(Action):
    """
    +2 Money

    Each other player trashes the top card of their deck and gains a card with
    the same cost that you choose.

    """

    def __init__(self):
        super().__init__(name="Swindler", cost=3, type=(CardType.Action, CardType.Attack))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        player.state.money += 2

        for opponent in game.players:
            if opponent is not player and opponent.is_attacked(player, self, game):
                revealed_cards = AbstractDeck()
                opponent.draw(num_cards=1, destination=revealed_cards, silent=True)
                trashed_card = revealed_cards.cards[0]
                game.trash.add(trashed_card)
                trashed_cost = trashed_card.cost

                logger.info(f"{opponent} trashes {trashed_card}")

                valid_cards = [
                    c
                    for c in game.supply.avaliable_cards()
                    if c.cost == trashed_cost
                ]
                if len(valid_cards) == 0:
                    continue

                gain_cards = player.decider.gain_decision(
                    prompt=f"Pick a cost {trashed_cost} card for {opponent} to gain: ",
                    card=self,
                    valid_cards=valid_cards,
                    player=player,
                    game=game,
                    min_num_gain=1,
                    max_num_gain=1,
                )
                assert len(gain_cards) == 1
                gain_card = gain_cards[0]
                opponent.discard_pile.add(gain_card)

                logger.info(f"{opponent} gains {gain_card}")


class Torturer(Action):
    """
    +3 cards

    Each other player either discards 2 cards or gains a Curse to their
    hand, their choice. (They may pick an option they can't do.)

    """

    @unique
    class Choice(IntEnum):
        Discard = 0
        GainCurse = 1

    def __init__(self):
        super().__init__(name="Torturer", cost=5, type=(CardType.Action, CardType.Attack))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        player.draw(3)

        for opponent in game.players:
            if opponent is not player and opponent.is_attacked(player, self, game):
                options = [
                    "Discard 2 cards",
                    "Gain a Curse to your hand",
                ]
                choices = opponent.decider.multiple_option_decision(
                    card=self,
                    options=options,
                    player=opponent,
                    game=game,
                )
                assert len(choices) == 1
                choice = choices[0]

                if choice == Torturer.Choice.Discard:
                    self._discard(opponent, game)
                elif choice == Torturer.Choice.GainCurse:
                    self._gain_curse(opponent, game)
                else:
                    raise ValueError(f"Unknown torturer choice '{choice}'")

    def _discard(self, opponent: Player, game: "Game") -> None:
        num_discard = min(2, len(opponent.hand))
        if num_discard == 0:
            return

        discard_cards = opponent.decider.discard_decision(
            prompt=f"You must discard {num_discard} card(s) from your hand: ",
            card=self,
            valid_cards=opponent.hand.cards,
            player=opponent,
            game=game,
            min_num_discard=num_discard,
            max_num_discard=num_discard,
        )
        assert len(discard_cards) == num_discard

        for card in discard_cards:
            opponent.discard(target_card=card)

    def _gain_curse(self, opponent: Player, game: "Game") -> None:
        try:
            opponent.gain(
                card=curse,
                supply=game.supply,
                destination=opponent.hand,
            )
        except EmptyPile:
            pass


class TradingPost(Action):
    """
    Trash 2 cards from your hand. If you did, gain a Silver to your hand.

    """

    def __init__(self):
        super().__init__(name="Trading Post", cost=5, type=(CardType.Action,))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        len_hand = len(player.hand)
        if len_hand == 0:
            pass
        elif len_hand == 1:
            player.trash(player.hand.cards[0], game.trash)
        else:
            if len_hand == 2:
                trash_cards = player.hand.cards[:]
            else:
                trash_cards = player.decider.trash_decision(
                    prompt="Trash 2 cards from your hand: ",
                    card=self,
                    valid_cards=player.hand.cards,
                    player=player,
                    game=game,
                    min_num_trash=2,
                    max_num_trash=2,
                )
                assert len(trash_cards) == 2

            for card in trash_cards:
                player.trash(card, game.trash)

            # attempt to gain a silver to player's hand.
            # if silver pile is empty, proceed
            try:
                player.gain(silver, game.supply, player.hand)
            except EmptyPile:
                pass


class Upgrade(Action):
    """
    +1 card, +1 action
    Trash a card from your hand. Gain a card costing exactly $1 more than it.

    """

    def __init__(self):
        super().__init__(name="Upgrade", cost=5, type=(CardType.Action,))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        player.draw(1)
        player.state.actions += 1

        trash_cards = player.decider.trash_decision(
            prompt="Trash a card form your hand: ",
            card=self,
            valid_cards=player.hand.cards,
            player=player,
            game=game,
            min_num_trash=1,
            max_num_trash=1,
        )
        assert len(trash_cards) == 1
        trash_card = trash_cards[0]

        player.trash(trash_card, trash=game.trash)

        new_cost = trash_card.cost + 1
        valid_cards = [
            card
            for card in game.supply.avaliable_cards()
            if card.cost == new_cost
        ]

        if len(valid_cards) == 0:
            return

        gain_cards = player.decider.gain_decision(
            prompt=f"Gain a card costing {new_cost} money: ",
            card=self,
            valid_cards=valid_cards,
            player=player,
            game=game,
            min_num_gain=1,
            max_num_gain=1,
        )
        assert len(gain_cards) == 1
        gain_card = gain_cards[0]
        assert gain_card.cost == new_cost

        player.gain(gain_card, game.supply)


class WishingWell(Action):
    """
    +1 card, +1 action

    Name a card, then reveal the top card of your deck. If you named it,
    put it into your hand.

    """

    def __init__(self):
        super().__init__(name="Wishing Well", cost=3, type=(CardType.Action,))

    def play(
        self, player: Player, game: "Game", generic_play: bool = True
    ) -> None:

        logger.info(f"{player} plays {self}")

        if generic_play:
            super().generic_play(player)

        player.draw(1)
        player.state.actions += 1

        named_cards = player.decider.name_card_decision(
            prompt="Name a card: ",
            card=self,
            valid_cards=game.all_game_cards,
            player=player,
            game=game,
            min_num_name=1,
            max_num_name=1,
        )
        assert len(named_cards) == 1
        name = named_cards[0].name

        logger.info(f"{player} names {name}")

        revealed = AbstractDeck()
        player.draw(1, revealed, silent=True)
        revealed_card = revealed.cards[0]
        revealed_name = revealed_card.name

        msg = f"{player} reveals {revealed_name} and "
        if revealed_name == name:
            player.hand.add(revealed_card)
            msg += "puts it into their hand"
        else:
            player.deck.add(revealed_card)
            msg += "topdecks it"

        logger.info(msg)


baron = Baron()
conspirator = Conspirator()
courtier = Courtier()
courtyard = Courtyard()
duke = Duke()
harem = Harem()
ironworks = Ironworks()
lurker = Lurker()
masquerade = Masquerade()
mill = Mill()
minion = Minion()
nobles = Nobles()
pawn = Pawn()
shanty_town = ShantyTown()
steward = Steward()
swindler = Swindler()
torturer = Torturer()
trading_post = TradingPost()
upgrade = Upgrade()
wishing_well = WishingWell()


intrigue_set: List[Card] = [
    baron,
    conspirator,
    courtier,
    courtyard,
    duke,
    harem,
    ironworks,
    lurker,
    masquerade,
    mill,
    minion,
    nobles,
    pawn,
    shanty_town,
    steward,
    swindler,
    torturer,
    trading_post,
    upgrade,
    wishing_well,
]
