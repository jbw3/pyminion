from pyminion.expansions.base import smithy
from pyminion.expansions.promos import summon
from pyminion.game import Game
import pytest


@pytest.mark.kingdom_cards([smithy])
def test_summon(multiplayer_game: Game, monkeypatch):
    player = multiplayer_game.players[0]

    responses = ["smithy"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    player.state.money = 5
    player.buy(summon, multiplayer_game)
