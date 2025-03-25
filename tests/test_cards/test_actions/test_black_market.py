from pyminion.expansions.base import base_set, copper, gold
from pyminion.expansions.intrigue import intrigue_set
from pyminion.expansions.alchemy import alchemy_set
from pyminion.expansions.promos import BlackMarket, promos_set, black_market
from pyminion.game import Game
from pyminion.human import Human
import pytest


# set up the kingdom such that cards with potion cost have to be
# in the black market deck
@pytest.mark.expansions([alchemy_set, promos_set])
@pytest.mark.kingdom_cards([black_market])
def test_black_market_setup(game: Game):
    black_market_deck = game.get_non_supply_pile(BlackMarket.DECK_NAME)
    assert any(card.base_cost.potions > 0 for card in black_market_deck)

    assert any(pile.name == "Potion" for pile in game.supply.piles)


@pytest.mark.expansions([base_set, intrigue_set, promos_set])
@pytest.mark.kingdom_cards([black_market])
def test_black_market_buy(human: Human, game: Game, monkeypatch):
    black_market_deck = game.get_non_supply_pile(BlackMarket.DECK_NAME)
    assert len(black_market_deck) == 50

    top_card = black_market_deck.get_top()

    human.hand.add(black_market)
    human.hand.add(copper)
    human.hand.add(gold)
    human.hand.add(gold)

    responses = ["gold,gold", "", top_card.name]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.play(black_market, game)
    assert len(responses) == 0
    assert human.state.money == 8 - top_card.base_cost.money
    assert human.state.buys == 1
    assert len(human.hand) == 1
    assert human.hand.cards[0].name == "Copper"
    assert len(human.playmat) == 3
    assert set(c.name for c in human.playmat) == {"Black Market", "Gold"}
    assert len(human.discard_pile) == 1
    assert human.discard_pile.cards[0].name == top_card.name
