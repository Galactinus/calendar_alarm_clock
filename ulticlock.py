from ical_manager import IcalManager
from sqlManager import sqlManager
from config_manager import JsonConfig
from typing import Optional
from event import Event
import logging
from log_config import setup_logging

# Set up logging first
setup_logging()

# Load config after logging is configured
config = JsonConfig("ulticlock.config")
logger = logging.getLogger(__name__)

logger.debug("Starting application with debug level: %s", config.debug_level)

calendar = config.calendars[0]
ical_manager = IcalManager(calendar, config)

alarms_database = sqlManager(config.database_path, config.timezone)
next_event = alarms_database.get_next_alarm()
logger.info("Checking stored events")
if next_event is not None:
    logger.info("Next stored event: %s", next_event)
else:
    logger.info("No stored events found")

logger.info("Fetching new events from calendar")
# Fetch and store new events
parsed_events = ical_manager.fetch_and_parse_events()
for event in parsed_events:
    logger.info("Found event: %s", event)

alarms_database.store_alarms(parsed_events)
logger.info("Checking next alarm after update")
next_event = alarms_database.get_next_alarm()
if next_event is not None:
    logger.info("Next upcoming event: %s", next_event)
else:
    logger.info("No upcoming events found")
alarms_database.close()
