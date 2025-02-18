import sqlite3
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List
import pytz

# Type aliases
EventDict = Dict[str, Any]
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

    def store_alarms(self, events: List[EventDict]) -> int:
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute("DELETE FROM events")
        self.conn.commit()

        for event in events:
            # Convert local time to UTC for storage
            date_str = event["date"]
            time_str = event["start_time"]
            end_time_str = event["end_time"]

            # Parse datetime in configured timezone
            local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            local_dt = self.timezone.localize(local_dt)

            # Convert to UTC for storage
            utc_dt = local_dt.astimezone(pytz.UTC)
            utc_end = datetime.strptime(
                f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M:%S"
            )
            utc_end = self.timezone.localize(utc_end).astimezone(pytz.UTC)

            cursor.execute(
                """INSERT INTO events 
                   (event_id, date, start_time, end_time, title, is_system_managed) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(event["event_id"]),
                    utc_dt.strftime("%Y-%m-%d"),
                    utc_dt.strftime("%H:%M:%S"),
                    utc_end.strftime("%H:%M:%S"),
                    str(event["title"]),
                    0,
                ),
            )
        self.conn.commit()

    def get_next_alarm(self) -> Optional[EventDict]:
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

            # Convert UTC times back to configured timezone
            start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M:%S")
            start_dt = pytz.UTC.localize(start_dt)
            local_start = start_dt.astimezone(self.timezone)

            end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M:%S")
            end_dt = pytz.UTC.localize(end_dt)
            local_end = end_dt.astimezone(self.timezone)

            return {
                "event_id": event_id,
                "date": local_start.strftime("%Y-%m-%d"),
                "start_time": local_start.strftime("%H:%M:%S"),
                "end_time": local_end.strftime("%H:%M:%S"),
                "title": title,
                "is_system_managed": bool(is_system_managed),
            }
        return None

    def mark_system_managed(
        self, event_id: str, is_system_managed: bool = True
    ) -> bool:
        """Mark an event as system-managed in the database.

        Args:
            event_id: The unique identifier of the event

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            cursor: sqlite3.Cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE events SET is_system_managed = ? WHERE event_id = ?",
                (is_system_managed, str(event_id)),
            )
            self.conn.commit()
            logger.debug(
                "Marked event %s, system-managed: %s", event_id, is_system_managed
            )
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(
                "Error marking event %s, system-managed: %s: %s",
                event_id,
                is_system_managed,
                e,
            )
            return False

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
