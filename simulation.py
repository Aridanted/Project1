"""CSC111 Project 1: Text Adventure Game - Simulator

Instructions (READ THIS FIRST!)
===============================

This Python module contains code for Project 1 that allows a user to simulate
an entire playthrough of the game. Please consult the project handout for
instructions and details.

You can copy/paste your code from Assignment 1 into this file, and modify it as
needed to work with your game.

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
from event_logger import Event, EventList
from adventure import AdventureGame
from game_entities import Location


class AdventureGameSimulation:
    """A simulation of an adventure game playthrough.

    Instance Attributes:
        - None (all attributes are private)

    Representation Invariants:
        - self._events is not empty
    """
    # Private Instance Attributes:
    #   - _game: The AdventureGame instance that this simulation uses.
    #   - _events: A collection of the events to process during the simulation.
    _game: AdventureGame
    _events: EventList

    def __init__(self, game_data_file: str, initial_location_id: int, commands: list[str]) -> None:
        """Initialize a new game simulation based on the given game data, that runs through the given commands.

        >>> sim = AdventureGameSimulation('game_data.json', 1, ['go north', 'go south'])
        >>> len(sim.get_id_log())
        3
        >>> sim.get_id_log()[0]
        1

        Preconditions:
            - len(commands) > 0
            - all commands in the given list are valid commands when starting from the location at initial_location_id
        """
        self._events = EventList()
        self._game = AdventureGame(game_data_file, initial_location_id)

        # Add first event (initial location, no previous command)
        initial_location = self._game.get_location()
        self._events.add_event(Event(initial_location.id_num, initial_location.long_description))

        # Generate the remaining events based on the commands
        self.generate_events(commands, initial_location)

    def generate_events(self, commands: list[str], current_location: Location) -> None:
        """Generate events in this simulation, based on current_location and commands, a valid list of commands.

        >>> game = AdventureGame('game_data.json', 1)
        >>> sim = AdventureGameSimulation.__new__(AdventureGameSimulation)
        >>> sim._game = game
        >>> sim._events = EventList()
        >>> loc = game.get_location(1)
        >>> sim._events.add_event(Event(1, loc.long_description))
        >>> sim.generate_events(['go north', 'go south'], loc)
        >>> len(sim._events.get_id_log())
        3
        >>> sim._events.get_id_log()
        [1, 2, 1]

        Preconditions:
            - len(commands) > 0
            - all commands in the given list are valid commands when starting from current_location
        """
        for command in commands:
            # Handle different types of commands
            if command.startswith("go "):
                # Movement command
                direction = command[3:].strip()
                go_command = f"go {direction}"

                if go_command in current_location.available_commands:
                    result = current_location.available_commands[go_command]
                    
                    # Check if this is a special puzzle check command
                    if result == "action:puzzle_check":
                        # This represents entering location 12 from location 11
                        # The puzzle check allows movement to location 12
                        next_location_id = 12
                        next_location = self._game.get_location(next_location_id)
                        self._events.add_event(
                            Event(next_location.id_num, next_location.long_description),
                            command
                        )
                        current_location = next_location
                    elif isinstance(result, int):
                        next_location_id = result
                        next_location = self._game.get_location(next_location_id)
                        self._events.add_event(
                            Event(next_location.id_num, next_location.long_description),
                            command
                        )
                        current_location = next_location

            elif command == "talk to friend":
                # Special puzzle command - doesn't change location
                if "talk to friend" in current_location.available_commands:
                    # This command doesn't move us, so we stay at the same location
                    # but we still record it as an event
                    self._events.add_event(
                        Event(current_location.id_num, current_location.long_description),
                        command
                    )

            elif command.startswith("take ") or command.startswith("drop ") or command.startswith("examine "):
                # Item commands - don't change location but are still events
                self._events.add_event(
                    Event(current_location.id_num, current_location.long_description),
                    command
                )

            elif command in ["look", "inventory", "score", "log"]:
                # Menu commands - don't change location
                self._events.add_event(
                    Event(current_location.id_num, current_location.long_description),
                    command
                )

    def get_id_log(self) -> list[int]:
        """Get back a list of all location IDs in the order that they are visited within a game simulation
        that follows the given commands.

        >>> sim = AdventureGameSimulation('game_data.json', 1, ['go north', 'go east'])
        >>> log = sim.get_id_log()
        >>> log[0]
        1
        >>> log[1]
        2
        >>> log[2]
        4
        >>> len(log)
        3
        """
        return self._events.get_id_log()

    def run(self) -> None:
        """Run the game simulation and log location descriptions."""
        current_event = self._events.first

        print("=" * 60)
        print("GAME SIMULATION")
        print("=" * 60 + "\n")

        while current_event is not None:
            print(f"LOCATION {current_event.id_num}:")
            print(current_event.description)

            if current_event is not self._events.last:
                print(f"\n>>> You choose: {current_event.next_command}")
                print("-" * 60 + "\n")

            current_event = current_event.next

        print("\n" + "=" * 60)
        print("SIMULATION COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    # })

    # Walkthrough to WIN the game
    win_walkthrough = [
        "go north",  # 1 -> 2 (hallway)
        "go north",  # 2 -> 3 (common room)
        "talk to friend",  # Get permission (puzzle)
        "go south",  # 3 -> 2 (hallway)
        "go east",  # 2 -> 4 (St. George St)
        "go north",  # 4 -> 5 (Robarts entrance)
        "go north",  # 5 -> 6 (Robarts 1F)
        "go north",  # 6 -> 7 (Robarts 2F)
        "take usb drive",  # Pick up USB drive
        "go south",  # 7 -> 6
        "go south",  # 6 -> 5
        "go south",  # 5 -> 4
        "go east",  # 4 -> 8 (Bahen entrance)
        "go east",  # 8 -> 9 (Bahen 1F)
        "take toonie",  # Pick up toonie (bonus item)
        "go north",  # 9 -> 10 (Bahen 3F)
        "go east",  # 10 -> 11 (outside BA3200)
        "go north",  # 11 -> 12 (inside BA3200, uses friend's permission)
        "take laptop charger",  # Pick up charger
        "go south",  # 12 -> 11
        "go west",  # 11 -> 10
        "go south",  # 10 -> 9
        "go west",  # 9 -> 8
        "go west",  # 8 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go east",  # 4 -> 8
        "go west",  # 8 -> 13 (Wait, need to fix map)
    ]

    # Corrected win walkthrough
    win_walkthrough = [
        "go north",  # 1 -> 2 (hallway)
        "go north",  # 2 -> 3 (common room)
        "talk to friend",  # Get permission (puzzle)
        "go south",  # 3 -> 2 (hallway)
        "go east",  # 2 -> 4 (St. George St)
        "go north",  # 4 -> 5 (Robarts entrance)
        "go north",  # 5 -> 6 (Robarts 1F)
        "go north",  # 6 -> 7 (Robarts 2F study rooms)
        "take usb drive",  # Pick up USB drive
        "go south",  # 7 -> 6
        "go south",  # 6 -> 5
        "go south",  # 5 -> 4 (St. George St)
        "go east",  # 4 -> 8 (Bahen entrance)
        "go east",  # 8 -> 9 (Bahen 1F)
        "go north",  # 9 -> 10 (Bahen 3F)
        "go east",  # 10 -> 11 (outside BA3200)
        "go north",  # 11 -> 12 (inside BA3200, requires permission)
        "take laptop charger",  # Pick up laptop charger
        "go south",  # 12 -> 11
        "go west",  # 11 -> 10
        "go south",  # 10 -> 9
        "go west",  # 9 -> 8
        "go west",  # 8 -> 4 (St. George St)
        "go north",  # 4 -> 5 (Robarts entrance)
        "go south",  # 5 -> 4
        "go east",  # 4 -> 8
        "go west",  # Need to go to Tim Hortons via Sidney Smith
    ]

    # Final corrected win walkthrough - navigating to Tim Hortons
    win_walkthrough = [
        "go north",  # 1 -> 2 (Chestnut hallway)
        "go north",  # 2 -> 3 (common room)
        "talk to friend",  # Solve puzzle - get permission
        "go south",  # 3 -> 2
        "go east",  # 2 -> 4 (St. George St)
        "go north",  # 4 -> 5 (Robarts entrance)
        "go north",  # 5 -> 6 (Robarts 1F)
        "go north",  # 6 -> 7 (Robarts 2F - USB drive here)
        "take usb drive",  # Pick up USB drive
        "go south",  # 7 -> 6
        "go south",  # 6 -> 5
        "go south",  # 5 -> 4
        "go east",  # 4 -> 8 (Bahen entrance)
        "go east",  # 8 -> 9 (Bahen 1F)
        "go north",  # 9 -> 10 (Bahen 3F)
        "go east",  # 10 -> 11 (outside BA3200)
        "go north",  # 11 -> 12 (inside BA3200 - laptop charger here)
        "take laptop charger",  # Pick up laptop charger
        "go south",  # 12 -> 11
        "go west",  # 11 -> 10
        "go south",  # 10 -> 9
        "go west",  # 9 -> 8 (Bahen entrance)
        "go south",  # 8 -> 13 (Sidney Smith entrance)
        "go east",  # 13 -> 14 (Sidney Smith 1F)
        "go east",  # 14 -> 15 (Tim Hortons - lucky mug here)
        "take lucky mug",  # Pick up lucky mug
        "go west",  # 15 -> 14
        "go west",  # 14 -> 13
        "go north",  # 13 -> 8
        "go west",  # 8 -> 4
        "go west",  # 4 -> 2
        "go south",  # 2 -> 1 (back to dorm room)
        "drop usb drive",  # Drop all items in dorm
        "drop laptop charger",
        "drop lucky mug"
    ]

    expected_log = [1, 2, 3, 3, 2, 4, 5, 6, 7, 7, 6, 5, 4, 8, 9, 10, 11, 12, 12, 11, 10, 9, 8, 13, 14, 15, 15, 14,
                    13, 8, 4, 2, 1, 1, 1, 1]

    print("Testing WIN walkthrough...")
    sim = AdventureGameSimulation('game_data.json', 1, win_walkthrough)
    actual_log = sim.get_id_log()
    print(f"Expected: {expected_log}")
    print(f"Actual:   {actual_log}")
    assert expected_log == actual_log, f"Win walkthrough failed! Expected {expected_log}, got {actual_log}"
    print("✓ Win walkthrough test passed!\n")

    # Walkthrough to LOSE the game (run out of moves)
    lose_demo = [
        "go north",  # 1 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
        "go east",  # 2 -> 4
        "go west",  # 4 -> 2
    ]  # This exceeds 35 moves

    expected_log_lose = [1, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4, 2,
                         4, 2, 4, 2, 4, 2]

    print("Testing LOSE walkthrough...")
    sim = AdventureGameSimulation('game_data.json', 1, lose_demo)
    actual_log = sim.get_id_log()
    print(f"Expected: {expected_log_lose}")
    print(f"Actual:   {actual_log}")
    assert expected_log_lose == actual_log, f"Lose walkthrough failed!"
    print("✓ Lose walkthrough test passed!\n")

    # Demo showing inventory feature
    inventory_demo = [
        "go north",  # 1 -> 2
        "go east",  # 2 -> 4
        "go north",  # 4 -> 5
        "go north",  # 5 -> 6
        "go north",  # 6 -> 7 (USB drive location)
        "take usb drive",  # Pick up item
        "inventory",  # Check inventory
    ]

    expected_log_inventory = [1, 2, 4, 5, 6, 7, 7, 7]

    print("Testing INVENTORY demo...")
    sim = AdventureGameSimulation('game_data.json', 1, inventory_demo)
    actual_log = sim.get_id_log()
    assert expected_log_inventory == actual_log, f"Inventory demo failed!"
    print("✓ Inventory demo test passed!\n")

    # Demo showing score feature
    scores_demo = [
        "go north",  # 1 -> 2
        "go east",  # 2 -> 4
        "go north",  # 4 -> 5
        "go north",  # 5 -> 6
        "go north",  # 6 -> 7
        "take usb drive",  # Gain points for picking up
        "score",  # Check score
    ]

    expected_log_scores = [1, 2, 4, 5, 6, 7, 7, 7]

    print("Testing SCORE demo...")
    sim = AdventureGameSimulation('game_data.json', 1, scores_demo)
    actual_log = sim.get_id_log()
    assert expected_log_scores == actual_log, f"Scores demo failed!"
    print("✓ Scores demo test passed!\n")

    # Demo for Enhancement 1: Examine command
    enhancements_demo_examine = [
        "go north",  # 1 -> 2
        "go east",  # 2 -> 4
        "go north",  # 4 -> 5
        "go north",  # 5 -> 6
        "go north",  # 6 -> 7
        "examine usb drive",  # Examine item before taking it
        "take usb drive",
        "examine usb drive",  # Examine item in inventory
    ]

    expected_log_examine = [1, 2, 4, 5, 6, 7, 7, 7, 7]

    print("Testing EXAMINE enhancement demo...")
    sim = AdventureGameSimulation('game_data.json', 1, enhancements_demo_examine)
    actual_log = sim.get_id_log()
    assert expected_log_examine == actual_log, f"Examine enhancement demo failed!"
    print("✓ Examine enhancement demo test passed!\n")

    # Demo for Enhancement 2: Puzzle (talk to friend)
    enhancements_demo_puzzle = [
        "go north",  # 1 -> 2
        "go north",  # 2 -> 3 (common room with friend)
        "talk to friend",  # Solve puzzle to get permission
    ]

    expected_log_puzzle = [1, 2, 3, 3]

    print("Testing PUZZLE enhancement demo...")
    sim = AdventureGameSimulation('game_data.json', 1, enhancements_demo_puzzle)
    actual_log = sim.get_id_log()
    assert expected_log_puzzle == actual_log, f"Puzzle enhancement demo failed!"
    print("✓ Puzzle enhancement demo test passed!\n")

    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
