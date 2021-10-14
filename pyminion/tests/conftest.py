import pytest

from pyminion.base_set.base_cards import copper, silver, gold, estate, duchy, province
from pyminion.models.base import (
    Pile,
    Deck,
    DiscardPile,
    Hand,
    Playmat,
    Player,
    Turn,
    Supply,
)


NUM_COPPER = 7
NUM_ESTATE = 3


@pytest.fixture
def deck():
    start_cards = [copper for x in range(NUM_COPPER)] + [
        estate for x in range(NUM_ESTATE)
    ]
    deck = Deck(cards=start_cards)
    return deck


@pytest.fixture
def deck():
    start_cards = [copper for x in range(NUM_COPPER)] + [
        estate for x in range(NUM_ESTATE)
    ]
    deck = Deck(cards=start_cards)
    return deck


@pytest.fixture
def player(deck):
    discard = DiscardPile()
    hand = Hand()
    playmat = Playmat()
    player = Player(deck=deck, discard=discard, hand=hand, playmat=playmat)
    return player


@pytest.fixture
def turn(player):
    turn = Turn(player=player)
    return turn


@pytest.fixture
def supply():
    estates = Pile([estate for x in range(8)])
    duchies = Pile([duchy for x in range(8)])
    provinces = Pile([province for x in range(8)])
    coppers = Pile([copper for x in range(8)])
    silvers = Pile([silver for x in range(8)])
    golds = Pile([gold for x in range(8)])
    supply = Supply([estates, duchies, provinces, coppers, silvers, golds])
    return supply