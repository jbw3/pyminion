from pyminion.expansions.base import silver, gold, duchy
from pyminion.expansions.promos import church
from pyminion.game import Game
from pyminion.human import Human


def test_church_set_aside_and_trash(human: Human, game: Game, monkeypatch):
    human.hand.add(silver)
    human.hand.add(gold)
    human.hand.add(duchy)
    human.hand.add(church)
    assert len(human.hand) == 4

    responses = ["silver,gold,duchy", "silver"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(church, game)
    assert len(responses) == 1
    assert human.state.actions == 1
    assert len(human.hand) == 0
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 3
    assert set(c.name for c in human.set_aside) == {"Silver", "Gold", "Duchy"}
    assert len(human.discard_pile) == 0

    human.start_cleanup_phase(game)
    assert len(human.hand) == 5
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 3
    assert set(c.name for c in human.set_aside) == {"Silver", "Gold", "Duchy"}
    assert len(human.discard_pile) == 0

    human.start_turn(game)
    assert len(human.hand) == 7
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 0
    assert len(human.discard_pile) == 0
    assert len(game.trash) == 1
    assert game.trash.cards[0].name == "Silver"


def test_church_set_aside_no_trash(human: Human, game: Game, monkeypatch):
    human.hand.add(silver)
    human.hand.add(gold)
    human.hand.add(duchy)
    human.hand.add(church)
    assert len(human.hand) == 4

    responses = ["silver,gold,duchy", ""]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(church, game)
    assert len(responses) == 1
    assert human.state.actions == 1
    assert len(human.hand) == 0
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 3
    assert set(c.name for c in human.set_aside) == {"Silver", "Gold", "Duchy"}
    assert len(human.discard_pile) == 0

    human.start_cleanup_phase(game)
    assert len(human.hand) == 5
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 3
    assert set(c.name for c in human.set_aside) == {"Silver", "Gold", "Duchy"}
    assert len(human.discard_pile) == 0

    human.start_turn(game)
    assert len(human.hand) == 8
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 0
    assert len(human.discard_pile) == 0
    assert len(game.trash) == 0


def test_church_set_aside_one_no_trash(human: Human, game: Game, monkeypatch):
    human.hand.add(silver)
    human.hand.add(gold)
    human.hand.add(duchy)
    human.hand.add(church)
    assert len(human.hand) == 4

    responses = ["silver", ""]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(church, game)
    assert len(responses) == 1
    assert human.state.actions == 1
    assert len(human.hand) == 2
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 1
    assert set(c.name for c in human.set_aside) == {"Silver"}
    assert len(human.discard_pile) == 0

    human.start_cleanup_phase(game)
    assert len(human.hand) == 5
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 1
    assert set(c.name for c in human.set_aside) == {"Silver"}
    assert len(human.discard_pile) == 2

    human.start_turn(game)
    assert len(human.hand) == 6
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 0
    assert len(human.discard_pile) == 2
    assert len(game.trash) == 0


def test_church_no_set_aside_no_trash(human: Human, game: Game, monkeypatch):
    human.hand.add(silver)
    human.hand.add(gold)
    human.hand.add(duchy)
    human.hand.add(church)
    assert len(human.hand) == 4

    responses = ["", ""]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(church, game)
    assert len(responses) == 1
    assert human.state.actions == 1
    assert len(human.hand) == 3
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 0
    assert len(human.discard_pile) == 0

    human.start_cleanup_phase(game)
    assert len(human.hand) == 5
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 0
    assert len(human.discard_pile) == 3

    human.start_turn(game)
    assert len(human.hand) == 5
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Church"
    assert len(human.set_aside) == 0
    assert len(human.discard_pile) == 3
    assert len(game.trash) == 0
