from pyminion.core import get_action_cards, get_treasure_cards, get_victory_cards
from pyminion.expansions.base import gold, silver, copper, province, duchy, estate, market, smithy
from pyminion.expansions.intrigue import nobles


def test_get_action_cards():
    cards_in = [
        market,
        gold,
        estate,
        nobles,
        province,
        silver,
        duchy,
        smithy,
    ]
    cards_out = list(get_action_cards(cards_in))
    assert len(cards_out) == 3
    assert cards_out[0].name == "Market"
    assert cards_out[1].name == "Nobles"
    assert cards_out[2].name == "Smithy"


def test_get_treasure_cards():
    cards_in = [
        gold,
        estate,
        silver,
        duchy,
        copper,
        smithy,
        estate,
        copper,
    ]
    cards_out = list(get_treasure_cards(cards_in))
    assert len(cards_out) == 4
    assert cards_out[0].name == "Gold"
    assert cards_out[1].name == "Silver"
    assert cards_out[2].name == "Copper"
    assert cards_out[3].name == "Copper"


def test_get_victory_cards():
    cards_in = [
        gold,
        estate,
        province,
        silver,
        duchy,
        copper,
        smithy,
        nobles,
    ]
    cards_out = list(get_victory_cards(cards_in))
    assert len(cards_out) == 4
    assert cards_out[0].name == "Estate"
    assert cards_out[1].name == "Province"
    assert cards_out[2].name == "Duchy"
    assert cards_out[3].name == "Nobles"
