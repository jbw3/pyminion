from pyminion.models.core import (
    Player,
    Supply,
    Trash,
    Game,
)
from pyminion.models.base import province, duchy, estate, gold


def test_game_fixture(game: Game):
    assert len(game.players) == 1
    assert isinstance(game.supply, Supply)
    assert isinstance(game.trash, Trash)
    assert not game.trash


def test_create_game_one_player(player: Player, trash: Trash, supply: Supply):
    game = Game(players=[player], supply=supply, trash=trash)
    assert len(game.players) == 1
    assert isinstance(game.supply, Supply)
    assert isinstance(game.trash, Trash)
    assert not game.trash


def test_game_is_over_false(game: Game):
    assert not game.is_over()


def test_game_is_over_true_provinces(game: Game):
    game.supply.gain_card(card=province)
    assert not game.is_over()
    for i in range(7):
        game.supply.gain_card(card=province)
    assert game.is_over()


def test_game_is_over_true_three_piles(game: Game):
    for i in range(8):
        game.supply.gain_card(card=estate)
    assert not game.is_over()
    for i in range(8):
        game.supply.gain_card(card=duchy)
    assert not game.is_over()
    for i in range(29):
        game.supply.gain_card(card=gold)
    assert not game.is_over()
    game.supply.gain_card(card=gold)
    assert game.is_over()
