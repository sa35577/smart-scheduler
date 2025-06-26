import os, datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If you modify scopes, delete token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def list_today_events():
    service = get_service()

    # Define start/end of "today" in RFC3339 UTC format:
    now = datetime.datetime.now(datetime.UTC)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + datetime.timedelta(days=1)

    # iso_start = start_of_day.isoformat() + 'Z'
    # iso_end   = end_of_day.isoformat()   + 'Z'
    iso_start = start_of_day.strftime('%Y-%m-%dT%H:%M:%SZ')
    iso_end   = end_of_day.strftime('%Y-%m-%dT%H:%M:%SZ')

    print(iso_start)
    print(iso_end)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=iso_start,
        timeMax=iso_end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        print("No events found for today.")
        return

    print(f"Events for {start_of_day.date()}:")
    for evt in events:
        start = evt['start'].get('dateTime', evt['start'].get('date'))
        end   = evt['end'].get('dateTime',   evt['end'].get('date'))
        # Optionally parse back into local time for nicer formatting:
        start_fmt = datetime.datetime.fromisoformat(start).strftime('%I:%M %p')
        end_fmt   = datetime.datetime.fromisoformat(end).strftime('%I:%M %p')
        print(f" • {evt['summary']} — {start_fmt} to {end_fmt}")

if __name__ == '__main__':
    list_today_events()
