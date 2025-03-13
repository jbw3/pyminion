import pytest
from pyminion.core import Card, Pile
from pyminion.exceptions import CardNotFound, EmptyPile
from pyminion.expansions.base import copper, estate


def test_make_pile():
    estates: list[Card] = [estate for x in range(8)]
    estate_pile = Pile(estates)
    assert len(estate_pile) == 8
    assert estate_pile.name == "Estate"

    assert len(estate_pile.unique_cards) == 1
    assert estate_pile.unique_cards[0].name == "Estate"


def test_make_mixed_pile():
    mixed = Pile([estate, copper])
    assert len(mixed) == 2
    assert mixed.name == "Estate/Copper"

    assert len(mixed.unique_cards) == 2
    assert mixed.unique_cards[0].name == "Estate"
    assert mixed.unique_cards[1].name == "Copper"


def test_draw_empty_pile():
    pile = Pile([copper])
    assert len(pile) == 1
    pile.remove(copper)
    assert len(pile) == 0
    with pytest.raises(EmptyPile):
        pile.remove(copper)


def test_draw_wrong_card():
    pile = Pile([copper])
    with pytest.raises(CardNotFound):
        pile.remove(estate)


def test_get_top_pile():
    pile = Pile([estate, copper])
    assert len(pile) == 2

    assert pile.get_top().name == "Estate"
    assert len(pile) == 2

    pile.remove(estate)
    assert len(pile) == 1

    assert pile.get_top().name == "Copper"
    assert len(pile) == 1
