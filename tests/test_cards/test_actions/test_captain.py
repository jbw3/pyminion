from pyminion.expansions.base import base_set, gardens, smithy, village
from pyminion.expansions.intrigue import intrigue_set, duke, farm
from pyminion.expansions.seaside import seaside_set, astrolabe
from pyminion.expansions.alchemy import alchemy_set, philosophers_stone, vineyard
from pyminion.expansions.promos import promos_set, captain, marchland, stash
from pyminion.game import Game
from pyminion.human import Human
import pytest


@pytest.mark.expansions([base_set, promos_set])
@pytest.mark.kingdom_cards([captain, smithy, village])
def test_captain(human: Human, game: Game, monkeypatch):
    responses = ["smithy", "village"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.hand.add(captain)
    assert len(human.hand) == 1

    human.play(captain, game)
    assert len(responses) == 1
    assert human.state.actions == 0
    assert len(human.hand) == 3

    human.start_cleanup_phase(game)

    human.start_turn(game)
    assert len(responses) == 0
    assert human.state.actions == 3
    assert len(human.hand) == 6


@pytest.mark.expansions([base_set, intrigue_set, seaside_set, alchemy_set, promos_set])
@pytest.mark.kingdom_cards([astrolabe, captain, duke, farm, gardens, marchland, philosophers_stone, stash, village, vineyard])
def test_captain_no_options(human: Human, game: Game):
    # the only non-Command Action pile is Village; clear it
    # so there will be no valid options
    game.supply.get_pile("Village").cards.clear()

    human.hand.add(captain)
    assert len(human.hand) == 1

    human.play(captain, game)
    assert human.state.actions == 0
    assert len(human.hand) == 0

    human.start_cleanup_phase(game)

    human.start_turn(game)
    assert human.state.actions == 1
    assert len(human.hand) == 5


@pytest.mark.expansions([base_set, intrigue_set, seaside_set, alchemy_set, promos_set])
@pytest.mark.kingdom_cards([astrolabe, captain, duke, farm, gardens, marchland, philosophers_stone, stash, village, vineyard])
def test_captain_one_option(human: Human, game: Game):
    # the only non-Command Action pile is Village

    human.hand.add(captain)
    assert len(human.hand) == 1

    human.play(captain, game)
    assert human.state.actions == 2
    assert len(human.hand) == 1

    human.start_cleanup_phase(game)

    human.start_turn(game)
    assert human.state.actions == 3
    assert len(human.hand) == 6
