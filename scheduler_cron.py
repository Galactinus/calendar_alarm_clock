from datetime import datetime, timedelta
from pathlib import Path
import os
import subprocess
from typing import Dict, Optional, Union
import tempfile


class AlarmSchedulerCron:
    def __init__(self):
        """Initialize the AlarmScheduler using cron."""
        self.temp_dir = Path(tempfile.gettempdir()) / "alarm_scripts"
        self.temp_dir.mkdir(exist_ok=True)

    def _get_crontab(self) -> str:
        """Get current crontab content."""
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else ""
        except subprocess.SubprocessError:
            return ""

    def _write_crontab(self, content: str) -> bool:
        """Write content to crontab."""
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
                temp.write(content)
                temp_path = temp.name

            result = subprocess.run(
                ["crontab", temp_path], capture_output=True, text=True
            )
            os.unlink(temp_path)
            return result.returncode == 0
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return False

    def create_systemd_timer(self, alarm_id: str, time_spec: str, command: str) -> bool:
        """Create a cron job for an alarm.

        Args:
            alarm_id: Unique identifier for the alarm
            time_spec: Time specification in "YYYY-MM-DD HH:MM:SS" format
            command: The command to execute when alarm triggers

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert time_spec to cron format
            dt = datetime.strptime(time_spec, "%Y-%m-%d %H:%M:%S")
            cron_time = f"{dt.minute} {dt.hour} {dt.day} {dt.month} *"

            # Create the script that will be executed
            script_path = self.temp_dir / f"alarm-{alarm_id}.sh"
            script_content = f"""#!/bin/bash
{command}
# Remove this script and its cron job after execution
rm -f {script_path}
(crontab -l | grep -v "alarm-{alarm_id}") | crontab -
"""
            with open(script_path, "w") as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)

            # Add to crontab
            current_crontab = self._get_crontab()
            new_job = f"{cron_time} {script_path} # alarm-{alarm_id}"
            new_crontab = current_crontab + new_job + "\n"

            return self._write_crontab(new_crontab)
        except Exception:
            return False

    def modify_alarm_time(self, alarm_id: str, new_time_spec: str) -> bool:
        """Modify existing alarm time.

        Args:
            alarm_id: Unique identifier for the alarm
            new_time_spec: New time specification

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get current crontab
            current_crontab = self._get_crontab()
            lines = current_crontab.splitlines()

            # Find and update the relevant line
            dt = datetime.strptime(new_time_spec, "%Y-%m-%d %H:%M:%S")
            cron_time = f"{dt.minute} {dt.hour} {dt.day} {dt.month} *"

            new_lines = []
            for line in lines:
                if f"alarm-{alarm_id}" in line:
                    script_path = line.split()[-2]  # Get script path
                    new_lines.append(f"{cron_time} {script_path} # alarm-{alarm_id}")
                else:
                    new_lines.append(line)

            return self._write_crontab("\n".join(new_lines) + "\n")
        except Exception:
            return False

    def cancel_alarm(self, alarm_id: str) -> bool:
        """Cancel and remove an alarm.

        Args:
            alarm_id: Unique identifier for the alarm

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove from crontab
            current_crontab = self._get_crontab()
            new_crontab = (
                "\n".join(
                    line
                    for line in current_crontab.splitlines()
                    if f"alarm-{alarm_id}" not in line
                )
                + "\n"
            )

            # Remove the script file
            script_path = self.temp_dir / f"alarm-{alarm_id}.sh"
            if script_path.exists():
                script_path.unlink()

            return self._write_crontab(new_crontab)
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
            new_time = datetime.now() + timedelta(seconds=snooze_seconds)
            time_spec = new_time.strftime("%Y-%m-%d %H:%M:%S")
            return self.modify_alarm_time(alarm_id, time_spec)
        except Exception:
            return False

    def get_alarm_status(self, alarm_id: str) -> Dict[str, Union[bool, Optional[str]]]:
        """Get status of an alarm.

        Args:
            alarm_id: Unique identifier for the alarm

        Returns:
            Dict containing active status and next trigger time
        """
        try:
            current_crontab = self._get_crontab()
            for line in current_crontab.splitlines():
                if f"alarm-{alarm_id}" in line:
                    # Parse cron time
                    parts = line.split()
                    minute, hour, day, month, _ = parts[:5]

                    # Create datetime for next occurrence
                    now = datetime.now()
                    next_time = datetime(
                        year=now.year,
                        month=int(month),
                        day=int(day),
                        hour=int(hour),
                        minute=int(minute),
                    )

                    # If the time is in the past, add a year
                    if next_time < now:
                        next_time = next_time.replace(year=now.year + 1)

                    return {"active": True, "next_trigger": next_time.isoformat()}

            return {"active": False, "next_trigger": None}
        except Exception:
            return {"active": False, "next_trigger": None}
