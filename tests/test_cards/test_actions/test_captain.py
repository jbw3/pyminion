from pyminion.expansions.base import base_set, smithy, village
from pyminion.expansions.promos import promos_set, captain
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
