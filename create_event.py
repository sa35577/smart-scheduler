import argparse
import datetime
from service_helper import get_service
from schemas import Event
from zoneinfo import ZoneInfo

'''
Example:
python create_event.py \
  --summary "Coffee with Bob" \
  --start "2025-06-27T10:00:00-07:00" \
  --end   "2025-06-27T10:30:00-07:00" \
  --location "Café Nero" \
  --description "Discuss Q3 roadmap"
'''

def create_events(events: list[Event]):
    service = get_service()
    
    # Get calendar timezone
    calendar = service.calendars().get(calendarId='primary').execute()
    timezone = calendar.get('timeZone', 'UTC')
    tz = ZoneInfo(timezone)

    for event in events:
        # Parse the datetime and add timezone if missing
        start_dt = datetime.datetime.fromisoformat(event.start.replace('Z', '+00:00'))
        end_dt = datetime.datetime.fromisoformat(event.end.replace('Z', '+00:00'))
        
        # If no timezone info, assume it's in the calendar's timezone
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=tz)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=tz)
        
        event_dict = {
            'summary':     event.summary,
            'location':    event.location,
            'description': event.description,
            'start':       {'dateTime': start_dt.isoformat()},
            'end':         {'dateTime': end_dt.isoformat()},
        }
        created = service.events().insert(
            calendarId='primary',
            body=event_dict,
        ).execute()
        print(f"Event created: {created.get('id')}")


def create_event(event: Event):
    return create_events([event])


def parse_args():
    p = argparse.ArgumentParser(
        description="Create a Google Calendar event via API"
    )
    p.add_argument('--summary',     required=True, help="Event title")
    p.add_argument('--start',       required=True,
                   help="Start time in RFC3339, e.g. 2025-06-30T10:00:00-07:00")
    p.add_argument('--end',         required=True,
                   help="End   time in RFC3339, e.g. 2025-06-30T10:30:00-07:00")
    p.add_argument('--location',    default="",    help="Optional location")
    p.add_argument('--description', default="",    help="Optional description")
    return p.parse_args()

def main():
    args = parse_args()
    service = get_service()

    event = {
        'summary':     args.summary,
        'location':    args.location,
        'description': args.description,
        'start':       {'dateTime': args.start},
        'end':         {'dateTime': args.end},
    }

    created = service.events().insert(
        calendarId='primary',
        body=event,
    ).execute()

    print("Event created:")
    print(f" • ID:   {created.get('id')}")
    print(f" • Link: {created.get('htmlLink')}")

if __name__ == '__main__':
    main()