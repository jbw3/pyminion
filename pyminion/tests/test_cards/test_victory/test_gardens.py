from pyminion.models.core import Turn, Player, Game
from pyminion.models.base import Gardens, Copper, Estate, gardens, copper, estate


def test_gardens_score_10_cards(turn: Turn, player: Player):
    player.hand.add(gardens)
    player.deck.remove(copper)
    assert len(player.get_all_cards()) == 10
    assert player.hand.cards[0].score(player) == 1


def test_gardens_score_9_cards(turn: Turn, player: Player):
    player.hand.add(gardens)
    player.deck.remove(copper)
    player.deck.remove(copper)
    assert len(player.get_all_cards()) == 9
    assert player.hand.cards[0].score(player) == 0


def test_gardens_score_over_11_cards(turn: Turn, player: Player):
    player.hand.add(gardens)
    assert len(player.get_all_cards()) == 11
    assert player.hand.cards[0].score(player) == 1


def test_gardens_score_21_cards(turn: Turn, player: Player):
    player.hand.add(gardens)
    for i in range(10):
        player.deck.add(copper)
    assert len(player.get_all_cards()) == 21
    assert player.hand.cards[0].score(player) == 2
