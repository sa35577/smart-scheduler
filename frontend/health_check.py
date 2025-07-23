import requests
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Google OAuth2 scopes for Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_access_token():
    # This assumes you have a credentials.json in your frontend/ directory
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
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds.token

BACKEND_URL = "http://localhost:8000/health"

if __name__ == "__main__":
    access_token = get_access_token()
    print("Got access token:", access_token[:10], "...")

    # Example: send the token to your backend (if you want to test /schedule, etc.)
    resp = requests.get(BACKEND_URL)
    print("Status code:", resp.status_code)
    print("Response:", resp.json()) 