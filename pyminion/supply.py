from typing import TYPE_CHECKING

from pyminion.core import Card, Pile
from pyminion.exceptions import EmptyPile, PileNotFound
from pyminion.expansions.alchemy import potion

if TYPE_CHECKING:
    from pyminion.game import Game
    from pyminion.player import Player

class Supply:
    """
    Collection of card piles that make up the game's supply.

    """

    def __init__(
            self,
            basic_score_piles: list[Pile],
            basic_treasure_piles: list[Pile],
            kingdom_piles: list[Pile],
    ):
        self.basic_score_piles = basic_score_piles
        self.basic_treasure_piles = basic_treasure_piles
        self.kingdom_piles = kingdom_piles
        self.piles = basic_score_piles + basic_treasure_piles + kingdom_piles

    def __repr__(self):
        return str(self.available_cards())

    def __len__(self):
        return len(self.piles)

    def _get_pile_str(self, pile: Pile, name_padding: int, player: "Player", game: "Game") -> str:
        count_str = f"({len(pile)})"
        s = f"{count_str:>4}"
        if len(pile) == 0:
            s += "  $-"
            name = pile.name
        else:
            top_card = pile.get_top()
            s += f" {top_card.get_cost(player, game):>3}"
            name = top_card.name
        s += f" {name:{name_padding}}"
        return s

    def get_pretty_string(self, player: "Player", game: "Game") -> str:
        max_len = max(len(pile.name) for pile in self.piles)
        kingdom_top = self.kingdom_piles[5:]
        kingdom_bottom = self.kingdom_piles[:5]
        s = "\nSupply:\n"
        s += "  ".join(f'{self._get_pile_str(pile, max_len, player, game)}' for pile in self.basic_score_piles) + "\n"
        s += "  ".join(f'{self._get_pile_str(pile, max_len, player, game)}' for pile in self.basic_treasure_piles) + "\n"
        s += "  ".join(f'{self._get_pile_str(pile, max_len, player, game)}' for pile in kingdom_top) + "\n"
        s += "  ".join(f'{self._get_pile_str(pile, max_len, player, game)}' for pile in kingdom_bottom) + "\n"
        return s

    def add_potions(self, game: "Game") -> None:
        potions_pile = Pile([potion] * potion.get_pile_starting_count(game))
        self.basic_treasure_piles.insert(0, potions_pile)
        self.piles.append(potions_pile)

    def get_pile(self, pile_name: str) -> Pile:
        """
        Get a pile by name.

        """
        for pile in self.piles:
            if pile.name == pile_name:
                return pile
        raise PileNotFound(f"{pile_name} pile is not valid")

    def get_pile_by_card(self, card_name: str) -> Pile:
        """
        Get a pile by the name of one of its cards.

        """
        for pile in self.piles:
            for card in pile.unique_cards:
                if card.name == card_name:
                    return pile
        raise PileNotFound(f"No piles for {card_name} card")

    def gain_card(self, card: Card) -> Card:
        """
        Gain a card from the supply.

        """
        pile = self.get_pile_by_card(card.name)
        try:
            return pile.remove(card)

        except EmptyPile as e:
            raise e

    def return_card(self, card: Card) -> None:
        """
        Return a card to the supply.

        """
        pile = self.get_pile_by_card(card.name)
        pile.add(card)

    def available_cards(self) -> list[Card]:
        """
        Returns a list containing the top card from each non-empty pile in the supply.

        """
        cards = [pile.get_top() for pile in self.piles if pile]
        return cards

    def num_empty_piles(self) -> int:
        """
        Returns the number of empty piles in the supply.

        """
        empty_piles: int = 0
        for pile in self.piles:
            if len(pile) == 0:
                empty_piles += 1
        return empty_piles

    def pile_length(self, card_name: str) -> int:
        """
        Get the number of cards in a specified pile in the supply.

        """
        pile = self.get_pile_by_card(card_name)
        return len(pile)
