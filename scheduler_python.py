from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import queue
import subprocess
from typing import Dict, Optional, Union, List
import heapq
import logging
from dataclasses import dataclass
import tempfile
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from plugins.plugin_manager import PluginManager

# Add near the top after imports
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass(order=True)
class AlarmTask:
    trigger_time: datetime
    alarm_id: str
    command: str
    plugin_list: Optional[List[str]] = None

    def __post_init__(self):
        # Make sure alarm_id isn't used in sorting
        self.sort_index = self.trigger_time


class AlarmSchedulerPython:
    def __init__(
        self, host="localhost", port=8080, plugins_dir: Path = Path("plugins")
    ):
        """Initialize the Python-based Alarm Scheduler."""
        logger.debug(
            "Initializing scheduler on %s:%s with plugins from %s",
            host,
            port,
            plugins_dir,
        )
        self.temp_dir = Path(tempfile.gettempdir()) / "alarm_scripts"
        self.temp_dir.mkdir(exist_ok=True)

        # Initialize task management
        self.tasks: List[AlarmTask] = []
        self.task_lock = threading.Lock()
        self.task_event = threading.Event()

        # Start scheduler thread
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True
        )
        self.scheduler_thread.start()

        # Start API server
        self.server = AlarmAPIServer((host, port), AlarmRequestHandler, scheduler=self)
        self.server_thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.server_thread.start()

        # Initialize plugin system
        self.plugin_manager = PluginManager(plugins_dir)
        self.plugin_manager.discover_plugins()

        logger.info("Alarm scheduler started on %s:%s", host, port)

    def _scheduler_loop(self):
        """Main scheduler loop that checks and executes tasks."""
        logger.debug("Starting scheduler loop")
        while self.running:
            now = datetime.now()
            with self.task_lock:
                if self.tasks:
                    logger.debug(
                        "Current time: %s, Next task: %s",
                        now,
                        self.tasks[0].trigger_time,
                    )
                while self.tasks and self.tasks[0].trigger_time <= now:
                    task = heapq.heappop(self.tasks)
                    logger.info("Task %s due for execution", task.alarm_id)
                    threading.Thread(target=self._execute_task, args=(task,)).start()
            time.sleep(1)
        logger.debug("Scheduler loop ended")

    def _execute_task(self, task: AlarmTask):
        """Execute a task using the plugin system."""
        logger.info("Executing task %s", task.alarm_id)
        try:
            self.plugin_manager.execute_all(task.alarm_id, task.plugin_list)

            # Update database status
            with self.db.conn:
                self.db.conn.execute(
                    """
                    UPDATE events SET status = 'triggered'
                    WHERE event_id = ?
                """,
                    (task.alarm_id,),
                )

        except Exception as e:
            logger.error("Execution failed: %s", e, exc_info=True)

    def _cleanup_task(self, alarm_id: str):
        """Clean up any resources associated with a task."""
        script_path = self.temp_dir / f"alarm-{alarm_id}.sh"
        if script_path.exists():
            script_path.unlink()

    def create_systemd_timer(self, alarm_id: str, time_spec: str, command: str) -> bool:
        """Schedule a new alarm task."""
        try:
            trigger_time = datetime.strptime(time_spec, "%Y-%m-%d %H:%M:%S")
            task = AlarmTask(trigger_time, alarm_id, command)

            with self.task_lock:
                # Remove any existing task with same ID
                self.tasks = [t for t in self.tasks if t.alarm_id != alarm_id]
                heapq.heappush(self.tasks, task)
                heapq.heapify(self.tasks)

            self.task_event.set()
            return True
        except Exception as e:
            logger.error("Error creating alarm %s: %s", alarm_id, e)
            return False

    def modify_alarm_time(self, alarm_id: str, new_time_spec: str) -> bool:
        """Modify the time of an existing alarm."""
        try:
            new_time = datetime.strptime(new_time_spec, "%Y-%m-%d %H:%M:%S")

            with self.task_lock:
                # Find the existing task
                old_task = None
                for task in self.tasks:
                    if task.alarm_id == alarm_id:
                        old_task = task
                        break

                if old_task:
                    # Create new task with updated time
                    new_task = AlarmTask(new_time, alarm_id, old_task.command)
                    self.tasks.remove(old_task)
                    heapq.heappush(self.tasks, new_task)
                    heapq.heapify(self.tasks)
                    return True

            return False
        except Exception as e:
            logger.error("Error modifying alarm %s: %s", alarm_id, e)
            return False

    def cancel_alarm(self, alarm_id: str) -> bool:
        """Cancel an alarm task."""
        try:
            with self.task_lock:
                self.tasks = [t for t in self.tasks if t.alarm_id != alarm_id]
                heapq.heapify(self.tasks)

            self._cleanup_task(alarm_id)
            return True
        except Exception as e:
            logger.error("Error canceling alarm %s: %s", alarm_id, e)
            return False

    def snooze_alarm(self, alarm_id: str, snooze_seconds: int = 540) -> bool:
        """Snooze an alarm for specified seconds."""
        try:
            with self.task_lock:
                original_task = next(
                    (t for t in self.tasks if t.alarm_id == alarm_id), None
                )

            if original_task:
                new_time = datetime.now() + timedelta(seconds=snooze_seconds)
                new_id = f"{alarm_id}_snooze_{int(new_time.timestamp())}"

                # Create new snooze task
                new_task = AlarmTask(
                    trigger_time=new_time,
                    alarm_id=new_id,
                    command=original_task.command,
                    plugin_list=original_task.plugin_list,
                )

                # Update database with original event reference
                self.db.conn.execute(
                    """
                    INSERT INTO events 
                    (event_id, date, start_time, source, status, original_event_id)
                    VALUES (?, ?, ?, 'system', 'snoozed', ?)
                """,
                    (
                        new_id,
                        new_time.date().isoformat(),
                        new_time.time().isoformat(),
                        alarm_id,  # Store original event ID
                    ),
                )
                self.db.conn.commit()

                # Schedule new task
                with self.task_lock:
                    heapq.heappush(self.tasks, new_task)

                # Mark original as triggered
                self.cancel_alarm(alarm_id)
                return True
            return False
        except Exception as e:
            logger.error("Error snoozing alarm %s: %s", alarm_id, e)
            return False

    def get_alarm_status(self, alarm_id: str) -> Dict[str, Union[bool, Optional[str]]]:
        """Get the status of an alarm."""
        try:
            with self.task_lock:
                for task in self.tasks:
                    if task.alarm_id == alarm_id:
                        return {
                            "active": True,
                            "next_trigger": task.trigger_time.isoformat(),
                        }

            return {"active": False, "next_trigger": None}
        except Exception as e:
            logger.error("Error getting alarm status %s: %s", alarm_id, e)
            return {"active": False, "next_trigger": None}

    def shutdown(self):
        """Shutdown the scheduler and cleanup plugins."""
        self.running = False
        self.plugin_manager.cleanup()
        self.server.shutdown()
        self.server.server_close()


class AlarmRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for creating/modifying alarms."""
        content_length = int(self.headers["Content-Length"])
        post_data = json.loads(self.rfile.read(content_length))

        path = urllib.parse.urlparse(self.path).path
        scheduler = self.server.scheduler

        result = False
        if path == "/create":
            result = scheduler.create_systemd_timer(
                post_data["alarm_id"], post_data["time_spec"], post_data["command"]
            )
        elif path == "/modify":
            result = scheduler.modify_alarm_time(
                post_data["alarm_id"], post_data["new_time_spec"]
            )
        elif path == "/cancel":
            result = scheduler.cancel_alarm(post_data["alarm_id"])
        elif path == "/snooze":
            result = scheduler.snooze_alarm(
                post_data["alarm_id"], post_data.get("snooze_seconds", 540)
            )

        self.send_response(200 if result else 400)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"success": result}).encode())

    def do_GET(self):
        """Handle GET requests for alarm status."""
        path_parts = urllib.parse.urlparse(self.path).path.split("/")
        if len(path_parts) >= 3 and path_parts[1] == "status":
            alarm_id = path_parts[2]
            status = self.server.scheduler.get_alarm_status(alarm_id)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()


class AlarmAPIServer(HTTPServer):
    def __init__(self, server_address, handler_class, scheduler):
        super().__init__(server_address, handler_class)
        self.scheduler = scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler = AlarmSchedulerPython()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
