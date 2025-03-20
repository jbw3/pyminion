from pyminion.expansions.base import copper, estate, province
from pyminion.expansions.promos import governor
from pyminion.game import Game


def test_governor_draw(multiplayer4_game: Game, monkeypatch):
    player1 = multiplayer4_game.players[0]
    other_players = multiplayer4_game.players[1:]

    player1.hand.add(governor)
    assert len(player1.hand) == 6
    for player in other_players:
        assert len(player.hand) == 5

    responses = ["1"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    player1.play(governor, multiplayer4_game)
    assert len(responses) == 0
    assert player1.state.actions == 1
    assert len(player1.hand) == 8
    for player in other_players:
        assert len(player.hand) == 6


def test_governor_gain_treasure(multiplayer4_game: Game, monkeypatch):
    player1 = multiplayer4_game.players[0]
    other_players = multiplayer4_game.players[1:]

    player1.hand.add(governor)
    assert len(player1.discard_pile) == 0
    for player in other_players:
        assert len(player.discard_pile) == 0

    responses = ["2"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    player1.play(governor, multiplayer4_game)
    assert len(responses) == 0
    assert player1.state.actions == 1
    assert len(player1.hand) == 5
    assert len(player1.discard_pile) == 1
    assert player1.discard_pile.cards[0].name == "Gold"
    for player in other_players:
        assert len(player.hand) == 5
        assert len(player.discard_pile) == 1
        assert player.discard_pile.cards[0].name == "Silver"


def test_governor_trash_and_gain(multiplayer4_game: Game, monkeypatch):
    players = multiplayer4_game.players

    for player in players:
        player.hand.cards.clear()

    players[0].hand.add(copper)
    players[1].hand.add(estate)
    # players[2] has no cards in hand
    players[3].hand.add(copper)

    players[0].hand.add(governor)
    for player in players:
        assert len(player.discard_pile) == 0

    responses = [
        # player 1
        "3", "y", "copper", "estate",
        # player 2
        "y", "estate", "silver",
        # player 3 has no cards in hand
        # player 4
        "n",
    ]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    players[0].play(governor, multiplayer4_game)
    assert len(responses) == 0

    assert players[0].state.actions == 1
    assert len(players[0].hand) == 0
    assert len(players[0].discard_pile) == 1
    assert players[0].discard_pile.cards[0].name == "Estate"

    assert len(players[1].hand) == 0
    assert len(players[1].discard_pile) == 1
    assert players[1].discard_pile.cards[0].name == "Silver"

    assert len(players[2].hand) == 0
    assert len(players[2].discard_pile) == 0

    assert len(players[3].hand) == 1
    assert len(players[3].discard_pile) == 0


def test_governor_trash_and_gain_no_valid_cards(multiplayer4_game: Game, monkeypatch):
    players = multiplayer4_game.players

    for player in players:
        player.hand.cards.clear()

    players[0].hand.add(province)
    players[1].hand.add(copper)
    players[2].hand.add(copper)
    players[3].hand.add(copper)

    players[0].hand.add(governor)
    for player in players:
        assert len(player.discard_pile) == 0

    responses = [
        # player 1
        "3", "y", "province",
        # player 2
        "y", "copper",
        # player 3
        "y", "copper",
        # player 4
        "y", "copper",
    ]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    players[0].play(governor, multiplayer4_game)
    assert len(responses) == 0

    assert players[0].state.actions == 1
    for player in players:
        assert len(player.hand) == 0
        assert len(player.discard_pile) == 0
