from pyminion.expansions.base import base_set, throne_room
from pyminion.expansions.promos import promos_set, walled_village
from pyminion.game import Game
from pyminion.human import Human


def test_walled_village_topdeck(human: Human, game: Game, monkeypatch):
    responses = ["y"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.hand.add(walled_village)

    human.play(walled_village, game)
    assert len(responses) == 1
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Walled Village"
    assert len(human.hand) == 1
    assert human.state.actions == 2

    human.start_cleanup_phase(game)
    assert len(responses) == 0
    assert len(human.playmat) == 0
    discard_pile_names = set(card.name for card in human.discard_pile)
    assert "Walled Village" not in discard_pile_names
    new_hand_names = set(card.name for card in human.hand)
    assert "Walled Village" in new_hand_names

    human.end_turn(game)


def test_walled_village_no_topdeck(human: Human, game: Game, monkeypatch):
    responses = ["n"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.hand.add(walled_village)

    human.play(walled_village, game)
    assert len(responses) == 1
    assert len(human.playmat) == 1
    assert human.playmat.cards[0].name == "Walled Village"
    assert len(human.hand) == 1
    assert human.state.actions == 2

    human.start_cleanup_phase(game)
    assert len(responses) == 0
    assert len(human.playmat) == 0
    discard_pile_names = set(card.name for card in human.discard_pile)
    assert "Walled Village" in discard_pile_names
    new_hand_names = set(card.name for card in human.hand)
    assert "Walled Village" not in new_hand_names

    human.end_turn(game)


def test_walled_village_no_topdeck_option(human: Human, game: Game, monkeypatch):
    responses = []
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    for _ in range(3):
        human.hand.add(walled_village)

    for _ in range(3):
        human.play(walled_village, game)

    assert len(responses) == 0
    assert len(human.playmat) == 3
    for i in range(3):
        assert human.playmat.cards[i].name == "Walled Village"
    assert len(human.hand) == 3
    assert human.state.actions == 4

    human.start_cleanup_phase(game)
    assert len(responses) == 0
    assert len(human.playmat) == 0
    discard_pile_count = sum(1 for card in human.discard_pile if card.name == "Walled Village")
    assert discard_pile_count == 3
    new_hand_count = sum(1 for card in human.hand if card.name == "Walled Village")
    assert new_hand_count == 0

    human.end_turn(game)


def test_walled_village_throne_room(human: Human, game: Game, monkeypatch):
    responses = ["walled village", "y"]
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))

    human.hand.add(throne_room)
    human.hand.add(walled_village)

    human.play(throne_room, game)
    assert len(responses) == 1
    assert len(human.playmat) == 2
    assert set(card.name for card in human.playmat) == {"Walled Village", "Throne Room"}
    assert len(human.hand) == 2
    assert human.state.actions == 4

    human.start_cleanup_phase(game)
    assert len(responses) == 0
    assert len(human.playmat) == 0
    discard_pile_names = set(card.name for card in human.discard_pile)
    assert "Throne Room" in discard_pile_names
    assert "Walled Village" not in discard_pile_names
    new_hand_count = sum(1 for card in human.hand if card.name == "Walled Village")
    assert new_hand_count == 1

    human.end_turn(game)
