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
import os
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure logging to file and console
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/scheduler.log"),
        logging.StreamHandler()
    ]
)

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
        
        logging.info("=" * 80)
        logging.info(f"🚀 GENERATING SCHEDULE FROM RANT: '{req.rant}'")
        logging.info("=" * 80)
        
        # Step 1: Get existing events
        existing_events = scheduler_pipeline._get_existing_events()
        logging.info(f"📅 FOUND {len(existing_events)} EXISTING EVENTS")
        for i, event in enumerate(existing_events, 1):
            logging.info(f"  [{i}] {event.summary} ({event.start} → {event.end})")
        
        # Step 2: Parse tasks from rant
        tasks = prompt_generator.generate_tasks(req.rant)
        logging.info(f"📋 PARSED {len(tasks)} TASKS FROM RANT:")
        for i, task in enumerate(tasks, 1):
            logging.info(f"  [{i}] {task.summary} (Duration: {task.duration_minutes}m)")
            if task.priority: logging.info(f"      Priority: {task.priority}")
        
        # Step 3: Generate initial schedule
        schedule = scheduler_pipeline._generate_schedule(
            existing_events, 
            tasks
        )
        
        logging.info("=" * 80)
        logging.info(f"🤖 INITIAL SCHEDULE GENERATED ({len(schedule)} events):")
        for i, event in enumerate(schedule, 1):
            status = "NEW" if not event.already_in_calendar else ("MODIFIED" if event.is_modified else "EXISTING")
            logging.info(f"  [{i}] [{status}] {event.summary} ({event.start} → {event.end})")
            if event.is_modified:
                logging.info(f"      → MOVED FROM: {event.original_start}")
        logging.info("=" * 80)
        
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
        
        # Log current schedule state before feedback
        logging.info("=" * 80)
        logging.info(f"📝 FEEDBACK RECEIVED: '{req.feedback}'")
        logging.info("=" * 80)
        logging.info(f"📅 CURRENT SCHEDULE ({len(current_schedule)} events):")
        for i, event in enumerate(current_schedule, 1):
            status = "NEW" if not event.already_in_calendar else ("MODIFIED" if event.is_modified else "EXISTING")
            logging.info(f"  [{i}] [{status}] {event.summary}")
            logging.info(f"      Time: {event.start} → {event.end}")
            logging.info(f"      already_in_calendar: {event.already_in_calendar}")
            logging.info(f"      is_modified: {event.is_modified}")
            logging.info(f"      event_id: {event.event_id}")
            if event.original_start:
                logging.info(f"      original_start: {event.original_start}")
                logging.info(f"      original_end: {event.original_end}")
        
        # Apply feedback
        updated_schedule = scheduler_pipeline.prompt_generator.adjust_schedule_with_feedback(
            current_schedule, req.feedback
        )
        
        # Log LLM response
        logging.info("=" * 80)
        logging.info(f"🤖 LLM RESPONSE ({len(updated_schedule)} events):")
        for i, event in enumerate(updated_schedule, 1):
            logging.info(f"  [{i}] {event.summary}")
            logging.info(f"      Time: {event.start} → {event.end}")
            logging.info(f"      already_in_calendar: {event.already_in_calendar}")
            logging.info(f"      is_modified: {getattr(event, 'is_modified', 'NOT SET')}")
            logging.info(f"      event_id: {event.event_id}")
            if hasattr(event, 'original_start') and event.original_start:
                logging.info(f"      original_start: {event.original_start}")
                logging.info(f"      original_end: {event.original_end}")
        
        # Post-process: Match events and detect moves
        logging.info("=" * 80)
        logging.info("🔍 POST-PROCESSING: Matching events and detecting moves...")
        existing_event_map = {e.event_id: e for e in current_schedule if e.event_id and e.already_in_calendar}
        existing_summary_map = {e.summary.lower(): e for e in current_schedule if e.already_in_calendar}
        
        for event in updated_schedule:
            matched = False
            # Try to match by event_id first
            if event.event_id and event.event_id in existing_event_map:
                original = existing_event_map[event.event_id]
                matched = True
                logging.info(f"  ✓ Matched '{event.summary}' by event_id: {event.event_id}")
            # Try to match by summary
            elif event.summary.lower() in existing_summary_map:
                original = existing_summary_map[event.summary.lower()]
                matched = True
                logging.info(f"  ✓ Matched '{event.summary}' by summary")
                # Preserve event_id if we matched by summary
                if original.event_id:
                    event.event_id = original.event_id
                    logging.info(f"    → Preserved event_id: {event.event_id}")
            
            if matched:
                event.already_in_calendar = True
                # Check if times changed
                if event.start != original.start or event.end != original.end:
                    event.is_modified = True
                    event.original_start = original.start
                    event.original_end = original.end
                    logging.info(f"    → DETECTED MOVE: {original.start} → {event.start}")
                else:
                    event.is_modified = False
                    logging.info(f"    → No time change, keeping as existing")
            else:
                if event.already_in_calendar:
                    logging.warning(f"  ⚠️  Event '{event.summary}' marked as already_in_calendar but couldn't match to existing event")
                else:
                    logging.info(f"  ✓ '{event.summary}' is a new event")
        
        # Log final state
        logging.info("=" * 80)
        logging.info(f"✅ FINAL SCHEDULE STATE ({len(updated_schedule)} events):")
        for i, event in enumerate(updated_schedule, 1):
            status = "NEW" if not event.already_in_calendar else ("MODIFIED" if event.is_modified else "EXISTING")
            logging.info(f"  [{i}] [{status}] {event.summary} ({event.start} → {event.end})")
        logging.info("=" * 80)
        
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
        
        # Add/update events in calendar
        calendar_manager.add_events_to_calendar(current_schedule)
        
        # Count new vs modified events for message
        new_count = sum(1 for e in current_schedule if not e.already_in_calendar)
        modified_count = sum(1 for e in current_schedule if e.is_modified)
        existing_count = sum(1 for e in current_schedule if e.already_in_calendar and not e.is_modified)
        
        message_parts = []
        if new_count > 0:
            message_parts.append(f"added {new_count} new event{'s' if new_count != 1 else ''}")
        if modified_count > 0:
            message_parts.append(f"moved {modified_count} existing event{'s' if modified_count != 1 else ''}")
        if existing_count > 0:
            message_parts.append(f"{existing_count} unchanged")
        
        message = f"Successfully {' and '.join(message_parts)} to calendar"
        
        # Clean up session
        del sessions[req.schedule_id]
        
        return {
            "message": message,
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