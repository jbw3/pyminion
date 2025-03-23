from pyminion.expansions.base import copper, silver, estate
from pyminion.expansions.promos import dismantle
from pyminion.game import Game
from pyminion.human import Human


def test_dismantle_zero_cost(human: Human, game: Game, monkeypatch):
    human.hand.add(copper)
    human.hand.add(copper)
    human.hand.add(dismantle)
    assert len(human.hand) == 3

    responses = ["copper"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(dismantle, game)
    assert len(responses) == 0
    assert human.state.actions == 0
    assert len(human.hand) == 1
    assert len(human.discard_pile) == 0
    assert len(game.trash) == 1
    assert game.trash.cards[0].name == "Copper"


def test_dismantle_nonzero_cost(human: Human, game: Game, monkeypatch):
    human.hand.add(copper)
    human.hand.add(silver)
    human.hand.add(dismantle)
    assert len(human.hand) == 3

    responses = ["silver", "estate"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(dismantle, game)
    assert len(responses) == 0
    assert human.state.actions == 0
    assert len(human.hand) == 1
    assert len(human.discard_pile) == 2
    assert set(c.name for c in human.discard_pile) == {"Gold", "Estate"}
    assert len(game.trash) == 1
    assert game.trash.cards[0].name == "Silver"


def test_dismantle_empty_hand(human: Human, game: Game, monkeypatch):
    human.hand.add(dismantle)
    assert len(human.hand) == 1

    human.play(dismantle, game)
    assert human.state.actions == 0
    assert len(human.hand) == 0
    assert len(human.discard_pile) == 0
    assert len(game.trash) == 0


def test_dismantle_one_gain_option(human: Human, game: Game, monkeypatch):
    # clear curse pile so copper will be the only valid option
    game.supply.get_pile("Curse").cards.clear()

    human.hand.add(estate)
    human.hand.add(dismantle)
    assert len(human.hand) == 2

    responses = []
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(dismantle, game)
    assert len(responses) == 0
    assert human.state.actions == 0
    assert len(human.hand) == 0
    assert len(human.discard_pile) == 2
    assert set(c.name for c in human.discard_pile) == {"Gold", "Copper"}
    assert len(game.trash) == 1
    assert game.trash.cards[0].name == "Estate"
