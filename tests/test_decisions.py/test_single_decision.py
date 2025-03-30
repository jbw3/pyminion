import pytest
from pyminion.human import single_decision
from pyminion.exceptions import InvalidSingleCardInput
from pyminion.expansions.base import copper, estate

valid_card_names = [copper.name, copper.name, estate.name]


def test_no_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert single_decision(prompt="test", valid_strings=valid_card_names) is None


def test_valid_card(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "Copper")
    card_name = single_decision(prompt="test", valid_strings=valid_card_names)
    assert card_name == copper.name


def test_invalid_card(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "Silver")
    with pytest.raises(
        InvalidSingleCardInput, match="Invalid input, Silver is not a valid selection"
    ):
        single_decision(prompt="test", valid_strings=valid_card_names)


def test_invalid_spelling(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "coopper")
    with pytest.raises(
        InvalidSingleCardInput, match="Invalid input, coopper is not a valid selection"
    ):
        single_decision(prompt="test", valid_strings=valid_card_names)


def test_confirm_case_insensitive(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "copper")
    card_name = single_decision(prompt="test", valid_strings=valid_card_names)
    assert card_name == copper.name
