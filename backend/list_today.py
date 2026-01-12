from service_helper import get_service
import datetime
import logging
from schemas import Event
from zoneinfo import ZoneInfo

'''
Example:
python list_today.py
'''

def get_calendar_timezone(service=None) -> str:
    if service is None:
        service = get_service(read_only=True)
    calendar = service.calendars().get(calendarId='primary').execute()
    return calendar.get('timeZone', 'UTC')

def list_today_events(service=None) -> list[Event]:
    if service is None:
        service = get_service(read_only=True)

    # Get calendar timezone
    calendar = service.calendars().get(calendarId='primary').execute()
    timezone = calendar.get('timeZone', 'UTC')
    
    # Define start/end of "today" in the calendar's timezone:
    
    tz = ZoneInfo(timezone)
    now = datetime.datetime.now(tz)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + datetime.timedelta(days=1)

    iso_start = start_of_day.isoformat()
    iso_end = end_of_day.isoformat()

    logging.info(iso_start)
    logging.info(iso_end)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=iso_start,
        timeMax=iso_end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        logging.info("No events found for today.")
        return []

    logging.info(f"Events for {start_of_day.date()}:")
    results = []
    for evt in events:
        start = evt['start'].get('dateTime', evt['start'].get('date'))
        end   = evt['end'].get('dateTime',   evt['end'].get('date'))
        
        # Parse the datetime strings
        start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
        
        # Ensure timezone info is present
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=tz)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=tz)
        
        # Format for logging (human-readable)
        start_fmt = start_dt.strftime('%I:%M %p')
        end_fmt = end_dt.strftime('%I:%M %p')
        logging.info(f" • {evt['summary']} — {start_fmt} to {end_fmt}")
        
        # Store ISO8601 format for API (consistent with schedule generation)
        results.append(Event(
            summary=evt['summary'], 
            start=start_dt.isoformat(), 
            end=end_dt.isoformat(),
            already_in_calendar=True
        ))

    return results


if __name__ == '__main__':
    list_today_events()
