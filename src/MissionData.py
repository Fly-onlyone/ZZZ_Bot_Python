from dataclasses import dataclass
from typing import List

@dataclass
class Mission:
    name: str
    state: str


@dataclass
class DayEntry:
    day: str
    check_in: str
    missions: List[Mission]
