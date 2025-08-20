import requests
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Google OAuth2 scopes for Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly']

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

BACKEND_URL = "http://localhost:8000"

def test_health():
    """Test the basic health endpoint."""
    resp = requests.get(f"{BACKEND_URL}/health")
    print("Health check status code:", resp.status_code)
    print("Health check response:", resp.json())

def test_get_today_events(access_token):
    """Test getting today's events using the token."""
    resp = requests.post(f"{BACKEND_URL}/calendar/today", 
                        json={"access_token": access_token})
    print("Get today's events status code:", resp.status_code)
    if resp.status_code == 200:
        events = resp.json()["events"]
        print(f"Found {len(events)} events for today:")
        for event in events:
            print(f"  • {event['summary']} — {event['start']} to {event['end']}")
    else:
        print("Error response:", resp.json())

def test_get_current_date(access_token):
    """Test getting current date using the token."""
    resp = requests.post(f"{BACKEND_URL}/calendar/current-date", 
                        json={"access_token": access_token})
    print("Get current date status code:", resp.status_code)
    if resp.status_code == 200:
        current_date = resp.json()["current_date"]
        print(f"Current date: {current_date}")
    else:
        print("Error response:", resp.json())

def test_create_test_event(access_token):
    """Test creating a test event using the token."""
    resp = requests.post(f"{BACKEND_URL}/calendar/test-event", 
                        json={"access_token": access_token})
    print("Create test event status code:", resp.status_code)
    if resp.status_code == 200:
        event = resp.json()["event"]
        print(f"Created test event: {event['summary']} at {event['start']}")
    else:
        print("Error response:", resp.json())

def test_interactive_scheduling(access_token):
    """Test the complete interactive scheduling flow."""
    print("\n=== Testing Interactive Scheduling ===")
    
    # Step 1: Generate initial schedule
    print("1. Generating initial schedule...")
    resp = requests.post(f"{BACKEND_URL}/schedule/generate", 
                        json={
                            "access_token": access_token,
                            "rant": "I need to write a blog post about AI scheduling, attend a launch review meeting, and walk my dog. I have a busy day ahead!"
                        })
    
    if resp.status_code != 200:
        print("Error generating schedule:", resp.json())
        return
    
    result = resp.json()
    schedule_id = result["schedule_id"]
    print(f"Generated schedule with ID: {schedule_id}")
    print("Initial schedule:")
    for event in result["schedule"]:
        print(f"  • {event['summary']} — {event['start']} to {event['end']}")
    
    # Step 2: Provide feedback
    print("\n2. Providing feedback...")
    resp = requests.post(f"{BACKEND_URL}/schedule/feedback", 
                        json={
                            "access_token": access_token,
                            "schedule_id": schedule_id,
                            "feedback": "Can you move the blog post to earlier in the day and make the dog walk shorter?"
                        })
    
    if resp.status_code != 200:
        print("Error providing feedback:", resp.json())
        return
    
    result = resp.json()
    print("Updated schedule after feedback:")
    for event in result["schedule"]:
        print(f"  • {event['summary']} — {event['start']} to {event['end']}")
    
    # Step 3: Get current schedule
    print("\n3. Getting current schedule...")
    resp = requests.get(f"{BACKEND_URL}/schedule/{schedule_id}?access_token={access_token}")
    
    if resp.status_code == 200:
        result = resp.json()
        print("Current schedule:")
        for event in result["schedule"]:
            print(f"  • {event['summary']} — {event['start']} to {event['end']}")
    
    # Step 4: Commit to calendar (commented out to avoid actually adding events)
    print("\n4. Ready to commit to calendar...")
    print("(Uncomment the code below to actually commit events to calendar)")
    
    # Uncomment these lines to actually commit the schedule:
    # resp = requests.post(f"{BACKEND_URL}/schedule/commit", 
    #                     json={
    #                         "access_token": access_token,
    #                         "schedule_id": schedule_id
    #                     })
    # if resp.status_code == 200:
    #     print("Successfully committed schedule to calendar!")
    # else:
    #     print("Error committing schedule:", resp.json())

if __name__ == "__main__":
    access_token = get_access_token()
    print("Got access token:", access_token[:10], "...")

    # Test the new API endpoints
    print("\n=== Testing API Endpoints ===")
    
    test_health()
    print()
    
    test_get_today_events(access_token)
    print()
    
    test_get_current_date(access_token)
    print()
    
    # Test interactive scheduling
    test_interactive_scheduling(access_token)
    print()
    
    # Uncomment the line below to test creating a test event
    # test_create_test_event(access_token)