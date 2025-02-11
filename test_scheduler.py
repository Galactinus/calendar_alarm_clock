import time
import os
import sys
from datetime import datetime, timedelta
from scheduler_python_client import AlarmSchedulerPythonClient
import random
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_root():
    """Check if the script is running as root."""
    if os.geteuid() != 0:
        print("This script must be run as root. Please use 'sudo' or run as root.")
        # sys.exit(1)


def test_schedule_alarm():
    logger.info("Starting schedule alarm test")
    alarm_id = "test-schedule" + str(random.randint(10000, 99999))
    trigger_time = datetime.now() + timedelta(seconds=30)
    time_spec = trigger_time.strftime("%Y-%m-%d %H:%M:%S")

    logger.debug("Creating alarm %s for %s", alarm_id, trigger_time)
    scheduler = AlarmSchedulerPythonClient()
    success = scheduler.create_systemd_timer(
        alarm_id, 
        time_spec, 
        "Test alarm",
        plugin_list=["windows_notification"]
    )

    if success:
        logger.info("Alarm %s scheduled successfully", alarm_id)
        logger.debug("Waiting for alarm trigger")
        time.sleep(25)
        logger.info("Alarm should trigger in approximately 5 seconds")
        time.sleep(10)
    else:
        logger.error("Failed to schedule alarm %s", alarm_id)


def test_delay_alarm():
    """Test scheduling and then delaying an alarm."""
    alarm_id = "test-delay" + str(random.randint(10000, 99999))
    initial_time = datetime.now()
    scheduled_time = initial_time + timedelta(seconds=30)
    time_spec = scheduled_time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"Scheduling alarm '{alarm_id}' for {scheduled_time.strftime('%H:%M:%S')}...")
    scheduler = AlarmSchedulerPythonClient()
    success = scheduler.create_systemd_timer(
        alarm_id, 
        time_spec, 
        "Test delay alarm"
    )

    if success:
        print(f"Alarm '{alarm_id}' scheduled successfully!")
        print("Waiting 10 seconds before delaying...")
        time_elapsed = 10 # 10 seconds
        time.sleep(time_elapsed)

        delay_seconds = 30  # Delay by 30 seconds
        print(f"Delaying alarm '{alarm_id}' by {delay_seconds} seconds...")
        success = scheduler.snooze_alarm(alarm_id, delay_seconds)

        if success:
            new_time = initial_time + timedelta(seconds=time_elapsed) + timedelta(seconds=delay_seconds)
            print(
                f"Alarm '{alarm_id}' delayed successfully to {new_time.strftime('%H:%M:%S')}!"
            )
            print("Waiting for delayed alarm to trigger...")
            time.sleep(25)  # Wait until 5 seconds before new trigger time
            print("Delayed alarm should trigger in approximately 5 seconds...")
            time.sleep(7)  # Wait to ensure alarm triggered
        else:
            print(f"Failed to delay alarm '{alarm_id}'.")
    else:
        print(f"Failed to schedule alarm '{alarm_id}'.")


def test_cancel_alarm():
    """Test scheduling and then canceling an alarm."""
    alarm_id = "test-cancel" + str(random.randint(10000, 99999))
    trigger_time = datetime.now() + timedelta(seconds=30)
    time_spec = trigger_time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"Scheduling alarm '{alarm_id}' for {trigger_time.strftime('%H:%M:%S')}...")
    scheduler = AlarmSchedulerPythonClient()
    success = scheduler.create_systemd_timer(
        alarm_id, 
        time_spec, 
        "Test cancel alarm"
    )

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
