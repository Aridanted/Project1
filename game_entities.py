"""CSC111 Project 1: Text Adventure Game - Game Entities

Instructions (READ THIS FIRST!)
===============================

This Python module contains the entity classes for Project 1, to be imported and used by
 the `adventure` module.
 Please consult the project handout for instructions and details.

Copyright and Usage Information
===============================

This file is provided solely for the personal and private use of students
taking CSC111 at the University of Toronto St. George campus. All forms of
distribution of this code, whether as given or with any changes, are
expressly prohibited. For more information on copyright for CSC111 materials,
please consult our Course Syllabus.

This file is Copyright (c) 2026 CSC111 Teaching Team
"""
from dataclasses import dataclass


@dataclass
class Location:
    """A location in our text adventure game world.

    Instance Attributes:
        - id_num: A unique integer identifier for this location
        - brief_description: A short description shown on subsequent visits to this location
        - long_description: A detailed description shown on the first visit to this location
        - available_commands: A dictionary mapping command strings to location IDs that the command leads to,
                             or special actions (represented as strings starting with 'action:')
        - items: A list of item names currently present at this location
        - visited: A boolean indicating whether the player has visited this location before

    Representation Invariants:
        - self.id_num >= 0
        - self.brief_description != ''
        - self.long_description != ''
    """

    id_num: int
    brief_description: str
    long_description: str
    available_commands: dict[str, int | str]
    items: list[str]
    visited: bool = False


@dataclass
class Item:
    """An item in our text adventure game world.

    Instance Attributes:
        - name: The name of the item (used as a unique identifier)
        - description: A detailed description of what the item is
        - start_position: The location ID where this item starts the game
        - target_position: The location ID where this item should be deposited for points
        - target_points: The number of points awarded for depositing this item at its target location
        - pickup_points: The number of points awarded for picking up this item
        - current_position: The current location ID of this item, or -1 if it's in the player's inventory

    Representation Invariants:
        - self.name != ''
        - self.start_position >= -1
        - self.target_position >= -1
        - self.target_points >= 0
        - self.pickup_points >= 0
        - self.current_position >= -1
    """

    name: str
    description: str
    start_position: int
    target_position: int
    target_points: int
    pickup_points: int = 0
    current_position: int = -1

    def __post_init__(self) -> None:
        """Initialize the current position to the starting position if not already set.
        A start_position of -1 means the item does not exist in the world at game start
        (it will be spawned dynamically during gameplay).
        """
        if self.current_position == -1:
            self.current_position = self.start_position


class Player:
    """Represents the player in the text adventure game.

    Instance Attributes:
        - inventory: A list of Item objects that the player is currently carrying
        - score: The player's current score
        - moves_made: The number of moves the player has made so far
        - has_friend_permission: Whether the player has obtained their friend's permission (for puzzle)

    Representation Invariants:
        - self.score >= 0
        - self.moves_made >= 0
    """

    inventory: list[Item]
    score: int
    moves_made: int
    has_friend_permission: bool

    def __init__(self) -> None:
        """Initialize a new player with an empty inventory, zero score, and zero moves.

        >>> player = Player()
        >>> len(player.inventory)
        0
        >>> player.score
        0
        >>> player.moves_made
        0
        >>> player.has_friend_permission
        False
        """
        self.inventory = []
        self.score = 0
        self.moves_made = 0
        self.has_friend_permission = False

    def add_item(self, item: Item) -> None:
        """Add the given item to the player's inventory.

        >>> player = Player()
        >>> item = Item("USB Drive", "A USB drive", 7, 1, 20, 5)
        >>> player.add_item(item)
        >>> len(player.inventory)
        1
        >>> player.inventory[0].name
        'USB Drive'

        Preconditions:
            - item is not already in self.inventory
        """
        self.inventory.append(item)

    def remove_item(self, item_name: str) -> Item | None:
        """Remove and return the item with the given name from the player's inventory.
        Return None if no such item exists in the inventory.

        >>> player = Player()
        >>> item = Item("USB Drive", "A USB drive", 7, 1, 20, 5)
        >>> player.add_item(item)
        >>> removed = player.remove_item("USB Drive")
        >>> removed.name
        'USB Drive'
        >>> len(player.inventory)
        0
        >>> player.remove_item("Nonexistent Item") is None
        True
        """
        for item in self.inventory:
            if item.name.lower() == item_name.lower():
                self.inventory.remove(item)
                return item
        return None

    def has_item(self, item_name: str) -> bool:
        """Return True if the player has an item with the given name in their inventory.

        >>> player = Player()
        >>> item = Item("Lucky Mug", "A mug", 15, 1, 20, 5)
        >>> player.add_item(item)
        >>> player.has_item("Lucky Mug")
        True
        >>> player.has_item("lucky mug")
        True
        >>> player.has_item("USB Drive")
        False
        """
        return any(item.name.lower() == item_name.lower() for item in self.inventory)

    def get_item(self, item_name: str) -> Item | None:
        """Return the item with the given name from the player's inventory, or None if not found.

        >>> player = Player()
        >>> item1 = Item("USB Drive", "A USB drive", 7, 1, 20, 5)
        >>> item2 = Item("Lucky Mug", "A mug", 15, 1, 20, 5)
        >>> player.add_item(item1)
        >>> player.add_item(item2)
        >>> found = player.get_item("USB Drive")
        >>> found.name
        'USB Drive'
        >>> player.get_item("Nonexistent") is None
        True
        """
        for item in self.inventory:
            if item.name.lower() == item_name.lower():
                return item
        return None

    def add_score(self, points: int) -> None:
        """Add the given number of points to the player's score.

        >>> player = Player()
        >>> player.score
        0
        >>> player.add_score(10)
        >>> player.score
        10
        >>> player.add_score(25)
        >>> player.score
        35

        Preconditions:
            - points >= 0
        """
        self.score += points

    def increment_moves(self) -> None:
        """Increment the number of moves the player has made by 1.

        >>> player = Player()
        >>> player.moves_made
        0
        >>> player.increment_moves()
        >>> player.moves_made
        1
        >>> player.increment_moves()
        >>> player.moves_made
        2
        """
        self.moves_made += 1


if __name__ == "__main__":
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    })
