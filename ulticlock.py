from ical_manager import IcalManager
from sqlManager import sqlManager
from config_manager import JsonConfig
from typing import Optional, Dict, Any, List

config = JsonConfig("ulticlock.config")
calendar = config.calendars[0]
ical_manager = IcalManager(calendar, config)

alarms_database = sqlManager(config.database_path, config.timezone)
next_event = alarms_database.get_next_alarm()
print("Stored event")
if next_event is not None:
    print(
        f"Date: {next_event['date']}, Start_Time: {next_event['start_time']}, End_Time: {next_event['end_time']}, Title: {next_event['title']}, event_id: {next_event['event_id']}"
    )
else:
    print("No value found")
print("new set of events")
# Print the sorted events
parsed_events = ical_manager.fetch_and_parse_events()
for event in parsed_events:
    print(
        f"Date: {event['date']}, Start_Time: {event['start_time']}, End_Time: {event['end_time']}, Title: {event['title']}, Event ID: {event['event_id']}"
    )

alarms_database.store_alarms(parsed_events)
print("new next alarm")
next_event = alarms_database.get_next_alarm()
if next_event is not None:
    print(
        f"Date: {next_event['date']}, Start_Time: {next_event['start_time']}, End_Time: {next_event['end_time']}, Title: {next_event['title']}, event_id: {next_event['event_id']}"
    )
else:
    print("No value found")
alarms_database.close()
