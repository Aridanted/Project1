"""CSC111 Project 1: Text Adventure Game - Game Manager

Instructions (READ THIS FIRST!)
===============================

This Python module contains the code for Project 1. Please consult
the project handout for instructions and details.

Copyright and Usage Information
===============================

This file is provided solely for the personal and private use of students
taking CSC111 at the University of Toronto St. George campus. All forms of
distribution of this code, whether as given or with any changes, are
expressly prohibited. For more information on copyright for CSC111 materials,
please consult our Course Syllabus.

This file is Copyright (c) 2026 CSC111 Teaching Team
"""
from __future__ import annotations
import json
from typing import Optional

from game_entities import Location, Item, Player
from event_logger import Event, EventList


MAX_MOVES = 35  # Maximum number of moves before the player loses
REQUIRED_ITEMS = ["USB Drive", "Laptop Charger", "Lucky Mug"]  # Items needed to win


class AdventureGame:
    """A text adventure game class storing all location, item and map data.

    Instance Attributes:
        - current_location_id: The ID of the location where the player currently is
        - ongoing: Whether the game is still ongoing (not won or lost)
        - player: The Player object representing the player's state
        - event_list: An EventList containing all events that have occurred in the game

    Representation Invariants:
        - self.current_location_id in self._locations
        - self.player.moves_made <= MAX_MOVES
    """

    # Private Instance Attributes:
    #   - _locations: a mapping from location id to Location object.
    #                       This represents all the locations in the game.
    #   - _items: a dictionary mapping item names to Item objects, representing all items in the game.

    _locations: dict[int, Location]
    _items: dict[str, Item]
    current_location_id: int
    ongoing: bool
    player: Player
    event_list: EventList

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """Initialize a new text adventure game, based on the data in the given file,
        setting starting location of game at the given initial location ID.

        Preconditions:
            - game_data_file is the filename of a valid game data JSON file
            - initial_location_id is a valid location ID in the game data file
        """
        self._locations, self._items = self._load_game_data(game_data_file)
        self.current_location_id = initial_location_id
        self.ongoing = True
        self.player = Player()
        self.event_list = EventList()

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], dict[str, Item]]:
        """Load locations and items from a JSON file with the given filename and
        return a tuple consisting of (1) a dictionary of locations mapping each game location's ID to a Location object,
        and (2) a dictionary of all Item objects mapped by their names.
        """
        with open(filename, 'r') as f:
            data = json.load(f)

        locations = {}
        for loc_data in data['locations']:
            location_obj = Location(
                loc_data['id'],
                loc_data['brief_description'],
                loc_data['long_description'],
                loc_data['available_commands'],
                loc_data['items'].copy()  # Create a copy to avoid modifying the original
            )
            locations[loc_data['id']] = location_obj

        items = {}
        for item_data in data['items']:
            item_obj = Item(
                item_data['name'],
                item_data['description'],
                item_data['start_position'],
                item_data['target_position'],
                item_data['target_points'],
                item_data.get('pickup_points', 0)  # Default to 0 if not specified
            )
            items[item_data['name']] = item_obj

        return locations, items

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.

        >>> game = AdventureGame('game_data.json', 1)
        >>> loc = game.get_location()
        >>> loc.id_num
        1
        >>> loc2 = game.get_location(2)
        >>> loc2.id_num
        2

        Preconditions:
            - loc_id is None or loc_id in self._locations
        """
        if loc_id is None:
            return self._locations[self.current_location_id]
        else:
            return self._locations[loc_id]

    def get_item(self, item_name: str) -> Optional[Item]:
        """Return the Item object with the given name, or None if no such item exists.
        Item name comparison is case-insensitive.

        >>> game = AdventureGame('game_data.json', 1)
        >>> item = game.get_item("USB Drive")
        >>> item.name
        'USB Drive'
        >>> item = game.get_item("usb drive")
        >>> item.name
        'USB Drive'
        >>> game.get_item("Nonexistent Item") is None
        True
        """
        for name, item in self._items.items():
            if name.lower() == item_name.lower():
                return item
        return None

    def handle_go_command(self, direction: str) -> bool:
        """Handle a 'go [direction]' command. Return True if the move was successful, False otherwise.
        If successful, update the current location and increment the player's move count.

        >>> game = AdventureGame('game_data.json', 1)
        >>> initial_moves = game.player.moves_made
        >>> game.handle_go_command('north')
        True
        >>> game.current_location_id
        2
        >>> game.player.moves_made == initial_moves + 1
        True
        >>> game.handle_go_command('south')
        True
        >>> game.current_location_id
        1

        Preconditions:
            - direction in ['north', 'south', 'east', 'west']
        """
        location = self.get_location()
        command = f"go {direction}"

        if command in location.available_commands:
            result = location.available_commands[command]
            if isinstance(result, int):
                self.current_location_id = result
                self.player.increment_moves()
                return True
            else:
                print("You can't go that way right now.")
                return False
        else:
            print(f"You can't go {direction} from here.")
            return False

    def handle_look_command(self) -> None:
        """Handle the 'look' command by displaying the full description of the current location."""
        location = self.get_location()
        print(location.long_description)
        self._display_location_items(location)

    def handle_inventory_command(self) -> None:
        """Handle the 'inventory' command by displaying all items in the player's inventory."""
        if len(self.player.inventory) == 0:
            print("Your inventory is empty.")
        else:
            print("\n=== YOUR INVENTORY ===")
            for item in self.player.inventory:
                print(f"- {item.name}")
            print("======================\n")

    def handle_score_command(self) -> None:
        """Handle the 'score' command by displaying the player's current score and moves."""
        print(f"\n=== SCORE ===")
        print(f"Current Score: {self.player.score}")
        print(f"Moves Made: {self.player.moves_made}/{MAX_MOVES}")
        print("=============\n")

    def handle_take_command(self, item_name: str) -> None:
        """Handle taking an item from the current location.

        >>> game = AdventureGame('game_data.json', 1)
        >>> game.current_location_id = 7  # Robarts 2F with USB Drive
        >>> initial_score = game.player.score
        >>> game.handle_take_command("USB Drive")
        You picked up the USB Drive.
        You gained 5 points!
        >>> game.player.has_item("USB Drive")
        True
        >>> game.player.score > initial_score
        True
        >>> "USB Drive" in game.get_location().items
        False

        Preconditions:
            - item_name is not the empty string
        """
        location = self.get_location()
        item = self.get_item(item_name)

        if item is None:
            print(f"There is no '{item_name}' here.")
            return

        if item.name not in location.items:
            print(f"There is no '{item_name}' here.")
            return

        # Remove item from location and add to inventory
        location.items.remove(item.name)
        item.current_position = -1  # -1 indicates it's in the player's inventory
        self.player.add_item(item)
        self.player.add_score(item.pickup_points)

        print(f"You picked up the {item.name}.")
        if item.pickup_points > 0:
            print(f"You gained {item.pickup_points} points!")

    def handle_drop_command(self, item_name: str) -> None:
        """Handle dropping an item at the current location.

        >>> game = AdventureGame('game_data.json', 1)
        >>> game.current_location_id = 7
        >>> game.handle_take_command("USB Drive")
        You picked up the USB Drive.
        You gained 5 points!
        >>> game.current_location_id = 1
        >>> initial_score = game.player.score
        >>> game.handle_drop_command("USB Drive")
        You dropped the USB Drive.
        This is where it belongs! You gained 20 points!
        >>> game.player.has_item("USB Drive")
        False
        >>> "USB Drive" in game.get_location().items
        True
        >>> game.player.score == initial_score + 20
        True

        Preconditions:
            - item_name is not the empty string
        """
        item = self.player.remove_item(item_name)

        if item is None:
            print(f"You don't have a '{item_name}' in your inventory.")
            return

        location = self.get_location()
        location.items.append(item.name)
        item.current_position = self.current_location_id

        # Check if item was dropped at its target location
        if self.current_location_id == item.target_position:
            self.player.add_score(item.target_points)
            print(f"You dropped the {item.name}.")
            print(f"This is where it belongs! You gained {item.target_points} points!")
        else:
            print(f"You dropped the {item.name}.")

    def handle_examine_command(self, item_name: str) -> None:
        """Handle examining an item (either in inventory or at current location).
        This is an enhancement feature that provides detailed information about items.

        Preconditions:
            - item_name is not the empty string
        """
        item = self.get_item(item_name)

        if item is None:
            print(f"There is no '{item_name}' to examine.")
            return

        location = self.get_location()

        # Check if item is in inventory or at current location
        if self.player.has_item(item_name) or item.name in location.items:
            print(f"\n=== {item.name.upper()} ===")
            print(item.description)
            print("=" * (len(item.name) + 8) + "\n")
        else:
            print(f"There is no '{item_name}' here to examine.")

    def handle_talk_to_friend(self) -> None:
        """Handle the puzzle: talking to the friend in the common room.
        This gives the player permission to enter the lecture hall.
        """
        if self.current_location_id == 3:  # Common room
            if not self.player.has_friend_permission:
                print("\nYour friend looks up from their book.")
                print("Friend: 'Hey! Shouldn't you be finishing our project? The deadline is at 1pm!'")
                print("You: 'I know, I know! I just woke up and realized I'm missing some important stuff.'")
                print("You: 'My USB drive, laptop charger, and lucky mug - I can't remember where I left them!'")
                print("Friend: 'Oh no! Well, you better find them fast. By the way, I saw you in BA3200 yesterday.'")
                print("Friend: 'Here, take my student card - the door might be locked. Good luck!'")
                print("\nYour friend hands you their student card.")
                print("You gained permission to enter locked rooms!")

                self.player.has_friend_permission = True
                self.player.add_score(10)
                print("You gained 10 points for solving the puzzle!")
            else:
                print("\nYour friend smiles encouragingly.")
                print("Friend: 'Did you find everything? Hurry back and submit that project!'")
        else:
            print("There's no one to talk to here.")

    def handle_puzzle_check(self) -> bool:
        """Handle attempting to enter the lecture hall (requires friend's permission).
        Return True if the player can enter, False otherwise.

        >>> game = AdventureGame('game_data.json', 1)
        >>> game.current_location_id = 11
        >>> game.handle_puzzle_check()
        <BLANKLINE>
        The lecture hall door is locked. You need permission to enter.
        Maybe your friend in the common room can help?
        False
        >>> game.player.has_friend_permission = True
        >>> game.handle_puzzle_check()
        You use your friend's student card to unlock the door.
        True
        >>> game.current_location_id
        12
        """
        if self.current_location_id == 11:  # Outside BA3200
            if self.player.has_friend_permission:
                print("You use your friend's student card to unlock the door.")
                self.current_location_id = 12
                self.player.increment_moves()
                return True
            else:
                print("\nThe lecture hall door is locked. You need permission to enter.")
                print("Maybe your friend in the common room can help?")
                return False
        return False

    def check_win_condition(self) -> bool:
        """Check if the player has won the game.
        The player wins if they have brought all required items back to their dorm room.

        >>> game = AdventureGame('game_data.json', 1)
        >>> game.check_win_condition()
        False
        >>> # Add all required items to dorm room (location 1)
        >>> game.get_location(1).items.extend(["USB Drive", "Laptop Charger", "Lucky Mug"])
        >>> game.check_win_condition()
        True
        """
        if self.current_location_id != 1:  # Not in dorm room
            return False

        location = self.get_location()

        # Check if all required items are at the dorm room
        for item_name in REQUIRED_ITEMS:
            if item_name not in location.items:
                return False

        return True

    def check_lose_condition(self) -> bool:
        """Check if the player has lost the game.
        The player loses if they have used up all their moves without winning.

        >>> game = AdventureGame('game_data.json', 1)
        >>> game.check_lose_condition()
        False
        >>> game.player.moves_made = 35
        >>> game.check_lose_condition()
        True
        >>> game.player.moves_made = 40
        >>> game.check_lose_condition()
        True
        """
        return self.player.moves_made >= MAX_MOVES

    def display_game_over(self, won: bool) -> None:
        """Display the appropriate game over message based on whether the player won or lost."""
        print("\n" + "=" * 60)
        if won:
            print("CONGRATULATIONS! YOU WON!")
            print("=" * 60)
            print("\nYou made it back to your dorm room with all your missing items!")
            print("You quickly fix the PythonTA errors, proofread your report,")
            print("and submit your project with 10 minutes to spare.")
            print("\nYour friend texts you: 'Nice work! We make a great team! 🎉'")
            print(f"\nFinal Score: {self.player.score}")
            print(f"Moves Used: {self.player.moves_made}/{MAX_MOVES}")
        else:
            print("GAME OVER - YOU LOST!")
            print("=" * 60)
            print("\nYou ran out of time! It's now 1pm and the deadline has passed.")
            print("You didn't make it back to your dorm in time to submit the project.")
            print("\nYour friend texts you: 'What happened?? 😰'")
            print(f"\nFinal Score: {self.player.score}")
            print(f"Moves Used: {self.player.moves_made}/{MAX_MOVES}")
        print("=" * 60 + "\n")

    def _display_location_items(self, location: Location) -> None:
        """Display all items present at the given location."""
        if len(location.items) > 0:
            print("\nYou can see the following items here:")
            for item_name in location.items:
                print(f"- {item_name}")


def play_game() -> None:
    """Main function to play the adventure game."""
    print("=" * 60)
    print("WELCOME TO: THE MISSING ITEMS ADVENTURE")
    print("A U of T Text Adventure Game")
    print("=" * 60)
    print("\nYou and your friend spent yesterday finishing your CS project.")
    print("The deadline is at 1pm today, but you fell asleep and now you're")
    print("missing some crucial items: your USB drive (with the only copy"),
    print("of your game code!), your laptop charger (battery at 5%!),")
    print("and your lucky U of T mug (you can't submit without it!).")
    print("\nCan you find everything and make it back in time?")
    print("\nType 'help' at any time to see available commands.")
    print("=" * 60 + "\n")

    game = AdventureGame('game_data.json', 1)
    menu = ["look", "inventory", "score", "log", "quit", "help"]

    # Add first event
    location = game.get_location()
    game.event_list.add_event(Event(location.id_num, location.long_description))

    # Display initial location
    print(location.long_description)
    game._display_location_items(location)

    while game.ongoing:
        location = game.get_location()

        # Mark location as visited
        if not location.visited:
            location.visited = True

        # Display available actions
        print("\n" + "-" * 60)
        print("Available commands: look, inventory, score, log, quit, help")
        print("At this location, you can also:")
        for action in location.available_commands:
            print(f"  - {action}")

        # Check for take/examine commands for items at this location
        for item_name in location.items:
            print(f"  - take {item_name}")
            print(f"  - examine {item_name}")

        # Check for drop/examine commands for items in inventory
        for item in game.player.inventory:
            print(f"  - drop {item.name}")
            if item.name not in location.items:  # Don't show examine twice
                print(f"  - examine {item.name}")

        # Get player input
        choice = input("\nWhat do you do? ").lower().strip()

        # Validate that it's a non-empty choice
        while choice == "":
            choice = input("Please enter a command: ").lower().strip()

        print("\n" + "=" * 60)

        # Handle the command
        command_handled = False

        # Menu commands
        if choice == "look":
            game.handle_look_command()
            command_handled = True
        elif choice == "inventory":
            game.handle_inventory_command()
            command_handled = True
        elif choice == "score":
            game.handle_score_command()
            command_handled = True
        elif choice == "log":
            game.event_list.display_events()
            command_handled = True
        elif choice == "help":
            print("\n=== HELP ===")
            print("Goal: Find your USB drive, laptop charger, and lucky mug,")
            print("      then return to your dorm room before time runs out!")
            print("\nBasic Commands:")
            print("  - go [direction]: Move in a direction (north, south, east, west)")
            print("  - look: See the full description of your current location")
            print("  - inventory: Check what items you're carrying")
            print("  - take [item]: Pick up an item")
            print("  - drop [item]: Drop an item at your current location")
            print("  - examine [item]: Get detailed information about an item")
            print("  - score: Check your current score and moves")
            print("  - log: See all the locations you've visited")
            print("  - quit: Exit the game")
            print("\nOther commands may be available at specific locations!")
            print("============\n")
            command_handled = True
        elif choice == "quit":
            print("Thanks for playing! Goodbye.")
            game.ongoing = False
            command_handled = True

        # Movement commands
        elif choice.startswith("go "):
            direction = choice[3:].strip()
            if direction in ["north", "south", "east", "west"]:
                success = game.handle_go_command(direction)
                if success:
                    location = game.get_location()
                    game.event_list.add_event(Event(location.id_num, location.long_description), choice)

                    # Display location description
                    if location.visited:
                        print(location.brief_description)
                    else:
                        print(location.long_description)

                    game._display_location_items(location)
                command_handled = True
            else:
                print("Invalid direction. Use: north, south, east, or west.")
                command_handled = True

        # Take command
        elif choice.startswith("take "):
            item_name = choice[5:].strip()
            game.handle_take_command(item_name)
            command_handled = True

        # Drop command
        elif choice.startswith("drop "):
            item_name = choice[5:].strip()
            game.handle_drop_command(item_name)
            command_handled = True

        # Examine command (enhancement feature)
        elif choice.startswith("examine "):
            item_name = choice[8:].strip()
            game.handle_examine_command(item_name)
            command_handled = True

        # Special location commands
        elif choice == "talk to friend":
            if "talk to friend" in location.available_commands:
                game.handle_talk_to_friend()
                command_handled = True
            else:
                print("You can't do that here.")
                command_handled = True

        # Handle puzzle check for entering lecture hall
        if not command_handled and choice == "go north" and game.current_location_id == 11:
            success = game.handle_puzzle_check()
            if success:
                location = game.get_location()
                game.event_list.add_event(Event(location.id_num, location.long_description), choice)
                print(location.long_description)
                game._display_location_items(location)
            command_handled = True

        # If command still not handled
        if not command_handled:
            print("Invalid command. Type 'help' to see available commands.")

        # Check win/lose conditions
        if game.ongoing:
            if game.check_win_condition():
                game.display_game_over(won=True)
                game.ongoing = False
            elif game.check_lose_condition():
                game.display_game_over(won=False)
                game.ongoing = False


if __name__ == "__main__":
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    })

    play_game()
