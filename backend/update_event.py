import datetime
from service_helper import get_service
from schemas import Event
from zoneinfo import ZoneInfo

def update_event(event: Event, service=None):
    """Update an existing calendar event."""
    if service is None:
        service = get_service()
    
    if not event.event_id:
        raise ValueError("Cannot update event without event_id")
    
    # Get calendar timezone
    calendar = service.calendars().get(calendarId='primary').execute()
    timezone = calendar.get('timeZone', 'UTC')
    tz = ZoneInfo(timezone)
    
    # Parse the datetime and add timezone if missing
    start_dt = datetime.datetime.fromisoformat(event.start.replace('Z', '+00:00'))
    end_dt = datetime.datetime.fromisoformat(event.end.replace('Z', '+00:00'))
    
    # If no timezone info, assume it's in the calendar's timezone
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=tz)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=tz)
    
    # Get the existing event first
    existing_event = service.events().get(
        calendarId='primary',
        eventId=event.event_id
    ).execute()
    
    # Update the event
    existing_event['summary'] = event.summary
    existing_event['start'] = {'dateTime': start_dt.isoformat()}
    existing_event['end'] = {'dateTime': end_dt.isoformat()}
    
    if event.location:
        existing_event['location'] = event.location
    if event.description:
        existing_event['description'] = event.description
    
    updated = service.events().update(
        calendarId='primary',
        eventId=event.event_id,
        body=existing_event
    ).execute()
    
    print(f"Event updated: {updated.get('summary')} (ID: {updated.get('id')})")
    return updated
