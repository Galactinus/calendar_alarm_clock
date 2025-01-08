from datetime import datetime, timedelta
from pathlib import Path
import os
import dbus
from typing import Dict, Optional, Union

class AlarmScheduler:
    def __init__(self, base_path: str = "/etc/systemd/system"):
        self.systemd_path: Path = Path(base_path)
        self.bus: dbus.SystemBus = dbus.SystemBus()
        self.systemd: dbus.proxies.ProxyObject = self.bus.get_object(
            'org.freedesktop.systemd1', 
            '/org/freedesktop/systemd1'
        )
        self.manager: dbus.proxies.Interface = dbus.Interface(
            self.systemd, 
            'org.freedesktop.systemd1.Manager'
        )

    def create_systemd_timer(self, alarm_id: str, time_spec: str) -> bool:
        """Create systemd timer and service files for an alarm
        
        Args:
            alarm_id: Unique identifier for the alarm
            time_spec: Systemd time specification string
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            service_content: str = f"""[Unit]
Description=Alarm Service {alarm_id}

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /path/to/alarm_script.py {alarm_id}

[Install]
WantedBy=multi-user.target"""

            timer_content: str = f"""[Unit]
Description=Timer for Alarm {alarm_id}

[Timer]
OnCalendar={time_spec}
Persistent=true

[Install]
WantedBy=timers.target"""

            service_file: Path = self.systemd_path / f"alarm-{alarm_id}.service"
            timer_file: Path = self.systemd_path / f"alarm-{alarm_id}.timer"

            with open(service_file, 'w') as f:
                f.write(service_content)
            with open(timer_file, 'w') as f:
                f.write(timer_content)

            os.system("systemctl daemon-reload")
            os.system(f"systemctl enable alarm-{alarm_id}.timer")
            os.system(f"systemctl start alarm-{alarm_id}.timer")
            return True
        except Exception:
            return False

    def modify_alarm_time(self, alarm_id: str, new_time_spec: str) -> bool:
        """Modify existing alarm time
        
        Args:
            alarm_id: Unique identifier for the alarm
            new_time_spec: New systemd time specification
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.system(f"systemctl stop alarm-{alarm_id}.timer")
            
            timer_file: Path = self.systemd_path / f"alarm-{alarm_id}.timer"
            
            timer_content: str = f"""[Unit]
Description=Timer for Alarm {alarm_id}

[Timer]
OnCalendar={new_time_spec}
Persistent=true

[Install]
WantedBy=timers.target"""

            with open(timer_file, 'w') as f:
                f.write(timer_content)

            os.system("systemctl daemon-reload")
            os.system(f"systemctl start alarm-{alarm_id}.timer")
            return True
        except Exception:
            return False

    def cancel_alarm(self, alarm_id: str) -> bool:
        """Cancel and remove an alarm
        
        Args:
            alarm_id: Unique identifier for the alarm
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.system(f"systemctl stop alarm-{alarm_id}.timer")
            os.system(f"systemctl disable alarm-{alarm_id}.timer")
            
            service_file: Path = self.systemd_path / f"alarm-{alarm_id}.service"
            timer_file: Path = self.systemd_path / f"alarm-{alarm_id}.timer"
            
            service_file.unlink(missing_ok=True)
            timer_file.unlink(missing_ok=True)
            
            os.system("systemctl daemon-reload")
            return True
        except Exception:
            return False

    def snooze_alarm(self, alarm_id: str, snooze_minutes: int = 9) -> bool:
        """Snooze an alarm for specified minutes
        
        Args:
            alarm_id: Unique identifier for the alarm
            snooze_minutes: Minutes to snooze
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            new_time: datetime = datetime.now() + timedelta(minutes=snooze_minutes)
            time_spec: str = new_time.strftime("%Y-%m-%d %H:%M:00")
            return self.modify_alarm_time(alarm_id, time_spec)
        except Exception:
            return False

    def get_alarm_status(self, alarm_id: str) -> Dict[str, Union[bool, Optional[str]]]:
        """Get status of an alarm timer
        
        Args:
            alarm_id: Unique identifier for the alarm
            
        Returns:
            Dict containing active status and next trigger time
        """
        try:
            unit_path = self.manager.GetUnit(f"alarm-{alarm_id}.timer")
            unit = self.bus.get_object('org.freedesktop.systemd1', unit_path)
            props = dbus.Interface(unit, 'org.freedesktop.DBus.Properties')
            
            state: str = props.Get('org.freedesktop.systemd1.Unit', 'ActiveState')
            next_trigger: int = props.Get('org.freedesktop.systemd1.Timer', 'NextElapseUSecRealtime')
            
            return {
                'active': state == 'active',
                'next_trigger': datetime.fromtimestamp(next_trigger / 1000000).isoformat()
            }
        except Exception:
            return {'active': False, 'next_trigger': None}




