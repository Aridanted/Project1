"""CSC111 Project 1: Text Adventure Game - Enhanced Version

Advanced Features:
- Combination lock puzzle (4-digit keypad code)
- Coffee consumable that extends move limit
- Only movement commands count as moves (look, inventory, examine are free)
- Multi-step puzzle requiring exploration and note-finding

Copyright (c) 2026 CSC111 Teaching Team
"""
from __future__ import annotations
import json
from typing import Optional

from game_entities import Location, Item, Player
from event_logger import Event, EventList

# Game Constants
BASE_MAX_MOVES = 28  # Base move limit (only GO commands count!) - gives 8 move buffer over optimal 20
REQUIRED_ITEMS = ["USB Drive", "Laptop Charger", "Lucky Mug"]
SERVER_ROOM_ID = 9  # Location ID of the server room
COFFEE_BONUS_MOVES = 5  # Bonus moves from drinking coffee


class AdventureGame:
    """Text adventure game with advanced puzzle mechanics.

    Instance Attributes:
        - current_location_id: Current location ID
        - ongoing: Whether game is still running
        - player: Player object with inventory and score
        - event_list: EventList tracking all events
        - max_moves: Maximum allowed moves (can increase with coffee)
        - server_room_unlocked: Whether server room has been unlocked
        - coffee_consumed: Whether player has drunk the coffee
        - puzzle_code: The correct keypad code
        - game_stage: Current story stage for dynamic messages
        - items_collected: Set of collected item names
        - ritual_complete: Whether ritual has been performed

    Representation Invariants:
        - self.current_location_id in self._locations
        - self.max_moves >= BASE_MAX_MOVES
        - self.game_stage in ['start', 'exploring', 'gathering', 'ready_ritual', 'ritual_done', 'winning']
    """
    _locations: dict[int, Location]
    _items: dict[str, Item]
    current_location_id: int
    ongoing: bool
    player: Player
    event_list: EventList
    max_moves: int
    server_room_unlocked: bool
    coffee_consumed: bool
    puzzle_code: str
    game_stage: str
    items_collected: set[str]
    ritual_complete: bool

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """Initialize game from JSON file."""
        self._locations, self._items, self.puzzle_code = self._load_game_data(game_data_file)
        self.current_location_id = initial_location_id
        self.ongoing = True
        self.player = Player()
        self.event_list = EventList()
        self.max_moves = BASE_MAX_MOVES
        self.server_room_unlocked = False
        self.coffee_consumed = False
        self.game_stage = 'start'
        self.items_collected = set()
        self.ritual_complete = False

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], dict[str, Item], str]:
        """Load game data from JSON file."""
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

        items = {}
        for item_data in data['items']:
            item_obj = Item(
                item_data['name'],
                item_data['description'],
                item_data['start_position'],
                item_data['target_position'],
                item_data['target_points'],
                item_data.get('pickup_points', 0)
            )
            items[item_data['name']] = item_obj

        puzzle_code = data.get('puzzle_code', '1992')
        return locations, items, puzzle_code

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Get location by ID (current if None)."""
        if loc_id is None:
            return self._locations[self.current_location_id]
        return self._locations[loc_id]

    def get_item(self, item_name: str) -> Optional[Item]:
        """Get item by name (case-insensitive)."""
        for name, item in self._items.items():
            if name.lower() == item_name.lower():
                return item
        return None

    def handle_go_command(self, direction: str) -> bool:
        """Handle movement. THIS IS THE ONLY COMMAND THAT COUNTS AS A MOVE!

        Returns True if successful, False otherwise.
        """
        location = self.get_location()
        command = f"go {direction}"

        if command in location.available_commands:
            result = location.available_commands[command]
            if isinstance(result, int):
                self.current_location_id = result
                self.player.increment_moves()

                # Show stage-specific messages
                self.check_and_display_stage_messages()

                return True
        print(f"You can't go {direction} from here.")
        return False

    def check_and_display_stage_messages(self) -> None:
        """Display dynamic messages based on game stage and location."""
        # Update game stage
        required_items = {"USB Drive", "Laptop Charger", "Lucky Mug"}
        collected = required_items.intersection(self.items_collected)

        if self.game_stage == 'start' and len(collected) > 0:
            self.game_stage = 'exploring'
        elif self.game_stage == 'exploring' and len(collected) == 1:
            self.game_stage = 'gathering'
        elif len(collected) == 3 and not self.ritual_complete:
            self.game_stage = 'ready_ritual'
        elif self.ritual_complete:
            self.game_stage = 'ritual_done'

        # King's College Circle - special messages based on stage
        if self.current_location_id == 10:
            if self.game_stage == 'start' or self.game_stage == 'exploring':
                print("\n" + "=" * 60)
                print("The founding circle feels... alive. Waiting.")
                print("You sense this place holds great power.")
                print("=" * 60 + "\n")
            elif self.game_stage == 'gathering':
                print("\n" + "=" * 60)
                print(f"You have {len(collected)} of 3 items needed.")
                print("The circle pulses faintly. It knows you're close...")
                print("=" * 60 + "\n")
            elif self.game_stage == 'ready_ritual':
                print("\n" + "=" * 60)
                print("⚡ THE TIME HAS COME ⚡")
                print("=" * 60)
                print("\nYou have all three sacred items!")
                print("The chalk triangle glows with anticipation.")
                print("\n🔮 RITUAL INSTRUCTIONS:")
                print("   1. DROP the USB Drive (Blue Guardian)")
                print("   2. DROP the Laptop Charger (Silver Conductor)")
                print("   3. DROP the Lucky Mug (Golden Vessel)")
                print("\nWhen all three rest in the circle,")
                print("the truth shall manifest!")
                print("=" * 60 + "\n")

        # Server room - explain the puzzle's importance
        if self.current_location_id == 12 and self.server_room_unlocked:
            print("\n" + "=" * 60)
            print("📄 DOCUMENT FOUND")
            print("=" * 60)
            print("\nOfficial Email from CS Department:")
            print("'Project deadline EXTENDED to 2pm due to server maintenance.'")
            print("\nHandwritten note from your partner:")
            print("'I found a CRITICAL BUG in our code that would cause instant")
            print("failure. I've been up all night fixing it. The ritual will")
            print("summon the corrected version. Submit THAT one, not the old USB.'")
            print("\nSo THAT'S why they hid everything! They were protecting you!")
            print("=" * 60 + "\n")

        # Gerstein - see partner watching
        if self.current_location_id == 11:
            if self.game_stage == 'ready_ritual':
                print("\n" + "=" * 60)
                print("👤 YOUR PARTNER!")
                print("=" * 60)
                print("\nYour partner is at the window holding a large sign:")
                print("\n  '3 ITEMS → CIRCLE → DROP ALL'")
                print("  'TRUTH WILL APPEAR!'")
                print("\nThey give you a thumbs up. You can do this!")
                print("=" * 60 + "\n")
            elif self.game_stage == 'ritual_done':
                print("\n" + "=" * 60)
                print("Your partner is grinning and holding a sign:")
                print("  'NOW GET IT HOME AND SUBMIT!'")
                print("  'WE'RE GOING TO PASS! 🎉'")
                print("=" * 60 + "\n")

    def handle_look_command(self) -> None:
        """Display full location description. Does NOT count as a move."""
        location = self.get_location()
        print(location.long_description)
        self._display_location_items(location)

    def handle_inventory_command(self) -> None:
        """Display inventory. Does NOT count as a move."""
        if len(self.player.inventory) == 0:
            print("Your inventory is empty.")
        else:
            print("\n=== INVENTORY ===")
            for item in self.player.inventory:
                print(f"- {item.name}")
            print("=================\n")

    def handle_score_command(self) -> None:
        """Display score and moves. Does NOT count as a move."""
        max_score = 175  # Total possible points
        percentage = (self.player.score / max_score) * 100

        print(f"\n{'='*60}")
        print("GAME STATUS")
        print("=" * 60)
        print(f"Score: {self.player.score}/{max_score} ({percentage:.1f}%)")
        print(f"Moves: {self.player.moves_made}/{self.max_moves}")

        # Progress indicators
        required = {"USB Drive", "Laptop Charger", "Lucky Mug"}
        collected = required.intersection(self.items_collected)
        print(f"Sacred Items: {len(collected)}/3")

        if self.coffee_consumed:
            print("Status: ☕ ENERGIZED (coffee bonus active!)")
        if self.ritual_complete:
            print("Ritual: ✓ COMPLETE (backup USB acquired!)")

        print("=" * 60 + "\n")

    def handle_take_command(self, item_name: str) -> None:
        """Take item. Does NOT count as a move."""
        location = self.get_location()
        item = self.get_item(item_name)

        if item is None or item.name not in location.items:
            print(f"There is no '{item_name}' here.")
            return

        location.items.remove(item.name)
        item.current_position = -1
        self.player.add_item(item)
        self.player.add_score(item.pickup_points)

        # Track collected items
        self.items_collected.add(item.name)

        print(f"\nYou picked up the {item.name}.")
        if item.pickup_points > 0:
            print(f"+{item.pickup_points} points!")

        # Special messages for key items
        if item.name == "USB Drive":
            print("\n💾 The BLUE GUARDIAN acquired!")
            print("You notice it's dated from 2 days ago...")
            required = {"USB Drive", "Laptop Charger", "Lucky Mug"}
            remaining = required - self.items_collected
            if remaining:
                print(f"Still need: {', '.join(remaining)}")
        elif item.name == "Laptop Charger":
            print("\n🔌 The SILVER CONDUCTOR acquired!")
            print("A note: 'Borrowed to fix your code all night.'")
            required = {"USB Drive", "Laptop Charger", "Lucky Mug"}
            remaining = required - self.items_collected
            if remaining:
                print(f"Still need: {', '.join(remaining)}")
        elif item.name == "Lucky Mug":
            print("\n☕ The GOLDEN VESSEL acquired!")
            print("Receipt inside: 3:47 AM - your partner was up all night!")
            required = {"USB Drive", "Laptop Charger", "Lucky Mug"}
            remaining = required - self.items_collected
            if remaining:
                print(f"Still need: {', '.join(remaining)}")
            else:
                print("\n" + "="*60)
                print("⚡ ALL THREE SACRED ITEMS COLLECTED! ⚡")
                print("="*60)
                print("\nHead to KING'S COLLEGE CIRCLE to perform the ritual!")
                print("=" * 60)

        # Special: Coffee gives bonus moves!
        if item.name.lower() == "coffee" and not self.coffee_consumed:
            self.handle_drink_coffee()

    def handle_drop_command(self, item_name: str) -> None:
        """Drop item. Does NOT count as a move.

        Special: If all 3 required items dropped at King's College Circle,
        triggers the summoning ritual!
        """
        item = self.player.remove_item(item_name)

        if item is None:
            print(f"You don't have '{item_name}'.")
            return

        location = self.get_location()
        location.items.append(item.name)
        item.current_position = self.current_location_id

        print(f"You drop the {item.name}.")

        # Award points for correct location
        if self.current_location_id == item.target_position and item.target_points > 0:
            self.player.add_score(item.target_points)
            print(f"It belongs here! +{item.target_points} points!")

        # Check for ritual at King's College Circle (location 10)
        if self.current_location_id == 10:
            self.check_ritual()

    def check_ritual(self) -> None:
        """Check if ritual is complete (all 3 items at King's College Circle)."""
        location = self.get_location()
        required = ["USB Drive", "Laptop Charger", "Lucky Mug"]

        all_present = all(item in location.items for item in required)

        if all_present and not self.ritual_complete:
            self.ritual_complete = True
            print("\n" + "=" * 70)
            print(" " * 20 + "⚡ THE RITUAL BEGINS ⚡")
            print("=" * 70)
            print("\nThe three items glow with ethereal light!")
            print("\n  💾 BLUE... (USB Drive rises)")
            print("  🔌 SILVER... (Charger levitates)")
            print("  ☕ GOLD... (Mug floats up)")
            print("\nThey orbit each other, forming a perfect triangle!")
            print("Energy crackles between them!")
            print("\nA BLINDING FLASH OF LIGHT!")
            print("\nWhen your vision clears...")
            print("\n✨ A NEW USB DRIVE materializes in the center! ✨")
            print("\nIt's labeled: 'FIXED VERSION - NO BUGS - SUBMIT THIS ONE'")
            print("\nThe three original items DISSOLVE into particles of light,")
            print("merging with the new USB drive!")
            print("\nYour partner's voice echoes across campus:")
            print("'I fixed the code. The backup has EVERYTHING you need!'")
            print("'Charger and mug are infused into it - just take the USB home!'")
            print("\n💎 +50 POINTS! The ritual is complete!")
            print("=" * 70 + "\n")

            # Remove the three original items from the location
            for item_name in required:
                if item_name in location.items:
                    location.items.remove(item_name)

            # Spawn the backup USB at this location
            backup = self.get_item("backup_usb")
            if backup:
                backup.current_position = 10
                location.items.append("backup_usb")
                self.player.add_score(50)

            # Update game stage
            self.game_stage = 'ritual_done'

    def handle_examine_command(self, item_name: str) -> None:
        """Examine item. Does NOT count as a move."""
        item = self.get_item(item_name)
        if item is None:
            print(f"No such item: '{item_name}'.")
            return

        location = self.get_location()
        if self.player.has_item(item_name) or item.name in location.items:
            print(f"\n{item.name}:")
            print(item.description)
            print()
        else:
            print(f"You can't see '{item_name}' here.")

    def handle_read_note_command(self) -> None:
        """Read the note (if in inventory or at location)."""
        note_item = self.get_item("note")
        if note_item is None:
            print("No note to read.")
            return

        location = self.get_location()
        if self.player.has_item("note") or "note" in location.items:
            print("\nThe note reads:")
            print("  'The bug is in the file handler. I fixed it.'")
            print("  'The code is 1992. Get the backup from the server room.'")
            print("  'Submit mine, not yours. We'll make the deadline. - Partner'")
            print("\nThe mystery deepens... your partner was trying to HELP you!\n")
        else:
            print("You don't have the note.")

    def handle_keypad_command(self) -> None:
        """Handle keypad puzzle (4-digit code: 1827 = UofT founding year)."""
        if self.current_location_id != 7:
            print("There's no keypad here.")
            return

        if self.server_room_unlocked:
            print("The server room is already unlocked. Go SOUTH to enter.")
            return

        print("\nThe keypad shows: ◆ ◆ ◆ ◆")
        print("A note on the wall says: 'When UofT was born, so was the code.'")
        print("\nEnter 4-digit code (or 'cancel'):")
        code = input("> ").strip()

        if code.lower() == 'cancel':
            print("Cancelled.")
            return

        if code == self.puzzle_code:
            print("\n" + "=" * 60)
            print("✓ *BEEP* ACCESS GRANTED!")
            print("=" * 60)
            print("\nThe server room door unlocks with a satisfying CLICK.")
            print("You hear servers humming inside...")
            print("\n🔓 PUZZLE SOLVED! +20 POINTS!")
            print("\nThe server room contains important clues about what")
            print("your partner has been doing and WHY they hid everything!")
            print("=" * 60 + "\n")

            self.server_room_unlocked = True
            # Add special command to go south to server room
            self._locations[7].available_commands["go south"] = 12
            self.player.add_score(20)
        else:
            print("\n" + "=" * 60)
            print("✗ *BUZZ* ACCESS DENIED")
            print("=" * 60)
            print(f"\nIncorrect code: {code}")
            print("\nHint: The note says 'When UofT was born'...")
            print("When was the University of Toronto founded?")
            print("(You can look this up or find clues on campus)")
            print("=" * 60 + "\n")

    def handle_drink_coffee(self) -> None:
        """Drink coffee to get bonus moves."""
        if not self.player.has_item("coffee"):
            print("You don't have coffee.")
            return

        if self.coffee_consumed:
            print("You already drank coffee!")
            return

        print("\nYou drink the coffee. Ahh, that double-double hits the spot!")
        print(f"You feel energized! +{COFFEE_BONUS_MOVES} bonus moves added to your limit!")
        self.max_moves += COFFEE_BONUS_MOVES
        self.coffee_consumed = True
        # Remove coffee from inventory after drinking
        self.player.remove_item("coffee")

    def check_win_condition(self) -> bool:
        """Check if player won (backup_usb at dorm).

        The backup USB contains everything (code + charger + mug power)!
        """
        if self.current_location_id != 0:
            return False

        location = self.get_location()
        return "backup_usb" in location.items

    def check_lose_condition(self) -> bool:
        """Check if player lost (exceeded move limit)."""
        return self.player.moves_made >= self.max_moves

    def display_game_over(self, won: bool) -> None:
        """Display game over message."""
        print("\n" + "=" * 60)
        if won:
            print("""
    ╔══════════════════════════════════════════════════════╗
    ║           🎉  YOU WON! MYSTERY SOLVED! 🎉           ║
    ╚══════════════════════════════════════════════════════╝
            """)
            print("You rush back to your dorm and submit the FIXED code!")
            print("12:57pm - 3 minutes to spare!")
            print("\nYour partner appears at the door:")
            print("'I'm sorry for the mystery. They were watching - trying to")
            print("sabotage our project. I had to hide everything and leave")
            print("clues only YOU would understand. The ritual was to make sure")
            print("you got the FIXED version, not the buggy one.'")
            print("\n'We're a team. Always.'")
            print("\nThe project submits successfully. You both pass with flying colors!")
        else:
            print("""
    ╔══════════════════════════════════════════════════════╗
    ║           ⏰  TIME'S UP! GAME OVER  ⏰              ║
    ╚══════════════════════════════════════════════════════╝
            """)
            print("1:00pm. The deadline has passed.")
            print("Your laptop screen flickers: 'Submission window closed.'")
            print("\nYour partner texts: 'I tried to help... I'm sorry.'")
            print("The mystery remains unsolved...")

        print(f"\n{'='*60}")
        print(f"FINAL SCORE: {self.player.score} points")
        print(f"MOVES USED: {self.player.moves_made}/{self.max_moves}")
        if hasattr(self, 'ritual_complete') and self.ritual_complete:
            print("RITUAL: Completed ✓")
        print("=" * 60 + "\n")

    def _display_location_items(self, location: Location) -> None:
        """Display items at location."""
        if len(location.items) > 0:
            print("\nItems here:")
            for item_name in location.items:
                print(f"  - {item_name}")


def play_game() -> None:
    """Main game loop."""
    print("=" * 60)
    print("THE MISSING ITEMS - A U of T Text Adventure")
    print("=" * 60)
    print("\n12:15pm. You wake up in a panic. The project is due at 1pm!")
    print("You're missing: USB drive, laptop charger, and lucky mug.")
    print("\nIMPORTANT: Only MOVEMENT (go commands) counts toward your move limit!")
    print("Commands like 'look', 'inventory', 'examine' are FREE.\n")
    print("=" * 60 + "\n")

    game = AdventureGame('game_data.json', 0)
    menu = ["look", "inventory", "score", "log", "quit", "help"]

    location = game.get_location()
    game.event_list.add_event(Event(location.id_num, location.long_description))
    print(location.long_description)
    game._display_location_items(location)

    while game.ongoing:
        location = game.get_location()
        if not location.visited:
            location.visited = True

        print("\n" + "-" * 60)
        print("Available: look, inventory, score, log, quit, help")
        print("At this location:")

        # Show movement commands
        for action in location.available_commands:
            if action.startswith("go "):
                print(f"  - {action}")

        # Show special commands (not go, not action:)
        for action in location.available_commands:
            if not action.startswith("go ") and not action.startswith("action:"):
                print(f"  - {action}")

        # Show items at location (take/examine) - avoid duplicates
        shown_items = set()
        for item_name in location.items:
            item_lower = item_name.lower()
            if item_lower not in shown_items:
                print(f"  - take {item_name}")
                print(f"  - examine {item_name}")
                shown_items.add(item_lower)

        # Show inventory items (drop/examine) - avoid duplicates
        for item in game.player.inventory:
            item_lower = item.name.lower()
            if item_lower not in shown_items:
                print(f"  - drop {item.name}")
                print(f"  - examine {item.name}")
                shown_items.add(item_lower)
            else:
                # Only show drop if not already shown as location item
                print(f"  - drop {item.name}")

            # Special: can drink coffee
            if item.name.lower() == "coffee" and not game.coffee_consumed:
                print(f"  - drink coffee")

        choice = input("\nWhat do you do? ").lower().strip()
        if not choice:
            continue

        print("\n" + "=" * 60)

        # Handle commands
        if choice == "look":
            game.handle_look_command()
        elif choice == "inventory":
            game.handle_inventory_command()
        elif choice == "score":
            game.handle_score_command()
        elif choice == "log":
            game.event_list.display_events()
        elif choice == "quit":
            print("Thanks for playing!")
            game.ongoing = False
        elif choice == "help":
            print("\n=== HELP ===")
            print("Goal: Find USB drive, laptop charger, lucky mug.")
            print("      Return all to your dorm (Location 0) before moves run out!")
            print("\nMOVE COUNTING:")
            print("  - Only 'go [direction]' counts as a move!")
            print("  - look, inventory, examine, take, drop are FREE")
            print("\nCommands:")
            print("  go [north/south/east/west/up/down]")
            print("  take/drop/examine [item]")
            print("  look, inventory, score, log, quit")
            print("Special:")
            print("  - 'talk to friend' (at friend's room)")
            print("  - 'enter code' (at Bahen keypad)")
            print("  - 'drink coffee' (bonus moves!)")
            print("  - 'read note' (when you have the note)")
            print("============\n")
        elif choice.startswith("go "):
            direction = choice[3:].strip()
            success = game.handle_go_command(direction)
            if success:
                location = game.get_location()
                game.event_list.add_event(Event(location.id_num, location.long_description), choice)
                if location.visited:
                    print(location.brief_description)
                else:
                    print(location.long_description)
                game._display_location_items(location)
        elif choice.startswith("take "):
            item_name = choice[5:].strip()
            game.handle_take_command(item_name)
        elif choice.startswith("drop "):
            item_name = choice[5:].strip()
            game.handle_drop_command(item_name)
        elif choice.startswith("examine "):
            item_name = choice[8:].strip()
            game.handle_examine_command(item_name)
        elif choice in ["enter code", "use keypad"]:
            game.handle_keypad_command()
        elif choice == "read note":
            game.handle_read_note_command()
        elif choice == "drink coffee":
            game.handle_drink_coffee()
        else:
            print("Invalid command. Type 'help' for commands.")

        if game.ongoing:
            if game.check_win_condition():
                game.display_game_over(won=True)
                game.ongoing = False
            elif game.check_lose_condition():
                game.display_game_over(won=False)
                game.ongoing = False


if __name__ == "__main__":
    play_game()
