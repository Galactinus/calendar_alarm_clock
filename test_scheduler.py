import time
import os
import sys
from datetime import datetime, timedelta
from scheduler_python_client import AlarmSchedulerPythonClient
import random


def check_root():
    """Check if the script is running as root."""
    if os.geteuid() != 0:
        print("This script must be run as root. Please use 'sudo' or run as root.")
        # sys.exit(1)


def create_alarm_script(message: str, message_id: str) -> str:
    """Create a temporary Python script that will be executed by the alarm.

    Returns:
        str: Path to the created script
    """
    script_content = f"""#!/usr/bin/env python3
import os
import sys

# Send the message
os.system("wall '{message}'")

# Clean up this script
os.remove(sys.argv[0])
"""
    # Generate a random number between 10000 and 99999
    script_path = f"/tmp/alarm_notification_{message_id}.py"

    with open(script_path, "w") as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)  # Make the script executable
    return script_path


def test_schedule_alarm():
    """Test scheduling an alarm."""
    alarm_id = "test-schedule" + str(random.randint(10000, 99999))
    trigger_time = datetime.now() + timedelta(seconds=30)
    time_spec = trigger_time.strftime("%Y-%m-%d %H:%M:%S")

    # Create the notification script
    script_path = create_alarm_script(
        "Schedule Test: This alarm was triggered on schedule! " + time_spec, alarm_id
    )
    command = f"/usr/bin/python3 {script_path}"

    print(f"Scheduling alarm '{alarm_id}' for {trigger_time.strftime('%H:%M:%S')}...")
    scheduler = AlarmSchedulerPythonClient()
    success = scheduler.create_systemd_timer(alarm_id, time_spec, command)

    if success:
        print(f"Alarm '{alarm_id}' scheduled successfully!")
        print("Waiting for alarm to trigger...")
        time.sleep(25)  # Wait until close to trigger time
        print("Alarm should trigger in approximately 5 seconds...")
        time.sleep(10)  # Wait to ensure alarm triggered
    else:
        print(f"Failed to schedule alarm '{alarm_id}'.")


def test_delay_alarm():
    """Test scheduling and then delaying an alarm."""
    alarm_id = "test-delay" + str(random.randint(10000, 99999))
    initial_time = datetime.now() + timedelta(seconds=30)
    time_spec = initial_time.strftime("%Y-%m-%d %H:%M:%S")

    # Create the notification script
    script_path = create_alarm_script(
        "Delay Test: This alarm was triggered after being delayed! " + time_spec, alarm_id
    )
    command = f"/usr/bin/python3 {script_path}"

    print(f"Scheduling alarm '{alarm_id}' for {initial_time.strftime('%H:%M:%S')}...")
    scheduler = AlarmSchedulerPythonClient()
    success = scheduler.create_systemd_timer(alarm_id, time_spec, command)

    if success:
        print(f"Alarm '{alarm_id}' scheduled successfully!")
        print("Waiting 5 seconds before delaying...")
        time.sleep(5)

        delay_seconds = 30  # Delay by 30 seconds
        print(f"Delaying alarm '{alarm_id}' by {delay_seconds} seconds...")
        success = scheduler.snooze_alarm(alarm_id, delay_seconds)

        if success:
            new_time = initial_time + timedelta(seconds=delay_seconds)
            print(
                f"Alarm '{alarm_id}' delayed successfully to {new_time.strftime('%H:%M:%S')}!"
            )
            print("Waiting for delayed alarm to trigger...")
            time.sleep(50)  # Wait until 5 seconds before new trigger time
            print("Delayed alarm should trigger in approximately 5 seconds...")
            time.sleep(10)  # Wait to ensure alarm triggered
        else:
            print(f"Failed to delay alarm '{alarm_id}'.")
    else:
        print(f"Failed to schedule alarm '{alarm_id}'.")


def test_cancel_alarm():
    """Test scheduling and then canceling an alarm."""
    alarm_id = "test-cancel" + str(random.randint(10000, 99999))
    trigger_time = datetime.now() + timedelta(seconds=30)
    time_spec = trigger_time.strftime("%Y-%m-%d %H:%M:%S")

    # Create the notification script
    script_path = create_alarm_script(
        "🔔 Cancel Test: If you see this, the cancellation failed!", alarm_id
    )
    command = f"/usr/bin/python3 {script_path}"

    print(f"Scheduling alarm '{alarm_id}' for {trigger_time.strftime('%H:%M:%S')}...")
    scheduler = AlarmSchedulerPythonClient()
    success = scheduler.create_systemd_timer(alarm_id, time_spec, command)

    if success:
        print(f"Alarm '{alarm_id}' scheduled successfully!")
        print("Waiting 10 seconds before canceling...")
        time.sleep(10)

        print(f"Cancelling alarm '{alarm_id}'...")
        success = scheduler.cancel_alarm(alarm_id)

        if success:
            print(f"Alarm '{alarm_id}' canceled successfully!")
            print(
                f"Waiting past original trigger time {trigger_time.strftime('%H:%M:%S')} to verify cancellation..."
            )
            time.sleep(35)  # Wait to verify the alarm doesn't trigger
        else:
            print(f"Failed to cancel alarm '{alarm_id}'.")
    else:
        print(f"Failed to schedule alarm '{alarm_id}'.")


if __name__ == "__main__":
    check_root()  # Check for root privileges

    print("\nRunning schedule test...")
    test_schedule_alarm()

    print("\nRunning delay test...")
    test_delay_alarm()

    print("\nRunning cancel test...")
    test_cancel_alarm()
