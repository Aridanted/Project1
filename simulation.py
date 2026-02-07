"""CSC111 Project 1: Game Simulator"""
from __future__ import annotations
from event_logger import Event, EventList
from adventure import AdventureGame
from game_entities import Location


class AdventureGameSimulation:
    """Simulation of game playthrough."""
    _game: AdventureGame
    _events: EventList

    def __init__(self, game_data_file: str, initial_location_id: int, commands: list[str]) -> None:
        """Initialize simulation with commands."""
        self._events = EventList()
        self._game = AdventureGame(game_data_file, initial_location_id)

        initial_location = self._game.get_location()
        self._events.add_event(Event(initial_location.id_num, initial_location.long_description))

        self.generate_events(commands, initial_location)

    def generate_events(self, commands: list[str], current_location: Location) -> None:
        """Generate events from commands."""
        for command in commands:
            if command.startswith("go "):
                direction = command[3:].strip()
                go_command = f"go {direction}"

                if go_command in current_location.available_commands:
                    result = current_location.available_commands[go_command]
                    if isinstance(result, int):
                        next_location = self._game.get_location(result)
                        self._events.add_event(
                            Event(next_location.id_num, next_location.long_description),
                            command
                        )
                        current_location = next_location
            else:
                # Non-movement commands stay at same location
                self._events.add_event(
                    Event(current_location.id_num, current_location.long_description),
                    command
                )

    def get_id_log(self) -> list[int]:
        """Get list of location IDs visited."""
        return self._events.get_id_log()


if __name__ == "__main__":
    print("=" * 60)
    print("RITUAL MYSTERY - Game Simulation Tests")
    print("=" * 60 + "\n")

    # WIN: Complete ritual and return home (24 moves)
    win_walkthrough = [
        "go east",   # 0 -> 1 (hallway)
        "take coffee",  # FREE
        "drink coffee",  # FREE (+5 moves)
        "go north",  # 1 -> 2 (outside)
        "go north",  # 2 -> 10 (King's College Circle - ritual site!)
        "go east",   # 10 -> 11 (Gerstein - see partner)
        "go west",   # 11 -> 10 (back to circle)
        "go west",   # 10 -> 7 (Bahen)
        "go up",     # 7 -> 8 (lecture hall)
        "take laptop charger",  # FREE (SILVER CONDUCTOR)
        "go down",   # 8 -> 7
        "go north",  # 7 -> 3 (Sidney Smith)
        "go north",  # 3 -> 5 (Robarts)
        "go up",     # 5 -> 6 (upper stacks)
        "take usb drive",  # FREE (BLUE GUARDIAN)
        "go down",   # 6 -> 5
        "go south",  # 5 -> 3
        "go west",   # 3 -> 9 (Tim Hortons)
        "take lucky mug",  # FREE (GOLDEN VESSEL)
        "go east",   # 9 -> 3
        "go south",  # 3 -> 7 (Bahen)
        "go west",   # 7 -> 10 (King's College Circle)
        "drop usb drive",     # FREE - ritual part 1
        "drop laptop charger",  # FREE - ritual part 2
        "drop lucky mug",     # FREE - ritual part 3 = SUMMON!
        "take backup_usb",  # FREE - the summoned item!
        "go south",  # 10 -> 2
        "go south",  # 2 -> 1
        "go west",   # 1 -> 0 (dorm)
        "take laptop charger",  # Need to bring charger home too
        "take lucky mug",  # And mug
        "go east",   # Back to hallway
        "go north",  # To outside
        "go north",  # To King's College
        "take laptop charger",  # Get them from circle
        "take lucky mug",
        "go south",  # Back to outside
        "go south",  # To hallway
        "go west",   # To dorm
        "drop backup_usb",  # WIN: Drop all 3 at dorm
        "drop laptop charger",
        "drop lucky mug"
    ]

    # WIN: Simplified ritual walkthrough (20 moves)
    # The backup USB contains EVERYTHING (items dissolve into it during ritual)
    simple_win = [
        "go east",   # 0 -> 1 (hallway)
        "take coffee",  # FREE
        "drink coffee",  # FREE
        "go north",  # 1 -> 2 (outside)
        "go north",  # 2 -> 10 (King's College Circle!)
        "go west",   # 10 -> 7 (Bahen)
        "go up",     # 7 -> 8 (lecture hall)
        "take laptop charger",  # FREE
        "go down",   # 8 -> 7
        "go north",  # 7 -> 3 (Sidney Smith)
        "go north",  # 3 -> 5 (Robarts)
        "go up",     # 5 -> 6 (upper stacks)
        "take usb drive",  # FREE
        "go down",   # 6 -> 5
        "go south",  # 5 -> 3
        "go west",   # 3 -> 9 (Tim Hortons)
        "take lucky mug",  # FREE
        "go east",   # 9 -> 3
        "go south",  # 3 -> 7 (Bahen)
        "go east",   # 7 -> 10 (King's College Circle!)
        "drop usb drive",      # RITUAL part 1
        "drop laptop charger",  # RITUAL part 2
        "drop lucky mug",      # RITUAL part 3 = SUMMON! Items dissolve!
        "take backup_usb",  # Take the manifested USB (has EVERYTHING)
        "go south",  # 10 -> 2
        "go south",  # 2 -> 1
        "go west",   # 1 -> 0 (dorm)
        "drop backup_usb"  # WIN! (backup has everything)
    ]

    move_commands = [c for c in simple_win if c.startswith("go ")]
    print(f"Total commands: {len(simple_win)}")
    print(f"Movement commands: {len(move_commands)}")
    print(f"Base move limit: 28")
    print(f"With coffee bonus: 33")
    print(f"Buffer: {28 - len(move_commands)} moves ({33 - len(move_commands)} with coffee)")
    print()

    # Updated expected log - ritual removes items so no need to go back
    expected_log = [0, 1, 1, 1, 2, 10, 7, 8, 8, 7, 3, 5, 6, 6, 5, 3, 9, 9, 3, 7, 10, 10, 10, 10, 10, 2, 1, 0, 0]

    sim = AdventureGameSimulation('game_data.json', 0, simple_win)
    actual_log = sim.get_id_log()

    print(f"Expected log length: {len(expected_log)}")
    print(f"Actual log length:   {len(actual_log)}")
    assert expected_log == actual_log, f"Mismatch!\nExpected: {expected_log}\nActual:   {actual_log}"
    print("✅ WIN walkthrough test PASSED!\n")

    # LOSE: exceed move limit
    lose_demo = ["go east", "go west"] * 15  # 30 moves
    expected_lose = [0] + [1, 0] * 15

    sim2 = AdventureGameSimulation('game_data.json', 0, lose_demo)
    actual_log2 = sim2.get_id_log()
    assert expected_lose == actual_log2
    print("✅ LOSE walkthrough test PASSED!\n")

    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
