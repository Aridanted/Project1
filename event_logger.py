"""CSC111 Project 1: Text Adventure Game - Event Logger

Instructions (READ THIS FIRST!)
===============================

This Python module contains the code for Project 1. Please consult
the project handout for instructions and details.

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
from dataclasses import dataclass
from typing import Optional


@dataclass
class Event:
    """A node representing one event in an adventure game.

    Instance Attributes:
        - id_num: Integer ID of this event's location
        - description: Long description of this event's location
        - next_command: String command which leads this event to the next event, None if this is the last game event
        - next: Event object representing the next event in the game, or None if this is the last game event
        - prev: Event object representing the previous event in the game, None if this is the first game event

    Representation Invariants:
        - self.id_num >= 0
        - self.description != ''
        - (self.next is None) == (self.next_command is None) or self.next_command is None
    """
    id_num: int
    description: str
    next_command: Optional[str] = None
    next: Optional[Event] = None
    prev: Optional[Event] = None


class EventList:
    """A linked list of game events.

    Instance Attributes:
        - first: The first Event in this list, or None if the list is empty
        - last: The last Event in this list, or None if the list is empty

    Representation Invariants:
        - (self.first is None) == (self.last is None)
        - If self.first is not None, then self.first.prev is None
        - If self.last is not None, then self.last.next is None
    """
    first: Optional[Event]
    last: Optional[Event]

    def __init__(self) -> None:
        """Initialize a new empty event list.

        >>> events = EventList()
        >>> events.first is None
        True
        >>> events.last is None
        True
        >>> events.is_empty()
        True
        """
        self.first = None
        self.last = None

    def is_empty(self) -> bool:
        """Return whether this event list is empty.

        >>> events = EventList()
        >>> events.is_empty()
        True
        >>> events.add_event(Event(1, "Start location"))
        >>> events.is_empty()
        False
        """
        return self.first is None

    def add_event(self, event: Event, command: Optional[str] = None) -> None:
        """Add the given new event to the end of this event list.

        The given command is the command which was used to reach this new event,
        or None if this is the first event in the game.

        >>> events = EventList()
        >>> event1 = Event(1, "Location 1")
        >>> events.add_event(event1)
        >>> events.first.id_num
        1
        >>> events.last.id_num
        1
        >>> event2 = Event(2, "Location 2")
        >>> events.add_event(event2, "go north")
        >>> events.last.id_num
        2
        >>> events.first.next_command
        'go north'
        >>> events.last.prev.id_num
        1

        Preconditions:
            - event is not already in this list
        """
        if self.is_empty():
            # This is the first event
            self.first = event
            self.last = event
            event.prev = None
            event.next = None
            event.next_command = None
        else:
            # Add to the end of the list
            self.last.next = event
            self.last.next_command = command
            event.prev = self.last
            event.next = None
            event.next_command = None
            self.last = event

    def remove_last_event(self) -> None:
        """Remove the last event from this event list.

        If the list is empty, do nothing.

        >>> events = EventList()
        >>> events.remove_last_event()  # Does nothing when empty
        >>> event1 = Event(1, "Location 1")
        >>> event2 = Event(2, "Location 2")
        >>> event3 = Event(3, "Location 3")
        >>> events.add_event(event1)
        >>> events.add_event(event2, "go north")
        >>> events.add_event(event3, "go east")
        >>> events.last.id_num
        3
        >>> events.remove_last_event()
        >>> events.last.id_num
        2
        >>> events.last.next_command is None
        True
        >>> events.remove_last_event()
        >>> events.last.id_num
        1
        """
        if self.is_empty():
            return
        elif self.first == self.last:
            # Only one event in the list
            self.first = None
            self.last = None
        else:
            # Multiple events in the list
            new_last = self.last.prev
            new_last.next = None
            new_last.next_command = None
            self.last = new_last

    def get_id_log(self) -> list[int]:
        """Return a list of all location IDs visited for each event in this list, in sequence.

        >>> events = EventList()
        >>> events.add_event(Event(1, "Location 1"))
        >>> events.add_event(Event(2, "Location 2"), "go east")
        >>> events.add_event(Event(3, "Location 3"), "go north")
        >>> events.get_id_log()
        [1, 2, 3]
        """
        result = []
        curr = self.first
        while curr is not None:
            result.append(curr.id_num)
            curr = curr.next
        return result

    def display_events(self) -> None:
        """Display all events in chronological order."""
        if self.is_empty():
            print("No events recorded yet.")
            return

        print("\n=== EVENT LOG ===")
        curr = self.first
        event_num = 1
        while curr is not None:
            if curr.next_command is None:
                print(f"{event_num}. Location {curr.id_num}: {curr.description[:50]}...")
            else:
                print(f"{event_num}. Location {curr.id_num}: {curr.description[:50]}... -> Command: {curr.next_command}")
            curr = curr.next
            event_num += 1
        print("=================\n")


if __name__ == "__main__":
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    })
    
