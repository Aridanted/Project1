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


# Game-level constants
BASE_MAX_MOVES = 28       # Only GO commands count as moves
COFFEE_BONUS_MOVES = 5    # Extra moves from drinking coffee
# Max score: 3 items x(5 pickup + 30 deposit) + ritual 50 + puzzle 20 + clue_paper 15 + backup pickup 50
MAX_SCORE = 230
RITUAL_LOCATION_ID = 10   # King's College Circle - where ritual happens
RITUAL_ITEMS = ["USB Drive", "Laptop Charger", "Lucky Mug"]  # Items needed for ritual
DORM_LOCATION_ID = 0      # Win condition: bring items back here


class AdventureGame:
    """A text adventure game class storing all location, item and map data.

    Instance Attributes:
        - current_location_id: The ID of the location the player is currently at
        - ongoing: Whether the game is still in progress
        - player: The Player object tracking inventory, score, and moves
        - max_moves: The current move limit (can increase with coffee)
        - server_room_unlocked: Whether the Bahen server room door has been unlocked
        - coffee_consumed: Whether the player has drunk the coffee
        - puzzle_code: The correct 4-digit code for the Bahen keypad
        - game_stage: Current narrative stage for dynamic messages
        - items_collected: Set of item names the player has picked up so far
        - ritual_complete: Whether the summoning ritual has been performed

    Representation Invariants:
        - self.current_location_id in self._locations
        - self.max_moves >= BASE_MAX_MOVES
        - self.game_stage in {'start', 'exploring', 'gathering', 'ready_ritual', 'ritual_done'}
    """

    # Private Instance Attributes:
    #   - _locations: a mapping from location id to Location object.
    #   - _items: a list of Item objects, representing all items in the game.
    _locations: dict[int, Location]
    _items: list[Item]

    current_location_id: int
    ongoing: bool
    player: Player
    max_moves: int
    server_room_unlocked: bool
    coffee_consumed: bool
    puzzle_code: str
    game_stage: str
    items_collected: set[str]
    ritual_complete: bool

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """Initialize a new text adventure game, based on the data in the given file,
        setting starting location of game at the given initial location ID.

        Preconditions:
            - game_data_file is the filename of a valid game data JSON file
            - initial_location_id is a valid location ID in the game data
        """
        self._locations, self._items, self.puzzle_code = self._load_game_data(game_data_file)

        self.current_location_id = initial_location_id
        self.ongoing = True
        self.player = Player()
        self.max_moves = BASE_MAX_MOVES
        self.server_room_unlocked = False
        self.coffee_consumed = False
        self.game_stage = 'start'
        self.items_collected = set()
        self.ritual_complete = False

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], list[Item], str]:
        """Load locations and items from a JSON file with the given filename.

        Return a tuple of:
          (1) a dictionary mapping each location ID to a Location object,
          (2) a list of all Item objects,
          (3) the puzzle code string.
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
        If no ID is provided, return the Location object for the current location.

        Preconditions:
            - loc_id is None or loc_id in self._locations

        >>> game = AdventureGame('game_data.json', 0)
        >>> loc = game.get_location(0)
        >>> loc.id_num
        0
        >>> loc = game.get_location()
        >>> loc.id_num
        0
        """
        if loc_id is None:
            return self._locations[self.current_location_id]
        return self._locations[loc_id]

    def get_item(self, item_name: str) -> Optional[Item]:
        """Return the Item with the given name, or None if it doesn't exist.
        Matching is case-insensitive.

        >>> game = AdventureGame('game_data.json', 0)
        >>> item = game.get_item('USB Drive')
        >>> item.name
        'USB Drive'
        >>> game.get_item('nonexistent') is None
        True
        """
        for item in self._items:
            if item.name.lower() == item_name.lower():
                return item
        return None

    # -------------------------------------------------------------------------
    # Movement
    # -------------------------------------------------------------------------

    def do_go(self, direction: str, game_log: EventList) -> bool:
        """Move the player in the given direction if possible.

        This is the ONLY action that increments the player's move counter.
        Updates game_log with the new location event after a successful move.
        Returns True if the move succeeded, False otherwise.

        Preconditions:
            - direction is a non-empty string

        >>> game = AdventureGame('game_data.json', 0)
        >>> from event_logger import EventList
        >>> log = EventList()
        >>> game.do_go('east', log)
        True
        >>> game.current_location_id
        1
        >>> game.player.moves_made
        1
        >>> game.do_go('south', log)
        You can't go south from here.
        False
        >>> game.player.moves_made
        1
        """
        command = f"go {direction}"
        location = self.get_location()

        if command in location.available_commands:
            result = location.available_commands[command]
            if isinstance(result, int):
                self.current_location_id = result
                self.player.increment_moves()
                new_loc = self.get_location()
                game_log.add_event(Event(new_loc.id_num, new_loc.long_description), command)
                self._check_stage_messages()
                return True

        print(f"You can't go {direction} from here.")
        return False

    # -------------------------------------------------------------------------
    # Menu commands (free - no move cost)
    # -------------------------------------------------------------------------

    def do_look(self) -> None:
        """Print the full long description of the current location plus items present.

        Does NOT count as a move.
        """
        location = self.get_location()
        print(location.long_description)
        self._print_location_items(location)

    def do_inventory(self) -> None:
        """Print the player's current inventory.

        Does NOT count as a move.

        >>> game = AdventureGame('game_data.json', 0)
        >>> game.do_inventory()
        Your inventory is empty.
        """
        if not self.player.inventory:
            print("Your inventory is empty.")
        else:
            print("\n=== INVENTORY ===")
            for item in self.player.inventory:
                print(f"  - {item.name}")
            print("=================\n")

    def do_score(self) -> None:
        """Print the player's current score as X/MAX (percentage), plus move count.

        Does NOT count as a move.

        >>> game = AdventureGame('game_data.json', 0)
        >>> game.do_score()  # doctest: +NORMALIZE_WHITESPACE
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
        collected = len(required.intersection(self.items_collected))

        print("=" * 60)
        print("GAME STATUS")
        print("=" * 60)
        print(f"Score : {self.player.score} / {MAX_SCORE} ({pct:.1f}%)")
        print(f"Moves : {self.player.moves_made} / {self.max_moves}")
        print(f"Sacred Items : {collected} / 3")
        if self.coffee_consumed:
            print("Status: ENERGIZED (coffee bonus active!)")
        if self.ritual_complete:
            print("Ritual: COMPLETE - backup USB acquired!")
        print("=" * 60 + "\n")

    # -------------------------------------------------------------------------
    # Item commands (free - no move cost)
    # -------------------------------------------------------------------------

    def do_take(self, item_name: str) -> None:
        """Pick up the named item from the current location into the player's inventory.

        Awards pickup points and prints contextual story messages for sacred items.
        Does NOT count as a move.

        Preconditions:
            - item_name is a non-empty string

        >>> game = AdventureGame('game_data.json', 0)
        >>> game.current_location_id = 1
        >>> game.do_take('coffee')
        You picked up the coffee.
        You drink the coffee. Ahh, that double-double hits the spot!
        ENERGIZED! +5 bonus moves added to your limit. (28 -> 33)
        """
        location = self.get_location()
        item = self.get_item(item_name)

        # Find the item at the location (case-insensitive)
        matched_name = None
        for name in location.items:
            if name.lower() == item_name.lower():
                matched_name = name
                break

        if item is None or matched_name is None:
            print(f"There is no '{item_name}' here.")
            return

        location.items.remove(matched_name)
        item.current_position = -1
        self.player.add_item(item)
        self.player.add_score(item.pickup_points)
        self.items_collected.add(item.name)

        print(f"You picked up the {item.name}.")
        if item.pickup_points > 0:
            print(f"+{item.pickup_points} points!")

        # Sacred item story messages
        required = {"USB Drive", "Laptop Charger", "Lucky Mug"}
        if item.name == "USB Drive":
            print("\nThe BLUE GUARDIAN acquired!")
            print("Strangely, it's dated 2 days ago - before you fixed that bug...")
        elif item.name == "Laptop Charger":
            print("\nThe SILVER CONDUCTOR acquired!")
            print("Sticky note: 'Borrowed to debug your code all night. - Partner'")
        elif item.name == "Lucky Mug":
            print("\nThe GOLDEN VESSEL acquired!")
            print("Receipt inside: 3:47 AM. Your partner was up ALL night.")

        # Progress feedback for sacred items
        if item.name in required:
            remaining = required - self.items_collected
            if remaining:
                print(f"Still need: {', '.join(remaining)}")
            else:
                print("\n" + "=" * 60)
                print("ALL THREE SACRED ITEMS COLLECTED!")
                print("Head to KING'S COLLEGE CIRCLE to perform the ritual!")
                print("=" * 60)

        # Coffee is consumed immediately on pickup
        if item.name.lower() == "coffee":
            self._consume_coffee()

    def do_drop(self, item_name: str) -> None:
        """Drop the named item from the player's inventory to the current location.

        Awards target_points if the item is dropped at its target location.
        If all three sacred items are dropped at King's College Circle (id 10),
        triggers the summoning ritual automatically.
        Does NOT count as a move.

        Preconditions:
            - item_name is a non-empty string

        >>> game = AdventureGame('game_data.json', 0)
        >>> game.do_drop('USB Drive')
        You don't have 'USB Drive'.
        """
        item = self.player.remove_item(item_name)
        if item is None:
            print(f"You don't have '{item_name}'.")
            return

        location = self.get_location()
        location.items.append(item.name)
        item.current_position = self.current_location_id
        print(f"You place the {item.name} on the ground.")

        # Award target points for depositing at correct location
        if self.current_location_id == item.target_position and item.target_points > 0:
            self.player.add_score(item.target_points)
            print(f"+{item.target_points} points! Deposited at the right place!")

        # Check ritual trigger at King's College Circle
        if self.current_location_id == RITUAL_LOCATION_ID:
            self._check_ritual(location)

    def do_examine(self, item_name: str) -> None:
        """Print the description of the named item (in inventory or at current location).

        Does NOT count as a move.

        Preconditions:
            - item_name is a non-empty string

        >>> game = AdventureGame('game_data.json', 0)
        >>> game.current_location_id = 6
        >>> game.do_examine('USB Drive')
        USB Drive:
        BLUE USB drive with U of T sticker. The BLUE GUARDIAN. Contains your project code, but your partner mentioned a bug...
        """
        item = self.get_item(item_name)
        location = self.get_location()

        in_inventory = self.player.has_item(item_name)
        at_location = any(n.lower() == item_name.lower() for n in location.items)

        if item is None or (not in_inventory and not at_location):
            print(f"You can't see '{item_name}' here.")
            return

        print(f"{item.name}:")
        print(item.description)

    # -------------------------------------------------------------------------
    # Puzzle commands (free - no move cost)
    # -------------------------------------------------------------------------

    def do_enter_code(self) -> None:
        """Attempt to enter the keypad code at the Bahen server room door.

        Prompts the player for input. Correct code (1827) unlocks the server room
        and awards 20 points. Wrong code gives a hint.
        Does NOT count as a move.
        """
        if self.current_location_id != 7:
            print("There's no keypad here.")
            return
        if self.server_room_unlocked:
            print("The server room is already unlocked. Go SOUTH to enter.")
            return

        print("\nThe keypad shows: [_][_][_][_]")
        print("Clue on the wall: 'When UofT was born, so was the code.'")
        print("Enter 4-digit code (or type 'cancel'):")
        code = input("> ").strip()

        if code.lower() == 'cancel':
            print("You step back from the keypad.")
            return

        if code == self.puzzle_code:
            print("\n" + "=" * 60)
            print("*BEEP* -- ACCESS GRANTED")
            print("=" * 60)
            print("\nThe door clicks open. You hear servers humming inside.")
            print("The server room holds something important...")
            print("\nPUZZLE SOLVED! +20 points!")
            print("=" * 60 + "\n")
            self.server_room_unlocked = True
            self._locations[7].available_commands["go south"] = 12
            self.player.add_score(20)
        else:
            print("\n*BUZZ* -- ACCESS DENIED")
            print(f"Incorrect code: '{code}'")
            print("Hint: University of Toronto was founded in 1827.")
            print("      Look for clues in the game world...\n")

    def do_read_note(self) -> None:
        """Read the note item if the player is carrying it or it is at the current location.

        Does NOT count as a move.
        """
        note = self.get_item("note")
        location = self.get_location()
        if note is None:
            print("There is no note to read.")
            return
        if not self.player.has_item("note") and "note" not in location.items:
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

        >>> game = AdventureGame('game_data.json', 0)
        >>> game.check_win()
        False
        """
        if self.current_location_id != DORM_LOCATION_ID:
            return False
        return "backup_usb" in self.get_location().items

    def check_lose(self) -> bool:
        """Return True if the player has exceeded their move limit.

        >>> game = AdventureGame('game_data.json', 0)
        >>> game.check_lose()
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

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _consume_coffee(self) -> None:
        """Handle coffee consumption: extend move limit and remove from inventory."""
        if self.coffee_consumed:
            return
        self.coffee_consumed = True
        self.player.remove_item("coffee")
        self.max_moves += COFFEE_BONUS_MOVES
        print(f"You drink the coffee. Ahh, that double-double hits the spot!")
        print(f"ENERGIZED! +{COFFEE_BONUS_MOVES} bonus moves added to your limit."
              f" ({self.max_moves - COFFEE_BONUS_MOVES} -> {self.max_moves})")

    def _check_ritual(self, location: Location) -> None:
        """Check whether all three sacred items are present at the ritual location.
        If so, perform the summoning ritual: items dissolve, backup_usb materialises.
        """
        if self.ritual_complete:
            return
        if not all(name in location.items for name in RITUAL_ITEMS):
            remaining = [n for n in RITUAL_ITEMS if n not in location.items]
            print(f"  (The circle waits... still need: {', '.join(remaining)})")
            return

        self.ritual_complete = True
        self.game_stage = 'ritual_done'

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
            if name in location.items:
                location.items.remove(name)

        backup = self.get_item("backup_usb")
        if backup is not None:
            backup.current_position = RITUAL_LOCATION_ID
            location.items.append("backup_usb")
            self.player.add_score(50)

    def _check_stage_messages(self) -> None:
        """Display context-sensitive messages based on current stage and location."""
        required = {"USB Drive", "Laptop Charger", "Lucky Mug"}
        collected = required.intersection(self.items_collected)

        # Advance the stage
        if self.game_stage == 'start' and collected:
            self.game_stage = 'exploring'
        if self.game_stage == 'exploring' and len(collected) >= 2:
            self.game_stage = 'gathering'
        if len(collected) == 3 and not self.ritual_complete:
            self.game_stage = 'ready_ritual'

        loc = self.current_location_id

        # King's College Circle - messages change each stage
        if loc == RITUAL_LOCATION_ID:
            if self.game_stage in ('start', 'exploring'):
                print("\n--- The founding circle feels alive. Something is waiting. ---\n")
            elif self.game_stage == 'gathering':
                n = len(collected)
                print(f"\n--- The circle pulses. You have {n}/3 sacred items. ---\n")
            elif self.game_stage == 'ready_ritual':
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
            elif self.game_stage == 'ritual_done':
                print("\n--- The circle is quiet now. Its work is done. ---\n")

        # Gerstein Library - partner messages
        if loc == 11:
            if self.game_stage == 'ready_ritual':
                print("\n--- Your partner at the window holds a sign: ---")
                print("    'DROP THE THREE IN THE CIRCLE -> TRUTH APPEARS'")
                print("    They give you a thumbs-up.\n")
            elif self.game_stage == 'ritual_done':
                print("\n--- Partner's sign: 'TAKE IT HOME AND SUBMIT! WE DID IT!' ---\n")

        # Server room - story revelation (only first time)
        if loc == 12 and self.server_room_unlocked:
            print("\n--- DOCUMENT ON THE DESK ---")
            print("Email: 'Deadline extended to 2pm - server maintenance.'")
            print("Partner's note: 'Found a critical bug. Fixed it overnight.")
            print("  The ritual will summon the corrected version. Submit THAT.'")
            print("  They were protecting you the whole time.\n")

    def _print_location_items(self, location: Location) -> None:
        """Print items present at the given location, if any."""
        if location.items:
            print("\nItems here:")
            for item_name in location.items:
                print(f"  - {item_name}")


# -------------------------------------------------------------------------
# Command display helper (used in the main loop)
# -------------------------------------------------------------------------

def _print_available_actions(location: Location, player: Player,
                              coffee_consumed: bool, server_room_unlocked: bool) -> None:
    """Print all valid commands the player can currently use, without duplicates."""
    print("\nWhat to do? Choose from: look, inventory, score, log, quit")
    print("At this location, you can also:")

    # Movement commands from JSON (all values are ints now)
    for action in location.available_commands:
        print(f"  - {action}")

    # Puzzle command at Bahen (loc 7) only
    if location.id_num == 7 and not server_room_unlocked:
        print("  - enter code")

    # Items at location: take / examine (no duplicates)
    shown = set()
    for name in location.items:
        key = name.lower()
        if key not in shown:
            print(f"  - take {name}")
            print(f"  - examine {name}")
            shown.add(key)

    # Items in inventory: drop / examine
    for item in player.inventory:
        key = item.name.lower()
        print(f"  - drop {item.name}")
        if key not in shown:
            print(f"  - examine {item.name}")
            shown.add(key)


if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    # })

    game_log = EventList()   # REQUIRED: baseline requirement
    game = AdventureGame('game_data.json', 0)   # start at dorm (id 0)
    menu = ["look", "inventory", "score", "log", "quit"]
    choice = None

    # Log and print the initial location
    start_loc = game.get_location()
    game_log.add_event(Event(start_loc.id_num, start_loc.long_description))
    print(start_loc.long_description)
    game._print_location_items(start_loc)

    while game.ongoing:
        location = game.get_location()

        # Build the full set of valid choices for input validation
        valid_choices = set(menu)
        # Movement commands from JSON
        for action in location.available_commands:
            valid_choices.add(action)
        # Dynamic item commands (case-insensitive matching)
        shown_items: set[str] = set()
        for name in location.items:
            key = name.lower()
            if key not in shown_items:
                valid_choices.add(f"take {name.lower()}")
                valid_choices.add(f"examine {name.lower()}")
                shown_items.add(key)
        for item in game.player.inventory:
            key = item.name.lower()
            valid_choices.add(f"drop {item.name.lower()}")
            if key not in shown_items:
                valid_choices.add(f"examine {item.name.lower()}")
                shown_items.add(key)
        # Puzzle command only available at Bahen (loc 7) when not yet unlocked
        if game.current_location_id == 7 and not game.server_room_unlocked:
            valid_choices.add("enter code")
        # Read note always available (handles gracefully if no note present)
        valid_choices.add("read note")

        _print_available_actions(location, game.player, game.coffee_consumed,
                                 game.server_room_unlocked)

        # Validate input
        choice = input("\nEnter action: ").lower().strip()
        while choice not in valid_choices:
            print("That was an invalid option; try again.")
            choice = input("\nEnter action: ").lower().strip()

        print("=" * 60)
        print(f"You decided to: {choice}")
        print("=" * 60)

        # ---- Menu commands ----
        if choice == "look":
            game.do_look()
        elif choice == "inventory":
            game.do_inventory()
        elif choice == "score":
            game.do_score()
        elif choice == "log":
            game_log.display_events()
        elif choice == "quit":
            print("Thanks for playing! Goodbye.")
            game.ongoing = False

        # ---- Movement ----
        elif choice.startswith("go "):
            direction = choice[3:].strip()
            success = game.do_go(direction, game_log)
            if success:
                new_loc = game.get_location()
                if new_loc.visited:
                    print(new_loc.brief_description)
                else:
                    new_loc.visited = True
                    print(new_loc.long_description)
                game._print_location_items(new_loc)

        # ---- Item commands ----
        elif choice.startswith("take "):
            game.do_take(choice[5:].strip())
        elif choice.startswith("drop "):
            game.do_drop(choice[5:].strip())
        elif choice.startswith("examine "):
            game.do_examine(choice[8:].strip())

        # ---- Puzzle / special commands ----
        elif choice == "enter code":
            game.do_enter_code()
        elif choice == "read note":
            game.do_read_note()

        # ---- Check win/lose after every action ----
        if game.ongoing:
            if game.check_win():
                game.display_win()
                game.ongoing = False
            elif game.check_lose():
                game.display_lose()
                game.ongoing = False
