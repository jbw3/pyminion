import pytest
from pyminion.core import Card, CardType, Pile, Supply
from pyminion.exceptions import EmptyPile, PileNotFound
from pyminion.expansions.base import copper, duchy, estate, gold, province, silver
from pyminion.expansions.promos import sauna, avanto


def test_create_supply():

    estates = Pile([estate for x in range(8)])
    duchies = Pile([duchy for x in range(8)])
    provinces = Pile([province for x in range(8)])
    coppers = Pile([copper for x in range(8)])
    silvers = Pile([silver for x in range(8)])
    golds = Pile([gold for x in range(8)])
    supply = Supply([estates, duchies, provinces], [coppers, silvers, golds], [])
    assert len(supply) == 6


def test_supply_repr(supply: Supply):
    s = repr(supply)
    assert "Estate" in s
    assert "Duchy" in s
    assert "Province" in s
    assert "Copper" in s
    assert "Silver" in s
    assert "Gold" in s


def test_gain_card(supply: Supply):
    assert len(supply.piles[0]) == 8
    card = supply.gain_card(estate)
    assert card == estate
    assert len(supply.piles[0]) == 7


def test_gain_empty_pile(supply: Supply):
    for x in range(8):
        supply.gain_card(estate)
    assert len(supply.piles[0]) == 0
    with pytest.raises(EmptyPile):
        supply.gain_card(estate)


def test_pile_not_found(supply: Supply):
    fake_card = Card(name="fake", cost=0, type=(CardType.Action,))
    with pytest.raises(PileNotFound):
        supply.gain_card(fake_card)


def test_return_card(supply: Supply):
    estate_pile = supply.get_pile_by_card("Estate")
    assert len(estate_pile) == 8

    card = supply.gain_card(estate)
    assert len(estate_pile) == 7

    supply.return_card(card)
    assert len(estate_pile) == 8


def test_available_cards(supply: Supply):
    cards = supply.available_cards()
    assert len(cards) == len(supply)
    assert estate in cards
    for card in cards:
        assert isinstance(card, Card)


def test_available_cards_empty_pile(supply: Supply):
    for i in range(8):
        supply.piles[0].remove(estate)

    cards = supply.available_cards()
    assert len(cards) == 5
    assert estate not in cards
    for card in cards:
        assert isinstance(card, Card)


def test_empty_piles(supply: Supply):
    for i in range(8):
        supply.gain_card(card=estate)
    assert supply.num_empty_piles() == 1
    for i in range(8):
        supply.gain_card(card=duchy)
    assert supply.num_empty_piles() == 2
    for i in range(30):
        supply.gain_card(card=gold)
    assert supply.num_empty_piles() == 3


def test_pile_length(supply: Supply):
    assert supply.pile_length(card_name="Province") == 8
    supply.gain_card(card=province)
    assert supply.pile_length(card_name="Province") == 7


def test_get_pile():
    sauna_avanto_cards: list[Card] = []
    sauna_avanto_cards += [sauna] * 5
    sauna_avanto_cards += [avanto] * 5
    sauna_avanto_pile = Pile(sauna_avanto_cards)
    supply = Supply([], [], [sauna_avanto_pile])

    pile = supply.get_pile("Sauna/Avanto")
    assert pile.name == "Sauna/Avanto"
    assert pile.get_top().name == "Sauna"


def test_get_pile_by_card():
    sauna_avanto_cards: list[Card] = []
    sauna_avanto_cards += [sauna] * 5
    sauna_avanto_cards += [avanto] * 5
    sauna_avanto_pile = Pile(sauna_avanto_cards)
    supply = Supply([], [], [sauna_avanto_pile])

    pile1 = supply.get_pile_by_card("Sauna")
    assert pile1.name == "Sauna/Avanto"
    assert pile1.get_top().name == "Sauna"

    pile2 = supply.get_pile_by_card("Avanto")
    assert pile2.name == "Sauna/Avanto"
    assert pile2.get_top().name == "Sauna"
