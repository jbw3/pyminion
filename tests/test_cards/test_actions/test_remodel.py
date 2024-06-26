from pyminion.expansions.base import copper, remodel
from pyminion.game import Game
from pyminion.human import Human


def test_remodel_gain_valid(human: Human, game: Game, monkeypatch):
    human.hand.add(copper)
    human.hand.add(copper)
    human.hand.add(remodel)
    assert len(human.discard_pile) == 0
    assert len(game.trash) == 0

    responses = iter(["copper", "estate"])
    monkeypatch.setattr("builtins.input", lambda input: next(responses))

    human.play(remodel, game)
    assert len(human.playmat) == 1
    assert len(human.discard_pile) == 1
    assert human.state.actions == 0
    assert human.discard_pile.cards[0].name == "Estate"
    assert game.trash.cards[0].name == "Copper"


def test_remodel_1_card_hand(human: Human, game: Game, monkeypatch):
    human.hand.add(copper)
    human.hand.add(remodel)
    assert len(human.discard_pile) == 0
    assert len(game.trash) == 0

    responses = iter(["estate"])
    monkeypatch.setattr("builtins.input", lambda input: next(responses))

    human.play(remodel, game)
    assert len(human.playmat) == 1
    assert len(human.discard_pile) == 1
    assert human.state.actions == 0
    assert human.discard_pile.cards[0].name == "Estate"
    assert game.trash.cards[0].name == "Copper"


def test_remodel_empty_hand(human: Human, game: Game):
    human.hand.add(remodel)
    assert len(human.hand) == 1
    assert len(human.discard_pile) == 0
    assert len(game.trash) == 0

    human.play(remodel, game)
    assert len(human.playmat) == 1
    assert len(human.discard_pile) == 0
    assert len(game.trash) == 0
    assert human.state.actions == 0
