import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# If you modify scopes, delete token.json.
READ_ONLY_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
ALL_SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly']

def get_service(read_only=False):
    creds = None
    SCOPES = READ_ONLY_SCOPES if read_only else ALL_SCOPES
    if os.path.exists('token.json'):
        os.remove('token.json')
    # if os.path.exists('token.json'):
    #     creds = Credentials.from_authorized_user_file('token.json', SCOPES)
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