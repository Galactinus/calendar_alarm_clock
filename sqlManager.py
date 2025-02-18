import sqlite3
from datetime import datetime, timedelta
import logging
from typing import Optional, List
import pytz
from event import Event

# Get logger for this module
logger = logging.getLogger(__name__)


class sqlManager:
    def __init__(self, db_file: str, timezone: str) -> None:
        self.db_file: str = db_file
        self.timezone: pytz.timezone = pytz.timezone(timezone)
        try:
            self.conn: sqlite3.Connection = sqlite3.connect(db_file)
        except sqlite3.OperationalError:
            logger.error("Unable to open database location", exc_info=True)
            raise

        self.create_table()

    def create_table(self) -> None:
        # Create the events table if it doesn't exist
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                date TEXT,
                start_time TEXT,
                end_time TEXT,
                title TEXT,
                is_system_managed INTEGER DEFAULT 0  -- 0 = false, 1 = true
            )
        """)
        self.conn.commit()

    def store_alarms(self, events: List[Event]) -> int:
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute("DELETE FROM events")
        self.conn.commit()

        for event in events:
            # Convert to UTC for storage
            utc_event = event.to_utc()

            cursor.execute(
                """INSERT INTO events 
                   (event_id, date, start_time, end_time, title, is_system_managed) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    utc_event.event_id,
                    utc_event.date.strftime("%Y-%m-%d"),
                    utc_event.start_time.strftime("%H:%M:%S"),
                    utc_event.end_time.strftime("%H:%M:%S"),
                    utc_event.title,
                    1 if utc_event.is_system_managed else 0,
                ),
            )
        self.conn.commit()

    def get_next_alarm(self) -> Optional[Event]:
        """Get the next upcoming alarm in configured timezone."""
        cursor: sqlite3.Cursor = self.conn.cursor()

        # Get current time in UTC
        current_time = datetime.now(pytz.UTC)
        current_time = current_time - timedelta(minutes=1)
        current_datetime = current_time.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            SELECT * FROM events 
            WHERE date || ' ' || start_time >= ? 
            ORDER BY date || ' ' || start_time 
            LIMIT 1
            """,
            (current_datetime,),
        )

        row = cursor.fetchone()
        if row:
            event_id, date, start_time, end_time, title, is_system_managed = row

            # Create UTC event
            utc_event = Event(
                date_val=datetime.strptime(date, "%Y-%m-%d").date(),
                start_time=datetime.strptime(start_time, "%H:%M:%S").time(),
                end_time=datetime.strptime(end_time, "%H:%M:%S").time(),
                title=title,
                event_id=event_id,
                is_system_managed=bool(is_system_managed),
                timezone="UTC",
            )

            # Convert to local timezone
            local_event = Event(
                date_val=utc_event.get_start_datetime()
                .astimezone(self.timezone)
                .date(),
                start_time=utc_event.get_start_datetime()
                .astimezone(self.timezone)
                .time(),
                end_time=utc_event.get_end_datetime().astimezone(self.timezone).time(),
                title=utc_event.title,
                event_id=utc_event.event_id,
                is_system_managed=utc_event.is_system_managed,
                timezone=self.timezone.zone,
            )

            return local_event
        return None

    def close(self) -> None:
        self.conn.close()


if __name__ == "__main__":
    # Example usage
    events = []

    db_file = "events.db"
    timezone = "America/Denver"
    manager = sqlManager(db_file, timezone)
    manager.store_alarms(events)
    next_alarm = manager.get_next_alarm()
    print("Next alarm:", next_alarm)
    manager.close()
