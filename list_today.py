from service_helper import get_service
import datetime
import logging
from schemas import Event

'''
Example:
python list_today.py
'''

def list_today_events() -> list[Event]:
    service = get_service(read_only=True)

    # Get calendar timezone
    calendar = service.calendars().get(calendarId='primary').execute()
    timezone = calendar.get('timeZone', 'UTC')
    
    # Define start/end of "today" in the calendar's timezone:
    from zoneinfo import ZoneInfo
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
        # Optionally parse back into local time for nicer formatting:
        start_fmt = datetime.datetime.fromisoformat(start).strftime('%I:%M %p')
        end_fmt   = datetime.datetime.fromisoformat(end).strftime('%I:%M %p')
        logging.info(f" • {evt['summary']} — {start_fmt} to {end_fmt}")
        results.append(Event(summary=evt['summary'], start=start_fmt, end=end_fmt))

    return results


if __name__ == '__main__':
    list_today_events()
