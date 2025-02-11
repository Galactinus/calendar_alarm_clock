import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlManager import sqlManager
from ical_manager import IcalManager
from config_manager import JsonConfig
from scheduler_python_client import AlarmSchedulerPythonClient

class CalendarSyncService:
    def __init__(self, config_path: str):
        """Initialize the core alarm system service."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        
        self.config = JsonConfig(config_path)
        self.alarm_client = AlarmSchedulerPythonClient()
        self.alarm_client.host = self.config.scheduler_host
        self.alarm_client.port = self.config.scheduler_port
        
        # Initialize database with emergency retention period
        self.db = sqlManager(self.config.database_path)
        self.last_sync = datetime.min
        
    def _trigger_emergency_alarm(self, event: Dict[str, Any]) -> None:
        """Immediately trigger a missed alarm with escalation pattern."""
        self.logger.error("EMERGENCY: Triggering missed alarm %s", event["event_id"])
        # TODO: Implement hardware activation sequence
        self.alarm_client.create_systemd_timer(
            alarm_id=event["event_id"] + "_emergency",
            time_spec=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            command="EmergencyTrigger",
            plugin_list=["sound", "lights", "vibration"]
        )

    def _check_missed_alarms(self) -> None:
        """Critical system: Check for alarms that should have fired during downtime."""
        self.logger.debug("Checking for missed alarms")
        cursor = self.db.conn.cursor()
        try:
            current_time = datetime.now() - timedelta(minutes=1)
            cursor.execute("""
                SELECT * FROM events 
                WHERE date || ' ' || start_time < ?
                AND triggered = 0
            """, (current_time.strftime('%Y-%m-%d %H:%M:%S'),))
            
            for event in cursor.fetchall():
                self.logger.critical("Detected missed alarm: %s", event["event_id"])
                self._trigger_emergency_alarm(event)
                # Mark as triggered to prevent repeat
                cursor.execute("""
                    UPDATE events SET triggered = 1 
                    WHERE event_id = ?
                """, (event["event_id"],))
            self.db.conn.commit()
        except Exception as e:
            self.logger.error("Failed missed alarm check: %s", e, exc_info=True)
            self.db.conn.rollback()

    def _sync_calendar_events(self) -> None:
        """Synchronize calendar events with scheduler and database."""
        self.logger.info("Starting calendar synchronization")
        try:
            # Get current active calendar-based events
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT event_id, date, start_time 
                FROM events 
                WHERE source = 'ical' 
                AND status = 'active'
            """)
            existing_events = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

            # Process new events from all calendars
            new_events = []
            for calendar in self.config.calendars:
                ical = IcalManager(calendar, self.config)
                new_events += ical.fetch_and_parse_events()

            # Update database with merge strategy
            for event in new_events:
                event_id = event["event_id"]
                alarm_time = f"{event['date']} {event['start_time']}"
                
                # Check for existing snoozed system events
                cursor.execute("""
                    SELECT 1 FROM events 
                    WHERE original_event_id = ? 
                    AND source = 'system'
                    AND status = 'snoozed'
                """, (event_id,))
                
                if cursor.fetchone():
                    # Mark original ical event as triggered
                    cursor.execute("""
                        UPDATE events SET status = 'triggered'
                        WHERE event_id = ?
                    """, (event_id,))
                    continue  # Skip scheduling new alarm
                
                # Proceed with normal insert/update
                cursor.execute("""
                    INSERT OR REPLACE INTO events 
                    (event_id, date, start_time, end_time, title, source, original_time, status)
                    VALUES (?, ?, ?, ?, ?, 'ical', ?, 
                        COALESCE(
                            (SELECT status FROM events WHERE event_id = ?),
                            'active'
                        ))
                """, (
                    event_id,
                    event["date"],
                    event["start_time"],
                    event["end_time"],
                    event["title"],
                    alarm_time,
                    event_id
                ))

            # Identify and cancel deleted events that haven't triggered
            current_ids = {e["event_id"] for e in new_events}
            to_cancel = existing_events.keys() - current_ids
            
            for event_id in to_cancel:
                cursor.execute("""
                    UPDATE events SET status = 'canceled'
                    WHERE event_id = ? 
                    AND source = 'ical'
                    AND status NOT IN ('triggered', 'snoozed')
                """, (event_id,))
                self.alarm_client.cancel_alarm(event_id)

            self.db.conn.commit()

            # Schedule new/changed alarms
            for event in new_events:
                event_id = event["event_id"]
                stored_time = existing_events.get(event_id)
                alarm_time = f"{event['date']} {event['start_time']}"
                
                if stored_time != (event["date"], event["start_time"]):
                    # Reschedule if time changed
                    self.alarm_client.modify_alarm_time(event_id, alarm_time)
                elif not stored_time:
                    # New event
                    self.alarm_client.create_systemd_timer(
                        alarm_id=event_id,
                        time_spec=alarm_time,
                        command=f"Trigger {event['title']}",
                        plugin_list=self.config.default_plugins
                    )

        except Exception as e:
            self.logger.error("Calendar sync failed: %s", e, exc_info=True)

    def run_service(self) -> None:
        """Main service loop with reliability enhancements."""
        self.logger.info("Starting UltiClock Core Service")
        self._check_missed_alarms()  # Critical first action
        
        while True:
            try:
                self._sync_calendar_events()
                # Maintain minimum 15m sync interval with hardware button override
                next_sync = self.last_sync + timedelta(minutes=15)
                while datetime.now() < next_sync:
                    time.sleep(1)
                    # TODO: Add hardware interrupt check for manual sync
                    
            except KeyboardInterrupt:
                self.logger.info("Service shutdown requested")
                break
            except Exception as e:
                self.logger.critical("Unhandled service error: %s", e, exc_info=True)
                # TODO: Trigger hardware emergency reset sequence
                time.sleep(60)  # Prevent tight failure loop

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    service = CalendarSyncService("ulticlock.config")
    service.run_service() 