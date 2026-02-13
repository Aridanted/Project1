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

# Game Constants
BASE_MAX_MOVES = 28  # Only GO commands count as moves
REQUIRED_ITEMS = ["USB Drive", "Laptop Charger", "Lucky Mug"]
SERVER_ROOM_ID = 9  # Location ID of the server room
COFFEE_BONUS_MOVES = 5  # Extra moves from drinking coffee
MAX_SCORE = 230
RITUAL_LOCATION_ID = 10   # King's College Circle
RITUAL_ITEMS = ["USB Drive", "Laptop Charger", "Lucky Mug"]
DORM_LOCATION_ID = 0      # Win condition: bring items back here


from dataclasses import dataclass, field


@dataclass
class GameState:
    """Stores mutable game-progress state for AdventureGame.

    Instance Attributes:
        - server_room_unlocked: Whether the Bahen server room has been unlocked
        - coffee_consumed: Whether the player has drunk the coffee
        - puzzle_code: The correct 4-digit code for the Bahen keypad
        - game_stage: Current story stage for dynamic messages
        - items_collected: Set of item names the player has picked up
        - ritual_complete: Whether the summoning ritual has been performed

    Representation Invariants:
        - self.game_stage in ['start', 'exploring', 'gathering', 'ready_ritual', 'ritual_done', 'winning']
    """
    server_room_unlocked: bool = False
    coffee_consumed: bool = False
    puzzle_code: str = '1827'
    game_stage: str = 'start'
    items_collected: set = field(default_factory=set)
    ritual_complete: bool = False


class AdventureGame:
    """Text adventure game with advanced puzzle mechanics.

    Instance Attributes:
        - current_location_id: Current location ID
        - ongoing: Whether game is still running
        - player: The Player object tracking inventory, score, and moves
        - max_moves: Maximum allowed moves (can increase with coffee)
        - _state: Bundled mutable game-progress state (see GameState)

    Representation Invariants:
        - self.current_location_id in self._locations
        - self.max_moves >= BASE_MAX_MOVES
    """

    # Private Instance Attributes (do NOT remove these two attributes):
    #   - _locations: a mapping from location id to Location object.
    #                       This represents all the locations in the game.
    #   - _items: a list of Item objects, representing all items in the game.

    _locations: dict[int, Location]
    _items: list[Item]
    current_location_id: int
    ongoing: bool
    player: Player
    max_moves: int
    _state: GameState

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """
        Initialize a new text adventure game, based on the data in the given file, setting starting location of game
        at the given initial location ID.
        (note: you are allowed to modify the format of the file as you see fit)

        Preconditions:
        - game_data_file is the filename of a valid game data JSON file
        - initial_location_id is a valid location ID in the game data
        """
        self._locations, self._items, puzzle_code = self._load_game_data(game_data_file)
        self.current_location_id = initial_location_id  # game begins at this location
        self.ongoing = True     # whether the game is ongoing
        self.player = Player([], 0, 0, False)
        self.max_moves = BASE_MAX_MOVES
        self._state = GameState(puzzle_code=puzzle_code)

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], list[Item], str]:
        """Load locations and items from a JSON file with the given filename and
        return a tuple consisting of (1) a dictionary of locations mapping each game location's ID to a Location object,
        and (2) a list of all Item objects."""

        with open(filename, 'r') as f:
            data = json.load(f)  # This loads all the data from the JSON file

        locations = {}
        for loc_data in data['locations']:  # Go through each element associated with the 'locations' key in the file
            location_obj = Location(
                loc_data['id'],
                loc_data['brief_description'],
                loc_data['long_description'],
                loc_data['available_commands'],
                loc_data['items'].copy()
            )
            locations[loc_data['id']] = location_obj
        items = []
        for item_data in data['items']:
            item_obj = Item(
                item_data['name'],
                item_data['description'],
                item_data['start_position'],
                item_data['target_position'],
                item_data['target_points'],
                item_data.get('pickup_points', 0)
            )
            items.append(item_obj)

        puzzle_code = data.get('puzzle_code', '1827')
        return locations, items, puzzle_code

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.
        Preconditions:
            - loc_id is None or loc_id in self._locations

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> loc = game1.get_location(0)
        >>> loc.id_num
        0
        >>> loc = game1.get_location()
        >>> loc.id_num
        0
        """

        if loc_id is None:
            return self._locations[self.current_location_id]
        return self._locations[loc_id]

    def get_item(self, name_of_item: str) -> Optional[Item]:
        """Get item by name (case-insensitive) or None if it doesn't exist.

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> item1 = game1.get_item('USB Drive')
        >>> item1.name
        'USB Drive'
        >>> game1.get_item('nonexistent') is None
        True
        """
        for itemm in self._items:
            if itemm.name.lower() == name_of_item.lower():
                return itemm
        return None

    # -------------------------------------------------------------------------
    # Movement
    # -------------------------------------------------------------------------

    def go_command(self, direction: str, game_logs: EventList) -> bool:
        """Handle movement. THIS IS THE ONLY COMMAND THAT COUNTS AS A MOVE!

        Updates game_logs with the new location event after a successful move.
        Returns True if the move succeeded, False otherwise.
        Preconditions:
            - direction is a non-empty string

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> log = EventList()
        >>> game1.go_command('east', log)
        True
        >>> game1.current_location_id
        1
        >>> game1.player.moves_made
        1
        >>> game1.go_command('south', log)
        You can't go south from here.
        False
        >>> game1.player.moves_made
        1
        """
        command = f"go {direction}"
        location_now = self.get_location()

        if command in location_now.available_commands:
            result_id = location_now.available_commands[command]
            if isinstance(result_id, int):
                self.current_location_id = result_id
                self.player.increment_moves()
                new_location = self.get_location()
                game_logs.add_event(Event(new_location.id_num, new_location.long_description), command)
                self.check_stage_messages()
                return True

        print(f"You can't go {direction} from here.")
        return False

    def look_command(self) -> None:
        """Print the full long description of the current location plus items present.

        Does NOT count as a move.
        """
        location_now = self.get_location()
        print(location_now.long_description)
        self.print_location_items(location_now)

    def inventory_command(self) -> None:
        """Print the player's current inventory.

        Does NOT count as a move.

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> game1.inventory_command()
        Your inventory is empty.
        """
        if not self.player.inventory:
            print("Your inventory is empty.")
        else:
            print("\n=== INVENTORY ===")
            for item_inv in self.player.inventory:
                print(f"  - {item_inv.name}")
            print("=================\n")

    def score_command(self) -> None:
        """Print the player's current score as X/MAX (percentage), plus move count.

        Does NOT count as a move.

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> game1.score_command()
        ============================================================
        GAME STATUS
        ============================================================
        Score : 0 / 230 (0.0%)
        Moves : 0 / 28
        Sacred Items : 0 / 3
        ============================================================
        <BLANKLINE>
        """
        pct = (self.player.score / MAX_SCORE) * 100
        required = {"USB Drive", "Laptop Charger", "Lucky Mug"}
        collected = len(required.intersection(self._state.items_collected))

        print("=" * 60)
        print("GAME STATUS")
        print("=" * 60)
        print(f"Score : {self.player.score} / {MAX_SCORE} ({pct:.1f}%)")
        print(f"Moves : {self.player.moves_made} / {self.max_moves}")
        print(f"Sacred Items : {collected} / 3")
        if self._state.coffee_consumed:
            print("Status: ENERGIZED (coffee bonus active!)")
        if self._state.ritual_complete:
            print("Ritual: COMPLETE - backup USB acquired!")
        print("=" * 60 + "\n")

    def take_command(self, taking_item_name: str) -> None:
        """Pick up the named item from the current location into the player's inventory.

        Awards pickup points and prints contextual story messages for sacred items.
        Does NOT count as a move.

        Preconditions:
            - taking_item_name is a non-empty string

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> game1.current_location_id = 1
        >>> game1.take_command('coffee')
        You picked up the coffee.
        You drink the coffee. Ahh, that double-double hits the spot!
        ENERGIZED! +5 bonus moves added to your limit. (28 -> 33)
        """
        location1 = self.get_location()
        itemm = self.get_item(taking_item_name)

        # Find the item at the location (case-insensitive)
        matched_name = None
        for name in location1.items:
            if name.lower() == taking_item_name.lower():
                matched_name = name
                break

        if itemm is None or matched_name is None:
            print(f"There is no '{taking_item_name}' here.")
            return

        location1.items.remove(matched_name)
        itemm.current_position = -1
        self.player.add_item(itemm)
        self.player.add_score(itemm.pickup_points)
        self._state.items_collected.add(itemm.name)

        print(f"You picked up the {itemm.name}.")
        if itemm.pickup_points > 0:
            print(f"+{itemm.pickup_points} points!")

        # Sacred item story messages
        required = {"USB Drive", "Laptop Charger", "Lucky Mug"}
        if itemm.name == "USB Drive":
            print("\nThe BLUE GUARDIAN acquired!")
            print("Strangely, it's dated 2 days ago - before you fixed that bug...")
        elif itemm.name == "Laptop Charger":
            print("\nThe SILVER CONDUCTOR acquired!")
            print("Sticky note: 'Borrowed to debug your code all night. - Partner'")
        elif itemm.name == "Lucky Mug":
            print("\nThe GOLDEN VESSEL acquired!")
            print("Receipt inside: 3:47 AM. Your partner was up ALL night.")

        # Progress feedback for sacred items
        if itemm.name in required:
            remaining = required - self._state.items_collected
            if remaining:
                print(f"Still need: {', '.join(remaining)}")
            else:
                print("\n" + "=" * 60)
                print("ALL THREE SACRED ITEMS COLLECTED!")
                print("Head to KING'S COLLEGE CIRCLE to perform the ritual!")
                print("=" * 60)

        # Coffee is consumed immediately on pickup
        if itemm.name.lower() == "coffee":
            self._consume_coffee()

    def drop_command(self, item__name: str) -> None:
        """Drop the named item from the player's inventory to the current location.

        Awards target_points if the item is dropped at its target location.
        If all three sacred items are dropped at King's College Circle (id 10),
        triggers the summoning ritual automatically.
        Does NOT count as a move.

        Preconditions:
            - item__name is a non-empty string

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> game1.drop_command('USB Drive')
        You don't have 'USB Drive'.
        """
        itemm = self.player.remove_item(item__name)
        if itemm is None:
            print(f"You don't have '{item__name}'.")
            return

        locationn = self.get_location()
        locationn.items.append(itemm.name)
        itemm.current_position = self.current_location_id
        print(f"You place the {itemm.name} on the ground.")

        # Award target points for depositing at correct location
        if self.current_location_id == itemm.target_position and itemm.target_points > 0:
            self.player.add_score(itemm.target_points)
            print(f"+{itemm.target_points} points! Deposited at the right place!")

        # Check ritual trigger at King's College Circle
        if self.current_location_id == RITUAL_LOCATION_ID:
            self._check_ritual(locationn)

    def examine_command(self, item__name: str) -> None:
        """Print the description of the named item (in inventory or at current location).

        Does NOT count as a move.

        Preconditions:
            - item__name is a non-empty string

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> game1.current_location_id = 6
        >>> game1.examine_command('USB Drive')
        USB Drive:
        BLUE USB drive with U of T sticker. The BLUE GUARDIAN. Contains your project code, but your partner mentioned a bug...
        """
        itemm = self.get_item(item__name)
        locationn = self.get_location()

        in_inventory = self.player.has_item(item__name)
        at_location = any(n.lower() == item__name.lower() for n in locationn.items)

        if itemm is None or (not in_inventory and not at_location):
            print(f"You can't see '{item__name}' here.")
            return

        print(f"{itemm.name}:")
        print(itemm.description)

    # -------------------------------------------------------------------------
    # Puzzle commands (free - no move cost)
    # -------------------------------------------------------------------------

    def enter_code_command(self) -> None:
        """Attempt to enter the keypad code at the Bahen server room door.

        Prompts the player for input. Correct code (1827) unlocks the server room
        and awards 20 points. Wrong code gives a hint.
        Does NOT count as a move.
        """
        if self.current_location_id != 7:
            print("There's no keypad here.")
            return
        if self._state.server_room_unlocked:
            print("The server room is already unlocked. Go SOUTH to enter.")
            return

        print("\nThe keypad shows: [_][_][_][_]")
        print("Clue on the wall: 'When UofT was born, so was the code.'")
        print("Enter 4-digit code (or type 'cancel'):")
        code = input("> ").strip()

        if code.lower() == 'cancel':
            print("You step back from the keypad.")
            return

        if code == self._state.puzzle_code:
            print("\n" + "=" * 60)
            print("*BEEP* -- ACCESS GRANTED")
            print("=" * 60)
            print("\nThe door clicks open. You hear servers humming inside.")
            print("The server room holds something important...")
            print("\nPUZZLE SOLVED! +20 points!")
            print("=" * 60 + "\n")
            self._state.server_room_unlocked = True
            self._locations[7].available_commands["go south"] = 12
            self.player.add_score(20)
        else:
            print("\n*BUZZ* -- ACCESS DENIED")
            print(f"Incorrect code: '{code}'")
            print("Hint: University of Toronto was founded in 1827.")
            print("      Look for clues in the game world...\n")

    def read_note_command(self) -> None:
        """Read the note item if the player is carrying it or it is at the current location.

        Does NOT count as a move.
        """
        note = self.get_item("note")
        locationn = self.get_location()
        if note is None:
            print("There is no note to read.")
            return
        if not self.player.has_item("note") and "note" not in locationn.items:
            print("You don't have a note to read.")
            return
        print("\nThe note reads:")
        print("  'The bug is in the file handler. I fixed it.'")
        print("  'Code: founding year of UofT. Get the backup from the server room.'")
        print("  'Submit MINE, not yours. We will make it. - Partner'\n")

    # -------------------------------------------------------------------------
    # Win / Lose
    # -------------------------------------------------------------------------

    def check_win(self) -> bool:
        """Return True if the player has won (backup_usb deposited at dorm).

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> game1.check_win()
        False
        """
        if self.current_location_id != DORM_LOCATION_ID:
            return False
        return "backup_usb" in self.get_location().items

    def check_lose(self) -> bool:
        """Return True if the player has exceeded their move limit.

        >>> game1 = AdventureGame('game_data.json', 0)
        >>> game1.check_lose()
        False
        """
        return self.player.moves_made >= self.max_moves

    def display_win(self) -> None:
        """Print the win screen."""
        print("\n" + "=" * 60)
        print("  YOU WON! MYSTERY SOLVED!")
        print("=" * 60)
        print("\nYou rush to your laptop and submit the FIXED project!")
        print("12:57pm - three minutes to spare!")
        print("\nYour partner appears at the door:")
        print("  'They were trying to sabotage us. I had to hide everything")
        print("   and leave clues only you would understand. The ritual")
        print("   was to get you the fixed version safely.'")
        print("\n  'We're a team. Always.'")
        print("\nProject submitted. You both pass with flying colours!")
        print("=" * 60)
        print(f"FINAL SCORE : {self.player.score} / {MAX_SCORE}"
              f" ({(self.player.score / MAX_SCORE) * 100:.1f}%)")
        print(f"MOVES USED  : {self.player.moves_made} / {self.max_moves}")
        print("=" * 60 + "\n")

    def display_lose(self) -> None:
        """Print the lose screen."""
        print("\n" + "=" * 60)
        print("  TIME'S UP! GAME OVER")
        print("=" * 60)
        print("\n1:00pm. The submission window has closed.")
        print("Your laptop shows: 'Submission deadline passed.'")
        print("\nYour partner texts: 'I tried to help... I'm so sorry.'")
        print("The mystery remains unsolved.")
        print("=" * 60)
        print(f"FINAL SCORE : {self.player.score} / {MAX_SCORE}"
              f" ({(self.player.score / MAX_SCORE) * 100:.1f}%)")
        print(f"MOVES USED  : {self.player.moves_made} / {self.max_moves}")
        print("=" * 60 + "\n")

    def check_stage_messages(self) -> None:
        """Display context-sensitive messages based on current stage and location."""
        required = {"USB Drive", "Laptop Charger", "Lucky Mug"}
        collected = required.intersection(self._state.items_collected)

        # Advance the stage
        if self._state.game_stage == 'start' and collected:
            self._state.game_stage = 'exploring'
        if self._state.game_stage == 'exploring' and len(collected) >= 2:
            self._state.game_stage = 'gathering'
        if len(collected) == 3 and not self._state.ritual_complete:
            self._state.game_stage = 'ready_ritual'

        loc = self.current_location_id

        # King's College Circle - messages change each stage
        if loc == RITUAL_LOCATION_ID:
            if self._state.game_stage in ('start', 'exploring'):
                print("\n--- The founding circle feels alive. Something is waiting. ---\n")
            elif self._state.game_stage == 'gathering':
                n = len(collected)
                print(f"\n--- The circle pulses. You have {n}/3 sacred items. ---\n")
            elif self._state.game_stage == 'ready_ritual':
                print("\n" + "=" * 60)
                print("  THE TIME HAS COME")
                print("=" * 60)
                print("You have all three sacred items.")
                print("The chalk triangle glows with anticipation.\n")
                print("RITUAL INSTRUCTIONS:")
                print("  - drop USB Drive       (Blue Guardian)")
                print("  - drop Laptop Charger  (Silver Conductor)")
                print("  - drop Lucky Mug       (Golden Vessel)")
                print("\nWhen all three rest in the circle, truth shall manifest!")
                print("=" * 60 + "\n")
            elif self._state.game_stage == 'ritual_done':
                print("\n--- The circle is quiet now. Its work is done. ---\n")

        # Gerstein Library - partner messages
        if loc == 11:
            if self._state.game_stage == 'ready_ritual':
                print("\n--- Your partner at the window holds a sign: ---")
                print("    'DROP THE THREE IN THE CIRCLE -> TRUTH APPEARS'")
                print("    They give you a thumbs-up.\n")
            elif self._state.game_stage == 'ritual_done':
                print("\n--- Partner's sign: 'TAKE IT HOME AND SUBMIT! WE DID IT!' ---\n")

        # Server room - story revelation (only first time)
        if loc == 12 and self._state.server_room_unlocked:
            print("\n--- DOCUMENT ON THE DESK ---")
            print("Email: 'Deadline extended to 2pm - server maintenance.'")
            print("Partner's note: 'Found a critical bug. Fixed it overnight.")
            print("  The ritual will summon the corrected version. Submit THAT.'")
            print("  They were protecting you the whole time.\n")

    def print_location_items(self, locationn: Location) -> None:
        """Print items present at the given location, if any."""
        if locationn.items:
            print("\nItems here:")
            for item__name in locationn.items:
                print(f"  - {item__name}")

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _consume_coffee(self) -> None:
        """Handle coffee consumption: extend move limit and remove from inventory."""
        if self._state.coffee_consumed:
            return
        self._state.coffee_consumed = True
        self.player.remove_item("coffee")
        self.max_moves += COFFEE_BONUS_MOVES
        print("You drink the coffee. Ahh, that double-double hits the spot!")
        print(f"ENERGIZED! +{COFFEE_BONUS_MOVES} bonus moves added to your limit."
              f" ({self.max_moves - COFFEE_BONUS_MOVES} -> {self.max_moves})")

    def _check_ritual(self, locationn: Location) -> None:
        """Check whether all three sacred items are present at the ritual location.
        If so, perform the summoning ritual: items dissolve, backup_usb materialises.
        """
        if self._state.ritual_complete:
            return
        if not all(name_r in locationn.items for name_r in RITUAL_ITEMS):
            remaining = [n for n in RITUAL_ITEMS if n not in locationn.items]
            print(f"  (The circle waits... still need: {', '.join(remaining)})")
            return

        self._state.ritual_complete = True
        self._state.game_stage = 'ritual_done'

        print("\n" + "=" * 70)
        print(" " * 22 + "THE RITUAL BEGINS")
        print("=" * 70)
        print("\nThe three items glow with ethereal light!")
        print("\n  [USB Drive] glows BLUE...")
        print("  [Laptop Charger] glows SILVER...")
        print("  [Lucky Mug] glows GOLD...")
        print("\nThey rise, orbit each other, form a perfect triangle!")
        print("Energy crackles between them. The chalk marks ignite!")
        print("\n** BLINDING FLASH **")
        print("\nWhen your vision clears...")
        print("\n  A new USB drive materialises in the centre of the circle.")
        print("  Labelled: 'FIXED VERSION - SUBMIT THIS ONE'")
        print("\nThe three original items dissolve into particles of light,")
        print("their essence absorbed into the new drive.")
        print("\nYour partner's voice echoes from across campus:")
        print("  'The bug is gone. Take that drive home and submit it!'")
        print("\n+50 POINTS! Ritual complete!")
        print("=" * 70 + "\n")

        # Remove the three original items and spawn backup_usb
        for name in RITUAL_ITEMS:
            if name in locationn.items:
                locationn.items.remove(name)

        backup = self.get_item("backup_usb")
        if backup is not None:
            backup.current_position = RITUAL_LOCATION_ID
            locationn.items.append("backup_usb")
            self.player.add_score(50)

# -------------------------------------------------------------------------
# Command display helper (used in the main loop)
# -------------------------------------------------------------------------


def _print_available_actions(locationn: Location, player: Player, server_room_unlocked: bool) -> None:
    """Print all valid commands the player can currently use, without duplicates."""
    print("\nWhat to do? Choose from: look, inventory, score, log, quit")
    print("At this location, you can also:")

    # Movement commands from JSON (all values are ints now)
    for actionn in locationn.available_commands:
        print(f"  - {actionn}")

    # Puzzle command at Bahen (loc 7) only
    if locationn.id_num == 7 and not server_room_unlocked:
        print("  - enter code")

    # Items at locationn: take / examine (no duplicates)
    shown = set()
    for name in locationn.items:
        key = name.lower()
        if key not in shown:
            print(f"  - take {name}")
            print(f"  - examine {name}")
            shown.add(key)

    # Items in inventory: drop / examine
    for itemm in player.inventory:
        key = itemm.name.lower()
        print(f"  - drop {itemm.name}")
        if key not in shown:
            print(f"  - examine {itemm.name}")
            shown.add(key)


if __name__ == "__main__":
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    })

    game_log = EventList()
    game = AdventureGame('game_data.json', 0)  # load data, setting initial location ID to 0
    menu = ["look", "inventory", "score", "log", "quit"]  # Regular menu options available at each location
    choice = None

    while game.ongoing:
        location = game.get_location()
        commands = dict(location.available_commands)
        for item_name in location.items:
            low = item_name.lower()
            commands[f"take {low}"] = f"action:take:{item_name}"
            commands[f"examine {low}"] = f"action:examine:{item_name}"
        for item in game.player.inventory:
            low = item.name.lower()
            commands[f"drop {low}"] = f"action:drop:{item.name}"
            commands[f"examine {low}"] = f"action:examine:{item.name}"

        commands["read note"] = "action:read_note"
        if location.id_num == 7 and not game._state.server_room_unlocked:
            commands["enter code"] = "action:keypad"
        new_loc = game.get_location()
        if not new_loc.visited:
            print(new_loc.long_description)
            new_loc.visited = True
        else:
            print(new_loc.brief_description)
        game.print_location_items(new_loc)

        # Display possible actions at this location
        print("What to do? Choose from: look, inventory, score, log, quit")
        print("At this location, you can also:")
        for action in commands:
            print("-", action)

        # Validate choice
        choice = input("\nEnter action: ").lower().strip()
        while choice not in commands and choice not in menu:
            print("That was an invalid option; try again.")
            choice = input("\nEnter action: ").lower().strip()

        print("========")
        print("You decided to:", choice)

        if choice in menu:
            if choice == "log":
                game_log.display_events()
            elif choice == "look":
                game.look_command()
            elif choice == "inventory":
                game.inventory_command()
            elif choice == "score":
                game.score_command()
            elif choice == "quit":
                print("Thanks for playing!")
                game.ongoing = False

        else:
            # Handle non-menu actions
            result = commands[choice]

            # Movement: only count moves if the command is actually "go ..."
            parts = choice.split(maxsplit=1)
            verb = parts[0]

            if isinstance(result, int):
                # This is a location change command from JSON
                game.current_location_id = result
                if verb == "go":
                    game.player.increment_moves()
                    game.check_stage_messages()
            else:
                tag_parts = str(result).split(":", maxsplit=2)
                action = tag_parts[1] if len(tag_parts) >= 2 else ""
                payload = tag_parts[2] if len(tag_parts) == 3 else ""

                if action == "take":
                    game.take_command(payload)
                elif action == "drop":
                    game.drop_command(payload)
                elif action == "examine":
                    game.examine_command(payload)
                elif action == "read_note":
                    game.read_note_command()
                elif action == "keypad":
                    game.enter_code_command()

            new_loc = game.get_location()
            if not new_loc.visited:
                print(new_loc.long_description)
                new_loc.visited = True
            else:
                print(new_loc.brief_description)
            game.print_location_items(new_loc)

        if game.ongoing:
            if game.check_win():
                game.display_win()
                game.ongoing = False
            elif game.check_lose():
                game.display_lose()
                game.ongoing = False
