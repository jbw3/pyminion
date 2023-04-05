from typing import TYPE_CHECKING, List, Optional, Protocol

if TYPE_CHECKING:
    from pyminion.core import Card, Player
    from pyminion.game import Game


class Decider(Protocol):
    """
    Interface for prompting a player for a decision.

    """

    def action_phase_decision(
        self,
        valid_actions: List["Card"],
        player: "Player",
        game: "Game",
    ) -> Optional["Card"]:
        raise NotImplementedError("action_phase_decision is not implemented")

    def treasure_phase_decision(
        self,
        valid_treasures: List["Card"],
        player: "Player",
        game: "Game",
    ) -> List["Card"]:
        raise NotImplementedError("treasure_phase_decision is not implemented")

    def binary_decision(
        self,
        prompt: str,
        card: "Card",
        player: "Player",
        game: "Game",
        relevant_cards: Optional[List["Card"]] = None,
    ) -> bool:
        raise NotImplementedError("binary_decision is not implemented")

    def discard_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_discard: int = 0,
        max_num_discard: int = -1,
    ) -> List["Card"]:
        raise NotImplementedError("discard_decision is not implemented")

    def trash_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_trash: int = 0,
        max_num_trash: int = -1,
    ) -> List["Card"]:
        raise NotImplementedError("trash_decision is not implemented")

    def gain_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_gain: int = 0,
        max_num_gain: int = -1,
    ) -> List["Card"]:
        raise NotImplementedError("gain_decision is not implemented")

    def topdeck_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        min_num_topdeck: int = 0,
        max_num_topdeck: int = -1,
    ) -> List["Card"]:
        raise NotImplementedError("topdeck_decision is not implemented")

    def multi_play_decision(
        self,
        prompt: str,
        card: "Card",
        valid_cards: List["Card"],
        player: "Player",
        game: "Game",
        required: bool = True,
    ) -> Optional["Card"]:
        raise NotImplementedError("multi_play_decision is not implemented")
