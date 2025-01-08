from datetime import datetime, timedelta
from typing import Dict, Optional, Union
import requests
import json


class AlarmSchedulerPythonClient:
    def __init__(self, host="localhost", port=8080):
        """Initialize the client for Python-based Alarm Scheduler.

        Args:
            host: Hostname of the scheduler service
            port: Port number of the scheduler service
        """
        self.base_url = f"http://{host}:{port}"

    def create_systemd_timer(self, alarm_id: str, time_spec: str, command: str) -> bool:
        """Schedule a new alarm task.

        Args:
            alarm_id: Unique identifier for the alarm
            time_spec: Time specification in "YYYY-MM-DD HH:MM:SS" format
            command: The command to execute when alarm triggers

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/create",
                json={
                    "alarm_id": alarm_id,
                    "time_spec": time_spec,
                    "command": command,
                },
            )
            return response.status_code == 200
        except Exception:
            return False

    def modify_alarm_time(self, alarm_id: str, new_time_spec: str) -> bool:
        """Modify the time of an existing alarm.

        Args:
            alarm_id: Unique identifier for the alarm
            new_time_spec: New time specification

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/modify",
                json={
                    "alarm_id": alarm_id,
                    "new_time_spec": new_time_spec,
                },
            )
            return response.status_code == 200
        except Exception:
            return False

    def cancel_alarm(self, alarm_id: str) -> bool:
        """Cancel an alarm task.

        Args:
            alarm_id: Unique identifier for the alarm

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/cancel",
                json={"alarm_id": alarm_id},
            )
            return response.status_code == 200
        except Exception:
            return False

    def snooze_alarm(self, alarm_id: str, snooze_seconds: int = 540) -> bool:
        """Snooze an alarm for specified seconds.

        Args:
            alarm_id: Unique identifier for the alarm
            snooze_seconds: Seconds to snooze (default 540 seconds = 9 minutes)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/snooze",
                json={
                    "alarm_id": alarm_id,
                    "snooze_seconds": snooze_seconds,
                },
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_alarm_status(self, alarm_id: str) -> Dict[str, Union[bool, Optional[str]]]:
        """Get the status of an alarm.

        Args:
            alarm_id: Unique identifier for the alarm

        Returns:
            Dict containing active status and next trigger time
        """
        try:
            response = requests.get(f"{self.base_url}/status/{alarm_id}")
            if response.status_code == 200:
                return response.json()
            return {"active": False, "next_trigger": None}
        except Exception:
            return {"active": False, "next_trigger": None}
