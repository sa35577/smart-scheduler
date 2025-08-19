from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from calendar_manager import CalendarManager
from schemas import Event
import logging

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScheduleRequest(BaseModel):
    rant: str
    access_token: str

class FeedbackRequest(BaseModel):
    schedule: dict
    feedback: str
    access_token: str

class SyncRequest(BaseModel):
    schedule: dict
    access_token: str

class TokenRequest(BaseModel):
    access_token: str

class EventRequest(BaseModel):
    access_token: str
    events: List[Event]

@app.get("/health")
def health():
    return {"status": "really healthy"}

@app.post("/calendar/today")
def get_today_events(req: TokenRequest):
    """Get today's events using the provided access token."""
    try:
        calendar_manager = CalendarManager(access_token=req.access_token)
        events = calendar_manager.get_today_events()
        return {"events": [event.dict() for event in events]}
    except Exception as e:
        logging.error(f"Failed to get today's events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/test-event")
def create_test_event(req: TokenRequest):
    """Create a test event using the provided access token."""
    try:
        calendar_manager = CalendarManager(access_token=req.access_token)
        event = calendar_manager.create_test_event()
        return {"event": event.dict()}
    except Exception as e:
        logging.error(f"Failed to create test event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/add-events")
def add_events_to_calendar(req: EventRequest):
    """Add multiple events to calendar using the provided access token."""
    try:
        calendar_manager = CalendarManager(access_token=req.access_token)
        calendar_manager.add_events_to_calendar(req.events)
        return {"message": f"Successfully added {len(req.events)} events to calendar"}
    except Exception as e:
        logging.error(f"Failed to add events to calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/current-date")
def get_current_date(req: TokenRequest):
    """Get current date using the provided access token."""
    try:
        calendar_manager = CalendarManager(access_token=req.access_token)
        current_date = calendar_manager.get_current_date()
        return {"current_date": current_date}
    except Exception as e:
        logging.error(f"Failed to get current date: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/schedule")
# async def create_schedule(req: ScheduleRequest):
#     return    

# @app.post("/feedback")
# async def update_schedule(req: FeedbackRequest):
#     return

# @app.post("/sync")
# async def sync_schedule(req: SyncRequest):
#     return