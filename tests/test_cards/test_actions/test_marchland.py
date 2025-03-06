from pyminion.expansions.base import base_set, estate, duchy
from pyminion.expansions.promos import marchland, promos_set
from pyminion.game import Game
from pyminion.human import Human
from pyminion.player import Player
import pytest


@pytest.mark.expansions([base_set, promos_set])
@pytest.mark.kingdom_cards([marchland])
def test_marchland_gain(human: Human, game: Game, monkeypatch):
    human.hand.cards.clear()

    human.hand.add(estate)
    human.hand.add(estate)
    human.hand.add(duchy)

    responses = ["estate, duchy"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    assert human.state.money == 0
    assert human.state.buys == 1
    assert len(human.hand) == 3
    assert set(c.name for c in human.hand) == {"Estate", "Duchy"}

    human.gain(marchland, game)

    assert human.state.money == 2
    assert human.state.buys == 2
    assert len(human.hand) == 1
    assert human.hand.cards[0].name == "Estate"


def test_marchland_vp(player: Player):
    player.deck.cards.clear()
    player.discard_pile.cards.clear()

    assert marchland.score(player) == 0

    # should be 0 points while less than 3 victory cards
    for _ in range(2):
        player.hand.add(estate)
        assert marchland.score(player) == 0

    # should be 1 point for 3-5 victory cards
    for _ in range(3):
        player.hand.add(duchy)
        assert marchland.score(player) == 1

    # should be 2 points for 6-8 victory cards
    for _ in range(3):
        player.hand.add(marchland)
        assert marchland.score(player) == 2
