import datetime
import logging
from zoneinfo import ZoneInfo
from typing import List, Optional
from service_helper import get_service
from schemas import Event
from list_today import list_today_events, get_calendar_timezone
from create_event import create_events
from update_event import update_event


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
        """Add or update events in the calendar."""
        try:
            logging.info("=" * 80)
            logging.info(f"📅 PROCESSING {len(events)} EVENTS FOR CALENDAR:")
            new_events = []
            updated_events = []
            skipped_events = []
            
            for i, event in enumerate(events, 1):
                logging.info(f"  [{i}] Processing: {event.summary}")
                logging.info(f"      already_in_calendar: {event.already_in_calendar}")
                logging.info(f"      is_modified: {event.is_modified}")
                logging.info(f"      event_id: {event.event_id}")
                
                if event.already_in_calendar and event.is_modified and event.event_id:
                    # Update existing event that was moved/modified
                    logging.info(f"      → ACTION: UPDATE (event was moved)")
                    logging.info(f"      → Old time: {getattr(event, 'original_start', 'N/A')} → {getattr(event, 'original_end', 'N/A')}")
                    logging.info(f"      → New time: {event.start} → {event.end}")
                    update_event(event, service=self.service)
                    updated_events.append(event)
                elif not event.already_in_calendar:
                    # Create new event
                    logging.info(f"      → ACTION: CREATE (new event)")
                    new_events.append(event)
                else:
                    # If already_in_calendar=True but not modified, skip (unchanged)
                    logging.info(f"      → ACTION: SKIP (unchanged existing event)")
                    skipped_events.append(event)
            
            logging.info("=" * 80)
            if new_events:
                logging.info(f"🆕 CREATING {len(new_events)} NEW EVENTS:")
                for event in new_events:
                    logging.info(f"  - {event.summary} ({event.start} → {event.end})")
                create_events(new_events, service=self.service)
            
            if updated_events:
                logging.info(f"🔄 UPDATED {len(updated_events)} EXISTING EVENTS:")
                for event in updated_events:
                    logging.info(f"  - {event.summary} (ID: {event.event_id})")
            
            if skipped_events:
                logging.info(f"⏭️  SKIPPED {len(skipped_events)} UNCHANGED EVENTS:")
                for event in skipped_events:
                    logging.info(f"  - {event.summary} (ID: {event.event_id})")
            
            logging.info(f"✅ Successfully processed {len(new_events)} new, {len(updated_events)} updated, {len(skipped_events)} skipped")
            logging.info("=" * 80)
        except Exception as e:
            logging.error(f"Failed to add/update events in calendar: {e}")
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