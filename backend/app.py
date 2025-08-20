from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from calendar_manager import CalendarManager
from schemas import Event, Task
from scheduler_pipeline import SchedulerPipeline
from prompt_generator import PromptGenerator
from openai import OpenAI
from dotenv import load_dotenv
import logging
import uuid
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (in production, use Redis or database)
sessions: Dict[str, Dict] = {}

class ScheduleRequest(BaseModel):
    rant: str
    access_token: str

class FeedbackRequest(BaseModel):
    schedule_id: str
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

class CommitRequest(BaseModel):
    schedule_id: str
    access_token: str

@app.get("/health")
def health():
    return {"status": "really healthy"}

@app.post("/schedule/generate")
def generate_schedule(req: ScheduleRequest):
    """Generate initial schedule from a rant/description."""
    try:
        # Create session
        session_id = str(uuid.uuid4())
        
        # Initialize components with the user's token
        calendar_manager = CalendarManager(access_token=req.access_token)
        client = OpenAI()
        prompt_generator = PromptGenerator(client)
        scheduler_pipeline = SchedulerPipeline(calendar_manager, prompt_generator)
        
        # Parse tasks from rant (you might want to enhance this)
        # For now, let's create some example tasks
        tasks = [
            Task(name="Task from rant", description=req.rant, time_estimate=60),
        ]
        
        # Generate initial schedule
        schedule = scheduler_pipeline._generate_schedule(
            scheduler_pipeline._get_existing_events(), 
            tasks
        )
        
        # Store session
        sessions[session_id] = {
            "calendar_manager": calendar_manager,
            "scheduler_pipeline": scheduler_pipeline,
            "current_schedule": schedule,
            "created_at": datetime.now(),
            "access_token": req.access_token
        }
        
        # Clean up old sessions (older than 1 hour)
        _cleanup_old_sessions()
        
        return {
            "schedule_id": session_id,
            "schedule": [event.dict() for event in schedule],
            "message": "Schedule generated successfully. Use schedule_id for feedback."
        }
        
    except Exception as e:
        logging.error(f"Failed to generate schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule/feedback")
def provide_feedback(req: FeedbackRequest):
    """Provide feedback to adjust the current schedule."""
    try:
        if req.schedule_id not in sessions:
            raise HTTPException(status_code=404, detail="Schedule session not found")
        
        session = sessions[req.schedule_id]
        
        # Verify access token matches
        if session["access_token"] != req.access_token:
            raise HTTPException(status_code=403, detail="Access token mismatch")
        
        # Get components from session
        scheduler_pipeline = session["scheduler_pipeline"]
        current_schedule = session["current_schedule"]
        
        # Apply feedback
        updated_schedule = scheduler_pipeline.prompt_generator.adjust_schedule_with_feedback(
            current_schedule, req.feedback
        )
        
        # Update session
        session["current_schedule"] = updated_schedule
        
        return {
            "schedule_id": req.schedule_id,
            "schedule": [event.dict() for event in updated_schedule],
            "message": "Schedule updated based on feedback."
        }
        
    except Exception as e:
        logging.error(f"Failed to process feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule/commit")
def commit_schedule(req: CommitRequest):
    """Commit the current schedule to the calendar."""
    try:
        if req.schedule_id not in sessions:
            raise HTTPException(status_code=404, detail="Schedule session not found")
        
        session = sessions[req.schedule_id]
        
        # Verify access token matches
        if session["access_token"] != req.access_token:
            raise HTTPException(status_code=403, detail="Access token mismatch")
        
        # Get components from session
        calendar_manager = session["calendar_manager"]
        current_schedule = session["current_schedule"]
        
        # Add events to calendar
        calendar_manager.add_events_to_calendar(current_schedule)
        
        # Clean up session
        del sessions[req.schedule_id]
        
        return {
            "message": f"Successfully added {len(current_schedule)} events to calendar",
            "schedule": [event.dict() for event in current_schedule]
        }
        
    except Exception as e:
        logging.error(f"Failed to commit schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule/{schedule_id}")
def get_schedule(schedule_id: str, access_token: str):
    """Get the current schedule for a session."""
    try:
        if schedule_id not in sessions:
            raise HTTPException(status_code=404, detail="Schedule session not found")
        
        session = sessions[schedule_id]
        
        # Verify access token matches
        if session["access_token"] != access_token:
            raise HTTPException(status_code=403, detail="Access token mismatch")
        
        return {
            "schedule_id": schedule_id,
            "schedule": [event.dict() for event in session["current_schedule"]],
            "created_at": session["created_at"].isoformat()
        }
        
    except Exception as e:
        logging.error(f"Failed to get schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _cleanup_old_sessions():
    """Remove sessions older than 1 hour."""
    cutoff_time = datetime.now() - timedelta(hours=1)
    expired_sessions = [
        session_id for session_id, session in sessions.items()
        if session["created_at"] < cutoff_time
    ]
    for session_id in expired_sessions:
        del sessions[session_id]

@app.post("/calendar/today")
def get_today_events(req: TokenRequest):
    """Get today's events using the provided access token."""
    try:
        calendar_manager = CalendarManager(access_token=req.access_token)
        events = calendar_manager.get_today_events()
        return {"events": [event.model_dump() for event in events]}
    except Exception as e:
        logging.error(f"Failed to get today's events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/test-event")
def create_test_event(req: TokenRequest):
    """Create a test event using the provided access token."""
    try:
        calendar_manager = CalendarManager(access_token=req.access_token)
        event = calendar_manager.create_test_event()
        return {"event": event.model_dump()}
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
    
@app.get("/calendar/today-events")
def get_today_events(req: TokenRequest):
    """Get today's events using the provided access token."""
    try:
        calendar_manager = CalendarManager(access_token=req.access_token)
        events = calendar_manager.get_today_events()
        return {"events": [event.model_dump() for event in events]}
    except Exception as e:
        logging.error(f"Failed to get today's events: {e}")
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