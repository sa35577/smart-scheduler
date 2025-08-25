import datetime
import logging
from zoneinfo import ZoneInfo
from typing import List, Optional
from service_helper import get_service
from schemas import Event
from list_today import list_today_events, get_calendar_timezone
from create_event import create_events


class CalendarManager:
    """Manages all calendar operations including reading, writing, and timezone handling."""
    
    def __init__(self, access_token: Optional[str] = None):
        try:
            self.service = get_service(access_token=access_token)
            self.timezone = ZoneInfo(get_calendar_timezone(service=self.service))
            logging.info(f"CalendarManager initialized with timezone: {self.timezone}")
        except Exception as e:
            logging.error(f"Failed to initialize CalendarManager: {e}")
            raise
    
    def get_today_events(self) -> List[Event]:
        """Retrieve all events for today."""
        try:
            events = list_today_events(service=self.service)
            logging.info(f"Retrieved {len(events)} events for today")
            return events
        except Exception as e:
            logging.error(f"Failed to get today's events: {e}")
            raise
    
    def create_test_event(self) -> Event:
        """Create a test event at 11am today."""
        try:
            now = datetime.datetime.now(self.timezone)
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            event_start = start_of_day.replace(hour=11, minute=0, second=0, microsecond=0)
            event_end = event_start + datetime.timedelta(minutes=30)
            
            event = Event(
                summary="Test Event",
                start=event_start.isoformat(),
                end=event_end.isoformat(),
                already_in_calendar=False
            )
            
            logging.info(f"Creating test event: {event.summary} at {event.start}")
            create_events([event], service=self.service)
            logging.info("Test event created successfully")
            return event
        except Exception as e:
            logging.error(f"Failed to create test event: {e}")
            raise
    
    def add_events_to_calendar(self, events: List[Event]) -> None:
        """Add multiple events to the calendar."""
        try:
            logging.info(f"Adding {len(events)} events to calendar")
            create_events(events, service=self.service)
            logging.info("Events added to calendar successfully")
        except Exception as e:
            logging.error(f"Failed to add events to calendar: {e}")
            raise
    
    def get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        try:
            current_date = datetime.datetime.now(self.timezone).strftime("%Y-%m-%d")
            logging.debug(f"Current date: {current_date}")
            return current_date
        except Exception as e:
            logging.error(f"Failed to get current date: {e}")
            raise 