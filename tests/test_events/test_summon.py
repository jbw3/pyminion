from pyminion.expansions.base import (
    base_set,
    artisan,
    bandit,
    council_room,
    gardens,
    festival,
    market,
    smithy,
    witch,
)
from pyminion.expansions.promos import promos_set, governor, marchland, stash, summon
from pyminion.game import Game
import pytest


@pytest.mark.kingdom_cards([smithy])
def test_summon(multiplayer_game: Game, monkeypatch):
    responses = ["smithy"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    player = multiplayer_game.players[0]
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 0

    player.state.money = 5
    player.buy(summon, multiplayer_game)
    assert len(responses) == 0
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 1
    assert player.set_aside.cards[0].name == "Smithy"

    player.end_turn(multiplayer_game)
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 1
    assert len(player.hand) == 5

    player.start_turn(multiplayer_game)
    assert len(player.playmat) == 1
    assert player.playmat.cards[0].name == "Smithy"
    assert len(player.set_aside) == 0
    assert len(player.hand) == 8


# make smithy the only valid option
@pytest.mark.expansions([base_set, promos_set])
@pytest.mark.kingdom_cards(
    [
        artisan,
        bandit,
        gardens,
        festival,
        market,
        council_room,
        witch,
        governor,
        marchland,
        stash,
    ]
)
def test_summon_one_option(multiplayer_game: Game):
    player = multiplayer_game.players[0]
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 0

    player.state.money = 5
    player.buy(summon, multiplayer_game)
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 0

    player.end_turn(multiplayer_game)
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 0
    assert len(player.hand) == 5

    player.start_turn(multiplayer_game)
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 0
    assert len(player.hand) == 5


# have no valid options
@pytest.mark.expansions([base_set, promos_set])
@pytest.mark.kingdom_cards(
    [
        artisan,
        bandit,
        gardens,
        festival,
        market,
        smithy,
        witch,
        governor,
        marchland,
        stash,
    ]
)
def test_summon_no_options(multiplayer_game: Game):
    player = multiplayer_game.players[0]
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 0

    player.state.money = 5
    player.buy(summon, multiplayer_game)
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 1
    assert player.set_aside.cards[0].name == "Smithy"

    player.end_turn(multiplayer_game)
    assert len(player.playmat) == 0
    assert len(player.set_aside) == 1
    assert len(player.hand) == 5

    player.start_turn(multiplayer_game)
    assert len(player.playmat) == 1
    assert player.playmat.cards[0].name == "Smithy"
    assert len(player.set_aside) == 0
    assert len(player.hand) == 8
