import datetime
import requests
import recurring_ical_events
from icalendar import Calendar
from operator import itemgetter
from config_manager import JsonConfig
from requests.auth import HTTPBasicAuth
import urllib3
import logging
import pytz
from datetime import timedelta
from typing import List, Dict, Any, Optional
from event import Event

# Disable logging warnings when user is not using cert check
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Get logger for this module
logger = logging.getLogger(__name__)

# Configure timezones
UTC_TZ = pytz.utc
MTN_TZ = pytz.timezone("America/Denver")  # Mountain Time

# Type aliases
CalendarDict = Dict[str, str]


class IcalManager:
    def __init__(self, calendar_obj: CalendarDict, config: JsonConfig) -> None:
        self.calendar: CalendarDict = calendar_obj
        self.events: List[Event] = []
        self.config: JsonConfig = config

    def fetch_and_parse_events(self) -> List[Event]:
        logger.info("Attempting to fetch calendar: %s", self.calendar["name"])
        logger.debug("Calendar URL: %s", self.calendar["ical_url"])
        logger.debug("Verify cert: %s", self.calendar["verify_cert"])

        auth = False
        if len(self.calendar["password"]) > 0:
            auth = True
        try:
            if auth:
                logger.debug(
                    "Using basic auth with username: %s", self.calendar["user_name"]
                )
                logger.debug("SSL verification: %s", self.calendar["verify_cert"])
                response = requests.get(
                    self.calendar["ical_url"],
                    auth=HTTPBasicAuth(
                        self.calendar["user_name"], self.calendar["password"]
                    ),
                    verify=self.calendar["verify_cert"],
                )
            else:
                response = requests.get(
                    self.calendar["ical_url"], verify=self.calendar["verify_cert"]
                )
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection failed to %s", self.calendar["ical_url"])
            logger.debug("Full connection error:", exc_info=True)
            # Add specific SSL troubleshooting
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                logger.error(
                    "SSL certificate verification failed. Try verify_cert=false"
                )
            raise  # Re-raise instead of exit() to preserve stack trace

        except requests.exceptions.SSLError as e:
            logger.error("SSL Error: %s", e)
            logger.debug(
                "SSL version: %s", requests.packages.urllib3.util.ssl_.OPENSSL_VERSION
            )
            raise

        except Exception as e:
            logger.error("Unexpected error fetching calendar: %s", e, exc_info=True)
            raise

        if response.status_code != 200:
            raise Exception(
                "Failed to fetch iCalendar data: Status Code %s" % response.status_code
            )

        # Initialize the list to store the events
        self.events = []

        # Parse the iCalendar data
        ical_data = response.text
        cal = Calendar.from_ical(ical_data)

        # Get current time in Mountain Time
        today_mtn = datetime.datetime.now(MTN_TZ)
        next_week_end_mtn = today_mtn + timedelta(days=7)

        # Convert to UTC for comparison with iCal dates
        today_utc = today_mtn.astimezone(UTC_TZ)
        next_week_end_utc = next_week_end_mtn.astimezone(UTC_TZ)

        # Process events with timezone conversion
        for event in recurring_ical_events.of(cal).between(
            today_utc, next_week_end_utc
        ):
            dtstart = event["DTSTART"].dt
            dtend = event["DTEND"].dt

            # Convert to Mountain Time if timezone-aware
            if dtstart.tzinfo is not None:
                dtstart_mtn = dtstart.astimezone(MTN_TZ)
            else:  # Handle floating times
                dtstart_mtn = MTN_TZ.localize(dtstart)

            if event["SUMMARY"].strip().startswith(self.config.alarm_keyword):
                logger.debug("Found alarm event: %s", event["SUMMARY"])
                event_obj = Event(
                    date_val=dtstart_mtn.date(),
                    start_time=dtstart_mtn.time(),
                    end_time=dtend.astimezone(MTN_TZ).time()
                    if dtend.tzinfo
                    else MTN_TZ.localize(dtend).time(),
                    title=event["SUMMARY"],
                    event_id="%s:%s"
                    % (event.get("UID"), dtstart_mtn.strftime("%m-%d")),
                    is_system_managed=False,
                    timezone=self.config.timezone,
                )
                self.events.append(event_obj)

        # Sort the events by start time
        self.events.sort()

        return self.events
