"""Domain models for ZZZ Bot.

Type-safe data classes representing business entities with validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

# ============================================================================
# ENUMS
# ============================================================================


class MissionStatus(str, Enum):
    """Mission completion status."""

    FINISHED = "Finished"
    UNFINISHED = "Unfinished"
    REWARD = "Reward"


class CheckInStatus(str, Enum):
    """Check-in result status."""

    SUCCESS = "Login Success"
    FAILED = "Login Failed"
    LINK_NOT_OPENED = "Link isn't opened"


class ButtonState(str, Enum):
    """Button visual states detected via image comparison."""

    FINISHED = "Finished"
    UNFINISHED = "Unfinished"
    REWARD = "Reward"
    UNKNOWN = "unknown"


class ItemAvailability(str, Enum):
    """Shopping item availability status."""

    EXCHANGE = "Exchange"
    LIMIT_REACHED = "Limit Reached"
    COUNTDOWN = "countdown"  # When item shows timer


# ============================================================================
# MISSION MODELS
# ============================================================================


@dataclass
class MissionRecord:
    """Individual mission completion record.

    Attributes:
        name: Mission display name
        state: Completion status (Finished/Unfinished)
    """

    name: str
    state: str  # Will be MissionStatus in the future

    def is_finished(self) -> bool:
        """Check if mission is completed."""
        return self.state == MissionStatus.FINISHED.value


@dataclass
class DailyMissionReport:
    """Daily mission completion report.

    Attributes:
        day: Date in dd/mm/yyyy format
        check_in: Check-in status
        missions: List of individual mission records
    """

    day: str
    check_in: str  # Will be CheckInStatus in the future
    missions: List[MissionRecord] = field(default_factory=list)

    @classmethod
    def create_for_today(cls) -> "DailyMissionReport":
        """Create a new report for today's date."""
        today_str = datetime.now().strftime("%d/%m/%Y")
        return cls(
            day=today_str,
            check_in=CheckInStatus.LINK_NOT_OPENED.value,
            missions=[],
        )

    def add_mission(self, name: str, state: str) -> None:
        """Add or update a mission record."""
        # Check if mission already exists
        for mission in self.missions:
            if mission.name == name:
                mission.state = state
                return
        # Add new mission
        self.missions.append(MissionRecord(name=name, state=state))

    def get_mission(self, name: str) -> Optional[MissionRecord]:
        """Get mission record by name."""
        return next((m for m in self.missions if m.name == name), None)


# ============================================================================
# SHOPPING MODELS
# ============================================================================


@dataclass
class ShoppingItem:
    """Shopping item with availability and pricing.

    Attributes:
        name: Item display name
        price: Cost in points
        inventory: Available quantity (0 if on cooldown)
        available: Availability status or return time
    """

    name: str
    price: int
    inventory: int
    available: str  # "Exchange", "Limit Reached", or "HH:MM DD/MM/YY"

    def is_available_for_exchange(self) -> bool:
        """Check if item can be exchanged now."""
        return self.available == ItemAvailability.EXCHANGE.value

    def is_on_cooldown(self) -> bool:
        """Check if item is on cooldown timer."""
        # Check if available field matches time format
        return "/" in self.available and ":" in self.available

    def is_limit_reached(self) -> bool:
        """Check if purchase limit reached."""
        return self.available == ItemAvailability.LIMIT_REACHED.value


@dataclass
class EventDuration:
    """Shopping event duration.

    Attributes:
        start: Start date in dd/mm format
        end: End date in dd/mm format
    """

    start: str  # Format: "dd/mm"
    end: str  # Format: "dd/mm"

    def is_active(self) -> bool:
        """Check if current time is within event duration."""
        try:
            current_year = datetime.now().year
            start_date = datetime.strptime(self.start, "%d/%m").replace(year=current_year)
            end_date = datetime.strptime(self.end, "%d/%m").replace(year=current_year)
            current_time = datetime.now()
            return start_date <= current_time <= end_date
        except (ValueError, TypeError):
            return False


@dataclass
class ShoppingData:
    """Complete shopping data structure.

    Attributes:
        point: Current point balance
        duration: Event duration
        items: Dictionary of available items (name -> ShoppingItem)
        selected: List of item names selected for auto-purchase
        purchased: List of item names already purchased
        hunt: List of item names in hunt mode
    """

    point: int
    duration: EventDuration
    items: dict[str, ShoppingItem]
    selected: List[str] = field(default_factory=list)
    purchased: List[str] = field(default_factory=list)
    hunt: List[str] = field(default_factory=list)

    def get_item(self, name: str) -> Optional[ShoppingItem]:
        """Get shopping item by name."""
        return self.items.get(name)

    def get_selected_items(self) -> List[ShoppingItem]:
        """Get list of selected ShoppingItem objects."""
        return [self.items[name] for name in self.selected if name in self.items]

    def get_hunt_items(self) -> List[ShoppingItem]:
        """Get list of hunt mode ShoppingItem objects."""
        return [self.items[name] for name in self.hunt if name in self.items]

    def mark_as_purchased(self, item_name: str) -> None:
        """Add item to purchased list."""
        if item_name not in self.purchased:
            self.purchased.append(item_name)


# ============================================================================
# REDEMPTION MODELS
# ============================================================================


@dataclass
class RedemptionCode:
    """Redemption code record.

    Attributes:
        item_name: Associated item name
        code: Redemption code string
        day: Timestamp when code was generated
        state: Success/failure status
    """

    item_name: str
    code: str
    day: str  # Format: "HH:MM dd/mm/yyyy"
    state: bool  # True = success, False = failure

    @classmethod
    def create_now(cls, item_name: str, code: str, state: bool) -> "RedemptionCode":
        """Create a redemption code record with current timestamp."""
        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        return cls(item_name=item_name, code=code, day=timestamp, state=state)

    def is_older_than_days(self, days: int) -> bool:
        """Check if redemption code is older than specified days."""
        try:
            code_date = datetime.strptime(self.day, "%H:%M %d/%m/%Y")
            current_date = datetime.now()
            age = current_date - code_date
            return age.days > days
        except ValueError:
            return False


# ============================================================================
# HUNT MODE MODELS
# ============================================================================


@dataclass
class HuntTarget:
    """Hunt mode target item.

    Attributes:
        name: Item name
        scheduled_time: When hunt should execute
        price: Item cost
        inventory: Current inventory
    """

    name: str
    scheduled_time: str  # Format: "HH:MM dd/mm/yy"
    price: int
    inventory: int


@dataclass
class HuntInfo:
    """Hunt mode status information.

    Attributes:
        enabled: Whether hunt mode is active
        hunt_items: List of target items
        next_hunt_time: Next scheduled hunt execution time
    """

    enabled: bool
    hunt_items: List[HuntTarget]
    next_hunt_time: Optional[str] = None  # Format: "HH:MM dd/mm/yy"
