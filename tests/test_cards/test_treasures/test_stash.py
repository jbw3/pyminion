from pyminion.expansions.base import base_set
from pyminion.expansions.promos import promos_set, stash
from pyminion.game import Game
from pyminion.player import Player
import pytest


def test_stash_play(player: Player, game: Game):
    player.hand.add(stash)

    player.play(stash, game)
    assert player.state.money == 2


@pytest.mark.expansions([base_set, promos_set])
@pytest.mark.kingdom_cards([stash])
def test_stash_shuffle(multiplayer_game: Game, monkeypatch):
    player = multiplayer_game.players[0]

    for _ in range(3):
        player.deck.add(stash)

    assert len(player.deck) == 8

    responses = ["1", "7", "3"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    player.deck.shuffle()

    assert sum(1 for c in player.deck if c.name == "Stash") == 3
    assert player.deck.cards[0].name == "Stash"
    assert player.deck.cards[2].name == "Stash"
    assert player.deck.cards[-1].name == "Stash"


@pytest.mark.expansions([base_set, promos_set])
@pytest.mark.kingdom_cards([stash])
def test_stash_shuffle_empty_deck(multiplayer_game: Game, monkeypatch):
    player = multiplayer_game.players[0]

    player.deck.cards.clear()
    for _ in range(3):
        player.deck.add(stash)

    assert len(player.deck) == 3

    responses = []
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    player.deck.shuffle()

    assert len(player.deck) == 3
    assert player.deck.cards[0].name == "Stash"
    assert player.deck.cards[1].name == "Stash"
    assert player.deck.cards[2].name == "Stash"
