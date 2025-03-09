from pyminion.expansions.base import copper, silver, gold, estate, duchy
from pyminion.expansions.promos import envoy
from pyminion.game import Game


def test_envoy(multiplayer_game: Game, monkeypatch):
    responses = ["gold"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    player1 = multiplayer_game.players[0]

    player1.deck.add(copper)
    player1.deck.add(silver)
    player1.deck.add(gold)
    player1.deck.add(estate)
    player1.deck.add(duchy)

    player1.hand.cards.clear()
    player1.hand.add(envoy)
    assert len(player1.hand) == 1

    player1.play(envoy, multiplayer_game)
    assert len(responses) == 0
    assert player1.state.actions == 0
    assert len(player1.hand) == 4
    assert set(c.name for c in player1.hand) == {"Copper", "Silver", "Estate", "Duchy"}
    assert len(player1.discard_pile) == 1
    assert player1.discard_pile.cards[0].name == "Gold"


def test_envoy_one_card(multiplayer_game: Game, monkeypatch):
    responses = []
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    player1 = multiplayer_game.players[0]

    player1.deck.cards.clear()
    player1.deck.add(copper)

    player1.hand.cards.clear()
    player1.hand.add(envoy)
    assert len(player1.hand) == 1

    player1.play(envoy, multiplayer_game)
    assert len(responses) == 0
    assert player1.state.actions == 0
    assert len(player1.hand) == 0
    assert len(player1.discard_pile) == 1
    assert player1.discard_pile.cards[0].name == "Copper"


def test_envoy_no_cards(multiplayer_game: Game, monkeypatch):
    responses = []
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    player1 = multiplayer_game.players[0]

    player1.deck.cards.clear()

    player1.hand.cards.clear()
    player1.hand.add(envoy)
    assert len(player1.hand) == 1

    player1.play(envoy, multiplayer_game)
    assert len(responses) == 0
    assert player1.state.actions == 0
    assert len(player1.hand) == 0
    assert len(player1.discard_pile) == 0
