from pyminion.expansions.base import base_set, copper, gold
from pyminion.expansions.intrigue import intrigue_set
from pyminion.expansions.alchemy import (
    alchemy_set,
    potion,
    apprentice,
    herbalist,
)
from pyminion.expansions.promos import (
    BlackMarket,
    promos_set,
    black_market,
    church,
    dismantle,
    envoy,
    governor,
    marchland,
    stash,
    walled_village,
)
from pyminion.game import Game
import pytest


# set up the kingdom such that cards with potion cost are
# in the black market deck but not in the kingdom cards
@pytest.mark.expansions([alchemy_set, promos_set])
@pytest.mark.kingdom_cards([
    black_market,
    church,
    dismantle,
    envoy,
    governor,
    marchland,
    stash,
    walled_village,
    apprentice,
    herbalist,
])
def test_black_market_setup(multiplayer_game: Game):
    black_market_deck = multiplayer_game.get_non_supply_pile(BlackMarket.DECK_NAME)
    assert any(card.base_cost.potions > 0 for card in black_market_deck)

    assert any(pile.name == "Potion" for pile in multiplayer_game.supply.piles)


@pytest.mark.expansions([base_set, intrigue_set, promos_set])
@pytest.mark.kingdom_cards([black_market])
def test_black_market_buy(multiplayer_game: Game, monkeypatch):
    human = multiplayer_game.players[0]

    black_market_deck = multiplayer_game.get_non_supply_pile(BlackMarket.DECK_NAME)
    assert len(black_market_deck) == 50

    top_card = black_market_deck.get_top()
    other_top_card_names = set(c.name for c in black_market_deck.cards[-3:-1])

    human.hand.cards.clear()
    human.hand.add(black_market)
    human.hand.add(copper)
    human.hand.add(gold)
    human.hand.add(gold)
    human.hand.add(potion)

    responses = ["gold,gold,potion", "", top_card.name]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(black_market, multiplayer_game)
    assert len(responses) == 0
    assert human.state.money == 8 - top_card.base_cost.money
    assert human.state.buys == 1
    assert len(human.hand) == 1
    assert human.hand.cards[0].name == "Copper"
    assert len(human.playmat) == 4
    assert set(c.name for c in human.playmat) == {"Black Market", "Gold", "Potion"}
    assert len(human.discard_pile) == 1
    assert human.discard_pile.cards[0].name == top_card.name
    assert len(black_market_deck) == 49
    bottom_card_names = set(c.name for c in black_market_deck.cards[:2])
    assert other_top_card_names == bottom_card_names


@pytest.mark.expansions([base_set, intrigue_set, promos_set])
@pytest.mark.kingdom_cards([black_market])
def test_black_market_no_buy(multiplayer_game: Game, monkeypatch):
    human = multiplayer_game.players[0]

    black_market_deck = multiplayer_game.get_non_supply_pile(BlackMarket.DECK_NAME)
    assert len(black_market_deck) == 50

    top_card_names = set(c.name for c in black_market_deck.cards[-3:])

    human.hand.cards.clear()
    human.hand.add(black_market)
    human.hand.add(copper)
    human.hand.add(gold)
    human.hand.add(gold)

    responses = ["gold,gold", "", ""]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(black_market, multiplayer_game)
    assert len(responses) == 0
    assert human.state.money == 8
    assert human.state.buys == 1
    assert len(human.hand) == 1
    assert human.hand.cards[0].name == "Copper"
    assert len(human.playmat) == 3
    assert set(c.name for c in human.playmat) == {"Black Market", "Gold"}
    assert len(human.discard_pile) == 0
    assert len(black_market_deck) == 50
    bottom_card_names = set(c.name for c in black_market_deck.cards[:3])
    assert top_card_names == bottom_card_names
