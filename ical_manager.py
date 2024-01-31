import datetime
import requests
import recurring_ical_events
from icalendar import Calendar
from operator import itemgetter

class IcalManager:
    def __init__(self, icalendar_url):
        self.icalendar_url = icalendar_url
        self.events = []

    def fetch_and_parse_events(self):
        # Fetch iCalendar data from the URL
        response = requests.get(self.icalendar_url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch iCalendar data: Status Code {response.status_code}")

        # Initialize the list to store the events
        self.events = []

        # Parse the iCalendar data
        ical_data = response.text
        cal = Calendar.from_ical(ical_data)

         # Calculate the start and end date for the next week
        today = datetime.date.today()
        next_week_end = today + datetime.timedelta(days=7)

        # Iterate through events for the upcoming week
        for event in recurring_ical_events.of(cal).between(today, next_week_end):
            # Generate event ID with month and day appended
            event_date = event["DTSTART"].dt
            event_id = event.get("UID")
            if event_date:
                event_id += f":{event_date.strftime('%m-%d')}"
            event_info = {
                "date": event["DTSTART"].dt.date(),
                "start_time": event["DTSTART"].dt.time(),
                "end_time": event["DTEND"].dt.time(),
                "title": event["SUMMARY"],
                "event_id": event_id,
            }
            self.events.append(event_info)

        # Sort the events by start time
        self.events.sort(key=lambda x: (x["date"], x["start_time"]))

        return self.events
