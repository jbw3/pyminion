from pyminion.expansions.base import copper, silver
from pyminion.expansions.promos import sauna, avanto
from pyminion.game import Game
from pyminion.human import Human
from pyminion.player import Player


def test_sauna(player: Player, game: Game):
    player.hand.add(sauna)
    assert len(player.hand) == 1

    player.play(sauna, game)
    assert len(player.hand) == 1
    assert player.state.actions == 1


def test_sauna_trash(human: Human, game: Game, monkeypatch):
    responses = ["copper"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.hand.add(sauna)
    human.hand.add(silver)
    human.deck.add(copper)
    assert len(human.hand) == 2

    human.play(sauna, game)
    assert len(human.hand) == 2

    human.play(silver, game)
    assert len(responses) == 0
    assert len(human.hand) == 0
    assert len(game.trash) == 1
    assert game.trash.cards[0].name == "Copper"


def test_sauna_no_trash(human: Human, game: Game, monkeypatch):
    responses = [""]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.hand.add(sauna)
    human.hand.add(silver)
    human.deck.add(copper)
    assert len(human.hand) == 2

    human.play(sauna, game)
    assert len(human.hand) == 2

    human.play(silver, game)
    assert len(responses) == 0
    assert len(human.hand) == 1
    assert human.hand.cards[0].name == "Copper"
    assert len(game.trash) == 0


def test_avanto(player: Player, game: Game):
    player.hand.add(avanto)
    assert len(player.hand) == 1

    player.play(avanto, game)
    assert len(player.hand) == 3
    assert player.state.actions == 0


def test_sauna_avanto_chain(human: Human, game: Game, monkeypatch):
    responses = ["y", "y"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.hand.add(sauna)
    human.hand.add(sauna)
    human.hand.add(avanto)
    assert len(human.hand) == 3

    human.play(sauna, game)
    assert len(responses) == 0
    assert len(human.hand) == 5
    assert human.state.actions == 2
    assert len(human.playmat) == 3
    assert sum(1 for c in human.playmat if c.name == "Sauna") == 2
    assert sum(1 for c in human.playmat if c.name == "Avanto") == 1
