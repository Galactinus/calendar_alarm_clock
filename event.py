from datetime import date, time, datetime
import logging
from typing import Optional
import pytz

logger = logging.getLogger(__name__)


class Event:
    """Class representing a calendar event with alarm functionality."""

    def __init__(
        self,
        date_val: date,
        start_time: time,
        end_time: time,
        title: str,
        event_id: str,
        is_system_managed: bool = False,
        timezone: Optional[str] = "America/Denver",
    ) -> None:
        """Initialize an Event instance.

        Args:
            date_val: The date of the event
            start_time: The start time of the event
            end_time: The end time of the event
            title: The event title/description
            event_id: Unique identifier for the event
            is_system_managed: Whether the event is managed by the system
            timezone: The timezone for the event (defaults to Mountain Time)
        """
        self.date: date = date_val
        self.start_time: time = start_time
        self.end_time: time = end_time
        self.title: str = title
        self.event_id: str = event_id
        self.is_system_managed: bool = is_system_managed
        self.timezone: pytz.timezone = pytz.timezone(timezone)

        logger.debug(
            "Created event %s: date=%s, start=%s, end=%s, title=%s",
            event_id,
            date_val,
            start_time,
            end_time,
            title,
        )

    @classmethod
    def from_dict(cls, event_dict: dict, timezone: str = "America/Denver") -> "Event":
        """Create an Event instance from a dictionary.

        Args:
            event_dict: Dictionary containing event data
            timezone: The timezone for the event

        Returns:
            Event: A new Event instance
        """
        return cls(
            date_val=event_dict["date"],
            start_time=event_dict["start_time"],
            end_time=event_dict["end_time"],
            title=event_dict["title"],
            event_id=event_dict["event_id"],
            is_system_managed=event_dict.get("is_system_managed", False),
            timezone=timezone,
        )

    def to_dict(self) -> dict:
        """Convert the Event instance to a dictionary.

        Returns:
            dict: Dictionary representation of the event
        """
        return {
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "title": self.title,
            "event_id": self.event_id,
            "is_system_managed": self.is_system_managed,
        }

    def get_start_datetime(self) -> datetime:
        """Get the full datetime for the event start.

        Returns:
            datetime: Timezone-aware datetime for event start
        """
        dt = datetime.combine(self.date, self.start_time)
        return self.timezone.localize(dt)

    def get_end_datetime(self) -> datetime:
        """Get the full datetime for the event end.

        Returns:
            datetime: Timezone-aware datetime for event end
        """
        dt = datetime.combine(self.date, self.end_time)
        return self.timezone.localize(dt)

    def to_utc(self) -> "Event":
        """Convert the event times to UTC.

        Returns:
            Event: A new Event instance with UTC times
        """
        start_dt = self.get_start_datetime()
        end_dt = self.get_end_datetime()

        utc_start = start_dt.astimezone(pytz.UTC)
        utc_end = end_dt.astimezone(pytz.UTC)

        return Event(
            date_val=utc_start.date(),
            start_time=utc_start.time(),
            end_time=utc_end.time(),
            title=self.title,
            event_id=self.event_id,
            is_system_managed=self.is_system_managed,
            timezone="UTC",
        )

    def __str__(self) -> str:
        """String representation of the event.

        Returns:
            str: Human-readable event string
        """
        return f"Event(id={self.event_id}, date={self.date}, start={self.start_time}, end={self.end_time}, title={self.title})"

    def __lt__(self, other: "Event") -> bool:
        """Compare events for sorting.

        Args:
            other: Another Event instance to compare with

        Returns:
            bool: True if this event should sort before the other
        """
        return self.get_start_datetime() < other.get_start_datetime()
