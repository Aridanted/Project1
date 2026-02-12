"""CSC111 Project 1: Game Simulation

Provides AdventureGameSimulation for automated walkthroughs used in testing,
and five demo lists that are referenced in the project report:
  - win_walkthrough
  - lose_demo
  - inventory_demo
  - scores_demo
  - enhancements_demo

This file is Copyright (c) 2026 CSC111 Teaching Team
"""
from __future__ import annotations
from event_logger import Event, EventList
from adventure import AdventureGame
from game_entities import Location


class AdventureGameSimulation:
    """Runs a predetermined sequence of commands through AdventureGame
    and records the resulting sequence of location IDs.

    Instance Attributes:
        - _game: The AdventureGame instance being simulated
        - _events: The EventList recording every location visited

    Representation Invariants:
        - len(self._events.get_id_log()) >= 1
    """
    _game: AdventureGame
    _events: EventList

    def __init__(self, game_data_file: str, initial_location_id: int,
                 commands: list[str]) -> None:
        """Initialize simulation: create a fresh game and replay all commands.

        Preconditions:
            - game_data_file is the filename of a valid game data JSON file
            - initial_location_id is a valid location ID
            - commands is a list of valid game commands
        """
        self._events = EventList()
        self._game = AdventureGame(game_data_file, initial_location_id)

        start = self._game.get_location()
        self._events.add_event(Event(start.id_num, start.long_description))

        self._replay(commands)

    def _replay(self, commands: list[str]) -> None:
        """Replay a list of commands, recording a location event after every command.

        Movement commands ('go ...') change the current location.
        All other commands stay at the current location.
        """
        for command in commands:
            if command.startswith("go "):
                direction = command[3:].strip()
                go_cmd = f"go {direction}"
                location = self._game.get_location()

                if go_cmd in location.available_commands:
                    result = location.available_commands[go_cmd]
                    if isinstance(result, int):
                        self._game.current_location_id = result
                        self._game.player.increment_moves()

                new_loc = self._game.get_location()
                self._events.add_event(
                    Event(new_loc.id_num, new_loc.long_description), command
                )
            else:
                # Non-movement: stay at current location, still log the event
                current = self._game.get_location()
                self._events.add_event(
                    Event(current.id_num, current.long_description), command
                )

    def get_id_log(self) -> list[int]:
        """Return the list of location IDs in the order they were visited/recorded.

        >>> sim = AdventureGameSimulation('game_data.json', 0, [])
        >>> sim.get_id_log()
        [0]
        """
        return self._events.get_id_log()


# ---------------------------------------------------------------------------
# DEMO LISTS  (referenced directly in the project report)
# ---------------------------------------------------------------------------

# WIN WALKTHROUGH
# Collect coffee (+5 moves), gather all 3 sacred items, perform ritual at
# King's College Circle (items dissolve → backup_usb appears), take backup
# home and drop it at the dorm.  18 movement commands; limit is 33 w/ coffee.
win_walkthrough = [
    "go east",             # 0 → 1  (Chestnut hallway)
    "take coffee",         # FREE  (coffee consumed instantly → +5 moves)
    "go north",            # 1 → 2  (Outside Chestnut)
    "go north",            # 2 → 10 (King's College Circle — ritual site)
    "go west",             # 10 → 7 (Bahen Center ground)
    "go up",               # 7 → 8  (BA3200 lecture hall)
    "take laptop charger", # FREE   +5 pts
    "go down",             # 8 → 7
    "go north",            # 7 → 3  (Sidney Smith)
    "go north",            # 3 → 5  (Robarts ground)
    "go up",               # 5 → 6  (Robarts upper stacks)
    "take usb drive",      # FREE   +5 pts
    "go down",             # 6 → 5
    "go south",            # 5 → 3
    "go west",             # 3 → 9  (Tim Hortons)
    "take lucky mug",      # FREE   +5 pts
    "go east",             # 9 → 3
    "go south",            # 3 → 7  (Bahen)
    "go east",             # 7 → 10 (King's College Circle)
    "drop usb drive",      # FREE   ritual step 1
    "drop laptop charger", # FREE   ritual step 2
    "drop lucky mug",      # FREE   ritual step 3 → RITUAL COMPLETE, backup_usb spawns
    "take backup_usb",     # FREE   +50 pts
    "go south",            # 10 → 2
    "go south",            # 2 → 1
    "go west",             # 1 → 0  (dorm)
    "drop backup_usb",     # FREE   +100 pts → WIN
]

# LOSE DEMO
# Exhaust the move limit (28) without completing the game.
lose_demo = ["go east", "go west"] * 14   # 28 moves exactly → limit reached

# INVENTORY DEMO
# Walk to Bahen lecture hall and pick up the Laptop Charger.
# Demonstrates pick-up and inventory tracking.
inventory_demo = [
    "go east",             # 0 → 1
    "go north",            # 1 → 2
    "go north",            # 2 → 10
    "go west",             # 10 → 7 (Bahen)
    "go up",               # 7 → 8  (BA3200)
    "take laptop charger", # pick up item
    "inventory",           # show inventory
]

# SCORES DEMO
# Walk to Robarts stacks and pick up the USB Drive (first score increase: +5).
scores_demo = [
    "go east",             # 0 → 1
    "go north",            # 1 → 2
    "go north",            # 2 → 10
    "go west",             # 10 → 7 (Bahen)
    "go north",            # 7 → 3  (Sidney Smith)
    "go north",            # 3 → 5  (Robarts ground)
    "go up",               # 5 → 6  (Robarts stacks)
    "take usb drive",      # +5 pts — FIRST SCORE INCREASE
    "score",               # display score
]

# ENHANCEMENTS DEMO
# Demo 1 – Summoning ritual (HIGH complexity):
#   Collect all 3 items and drop them at King's College Circle.
# Demo 2 – Dynamic stage messages (HIGH complexity):
#   Visit King's College Circle at different stages to see different messages.
# Demo 3 – Keypad puzzle (MEDIUM complexity):
#   Enter the correct 4-digit code (1827) to unlock the server room.
enhancements_demo = [
    # Stage messages: visit circle early (prints "alive / waiting" message)
    "go east",             # 0 → 1
    "go north",            # 1 → 2
    "go north",            # 2 → 10 (circle — stage=start message)
    # Collect items
    "go west",             # 10 → 7 (Bahen)
    "go up",               # 7 → 8
    "take laptop charger", # SILVER CONDUCTOR
    "go down",             # 8 → 7
    "go north",            # 7 → 3
    "go north",            # 3 → 5
    "go up",               # 5 → 6
    "take usb drive",      # BLUE GUARDIAN
    "go down",             # 6 → 5
    "go south",            # 5 → 3
    "go west",             # 3 → 9
    "take lucky mug",      # GOLDEN VESSEL — all 3 collected!
    "go east",             # 9 → 3
    "go south",            # 3 → 7
    "go east",             # 7 → 10 (circle — stage=ready_ritual instructions!)
    # Ritual: drop all three
    "drop usb drive",
    "drop laptop charger",
    "drop lucky mug",      # RITUAL FIRES — items dissolve, backup_usb appears
    # Keypad puzzle: go to Bahen and enter 1827
    "go west",             # 10 → 7
    # (enter code would require interactive input; in real play: enter code → 1827)
]


# ---------------------------------------------------------------------------
# TEST RUNNER
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("RITUAL MYSTERY - Simulation Tests")
    print("=" * 60 + "\n")

    # --- WIN TEST ---
    move_count = sum(1 for c in win_walkthrough if c.startswith("go "))
    print(f"WIN  : {move_count} movement commands (limit 33 with coffee)")

    expected_win = [
        0,   # start
        1,   # go east
        1,   # take coffee
        2,   # go north
        10,  # go north
        7,   # go west
        8,   # go up
        8,   # take laptop charger
        7,   # go down
        3,   # go north
        5,   # go north
        6,   # go up
        6,   # take usb drive
        5,   # go down
        3,   # go south
        9,   # go west
        9,   # take lucky mug
        3,   # go east
        7,   # go south
        10,  # go east
        10,  # drop usb drive
        10,  # drop laptop charger
        10,  # drop lucky mug
        10,  # take backup_usb
        2,   # go south
        1,   # go south
        0,   # go west
        0,   # drop backup_usb
    ]

    sim_win = AdventureGameSimulation('game_data.json', 0, win_walkthrough)
    actual_win = sim_win.get_id_log()
    assert expected_win == actual_win, (
        f"WIN mismatch!\nExpected: {expected_win}\nActual  : {actual_win}"
    )
    print("WIN walkthrough test PASSED!\n")

    # --- LOSE TEST ---
    move_count_lose = sum(1 for c in lose_demo if c.startswith("go "))
    print(f"LOSE : {move_count_lose} movement commands (limit 28)")

    expected_lose = [0] + [1, 0] * 14
    sim_lose = AdventureGameSimulation('game_data.json', 0, lose_demo)
    actual_lose = sim_lose.get_id_log()
    assert expected_lose == actual_lose, (
        f"LOSE mismatch!\nExpected: {expected_lose}\nActual  : {actual_lose}"
    )
    print("LOSE demo test PASSED!\n")

    # --- INVENTORY DEMO TEST ---
    expected_inv = [0, 1, 2, 10, 7, 8, 8, 8]
    sim_inv = AdventureGameSimulation('game_data.json', 0, inventory_demo)
    actual_inv = sim_inv.get_id_log()
    assert expected_inv == actual_inv, (
        f"INVENTORY mismatch!\nExpected: {expected_inv}\nActual  : {actual_inv}"
    )
    print("INVENTORY demo test PASSED!\n")

    # --- SCORES DEMO TEST ---
    expected_scores = [0, 1, 2, 10, 7, 3, 5, 6, 6, 6]
    sim_scores = AdventureGameSimulation('game_data.json', 0, scores_demo)
    actual_scores = sim_scores.get_id_log()
    assert expected_scores == actual_scores, (
        f"SCORES mismatch!\nExpected: {expected_scores}\nActual  : {actual_scores}"
    )
    print("SCORES demo test PASSED!\n")

    # --- ENHANCEMENTS DEMO TEST ---
    expected_enh = [
        0,   # start
        1,   # go east
        2,   # go north
        10,  # go north (circle — stage start)
        7,   # go west
        8,   # go up
        8,   # take laptop charger
        7,   # go down
        3,   # go north
        5,   # go north
        6,   # go up
        6,   # take usb drive
        5,   # go down
        3,   # go south
        9,   # go west
        9,   # take lucky mug
        3,   # go east
        7,   # go south
        10,  # go east (circle — stage ready_ritual)
        10,  # drop usb drive
        10,  # drop laptop charger
        10,  # drop lucky mug  (ritual!)
        7,   # go west
    ]
    sim_enh = AdventureGameSimulation('game_data.json', 0, enhancements_demo)
    actual_enh = sim_enh.get_id_log()
    assert expected_enh == actual_enh, (
        f"ENHANCEMENTS mismatch!\nExpected: {expected_enh}\nActual  : {actual_enh}"
    )
    print("ENHANCEMENTS demo test PASSED!\n")

    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
