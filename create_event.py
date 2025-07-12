import argparse
import datetime
from service_helper import get_service
from schemas import Event

'''
Example:
python create_event.py \
  --summary "Coffee with Bob" \
  --start "2025-06-27T10:00:00-07:00" \
  --end   "2025-06-27T10:30:00-07:00" \
  --location "Café Nero" \
  --description "Discuss Q3 roadmap"
'''

def create_event(event: Event):
    service = get_service()
    event = {
        'summary':     event.summary,
        'location':    event.location,
        'description': event.description,
        'start':       {'dateTime': event.start},
        'end':         {'dateTime': event.end},
    }
    created = service.events().insert(
        calendarId='primary',
        body=event,
    ).execute()
    return created

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