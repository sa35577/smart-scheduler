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
import json
import jwt
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# --- Structured Logging Configuration ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "session_id": getattr(record, "session_id", "N/A"),
            "user_id": getattr(record, "user_id", "N/A"),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

os.makedirs("logs", exist_ok=True)
handler = logging.FileHandler("logs/scheduler.json")
handler.setFormatter(JsonFormatter())

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler, logging.StreamHandler()]
)
logger = logging.getLogger("scheduler")

def get_user_id(access_token: str, id_token: Optional[str] = None) -> str:
    """Extract email from id_token (JWT) or fallback to access_token decoding."""
    # Debug: Check if id_token was provided
    if id_token:
        logger.info(f"📧 Attempting to decode id_token (length: {len(id_token)})")
    else:
        logger.warning("⚠️ No id_token provided, will attempt to decode access_token (likely to fail)")
    
    # Prefer id_token if provided (it's guaranteed to be a JWT with user info)
    token_to_decode = id_token if id_token else access_token
    
    try:
        # Decode JWT without verification (we just want to read the claims)
        decoded = jwt.decode(token_to_decode, options={"verify_signature": False})
        email = decoded.get("email")
        if email:
            logger.info(f"✅ Successfully extracted email from {'id_token' if id_token else 'access_token'}: {email}")
            return email
        else:
            logger.warning(f"⚠️ JWT decoded but no 'email' claim found. Claims: {list(decoded.keys())}")
    except jwt.DecodeError:
        # Token is not a JWT - access tokens are opaque, id_tokens are JWTs
        if id_token:
            logger.warning("❌ id_token is not a valid JWT, cannot extract email")
        else:
            logger.warning("❌ Access token is not a JWT (expected for opaque tokens), cannot extract email")
    except Exception as e:
        logger.warning(f"❌ Failed to decode token: {e}")
    
    return "unknown_user"

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
    id_token: Optional[str] = None  # JWT with user email (preferred for user identification)

class FeedbackRequest(BaseModel):
    schedule_id: str
    feedback: str
    access_token: str
    id_token: Optional[str] = None  # JWT with user email

class SyncRequest(BaseModel):
    schedule: dict
    access_token: str

class TokenRequest(BaseModel):
    access_token: str
    id_token: Optional[str] = None  # JWT with user email

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
    session_id = str(uuid.uuid4())
    user_id = get_user_id(req.access_token, req.id_token)
    
    # Create a contextual logger for this request
    ctx_logger = logging.LoggerAdapter(logger, {"session_id": session_id, "user_id": user_id})
    
    try:
        ctx_logger.info(f"🚀 Generating schedule from rant (Length: {len(req.rant)})")
        
        # Initialize components
        calendar_manager = CalendarManager(access_token=req.access_token)
        client = OpenAI()
        prompt_generator = PromptGenerator(client)
        scheduler_pipeline = SchedulerPipeline(calendar_manager, prompt_generator)
        
        # Step 1: Get existing events
        existing_events = scheduler_pipeline._get_existing_events()
        ctx_logger.info(f"📅 Found {len(existing_events)} existing events")
        
        # Step 2: Parse tasks from rant
        tasks = prompt_generator.generate_tasks(req.rant)
        ctx_logger.info(f"📋 Parsed {len(tasks)} tasks from rant")
        
        # Step 3: Generate initial schedule
        schedule = scheduler_pipeline._generate_schedule(existing_events, tasks)
        ctx_logger.info(f"🤖 Initial schedule generated with {len(schedule)} events")
        
        # Store session
        sessions[session_id] = {
            "calendar_manager": calendar_manager,
            "scheduler_pipeline": scheduler_pipeline,
            "current_schedule": schedule,
            "created_at": datetime.now(),
            "access_token": req.access_token,
            "user_id": user_id  # Cache user info
        }
        
        _cleanup_old_sessions()
        
        return {
            "schedule_id": session_id,
            "schedule": [event.dict() for event in schedule],
            "message": "Schedule generated successfully."
        }
        
    except Exception as e:
        ctx_logger.error(f"Failed to generate schedule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule/feedback")
def provide_feedback(req: FeedbackRequest):
    """Provide feedback to adjust the current schedule."""
    if req.schedule_id not in sessions:
        raise HTTPException(status_code=404, detail="Schedule session not found")
    
    session = sessions[req.schedule_id]
    user_id = session.get("user_id", "unknown")
    
    # Contextual logger with same session/user ID
    ctx_logger = logging.LoggerAdapter(logger, {"session_id": req.schedule_id, "user_id": user_id})
    
    try:
        if session["access_token"] != req.access_token:
            raise HTTPException(status_code=403, detail="Access token mismatch")
        
        ctx_logger.info(f"📝 Received feedback: '{req.feedback}'")
        
        scheduler_pipeline = session["scheduler_pipeline"]
        current_schedule = session["current_schedule"]
        
        # Apply feedback
        updated_schedule = scheduler_pipeline.prompt_generator.adjust_schedule_with_feedback(
            current_schedule, req.feedback
        )
        
        ctx_logger.info(f"✅ Adjusted schedule (Events: {len(updated_schedule)})")
        
        # Update session
        session["current_schedule"] = updated_schedule
        
        return {
            "schedule_id": req.schedule_id,
            "schedule": [event.dict() for event in updated_schedule],
            "message": "Schedule updated."
        }
        
    except Exception as e:
        ctx_logger.error(f"Failed to process feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule/commit")
def commit_schedule(req: CommitRequest):
    """Commit the current schedule to the calendar."""
    if req.schedule_id not in sessions:
        raise HTTPException(status_code=404, detail="Schedule session not found")
    
    session = sessions[req.schedule_id]
    user_id = session.get("user_id", "unknown")
    ctx_logger = logging.LoggerAdapter(logger, {"session_id": req.schedule_id, "user_id": user_id})
    
    try:
        if session["access_token"] != req.access_token:
            raise HTTPException(status_code=403, detail="Access token mismatch")
        
        calendar_manager = session["calendar_manager"]
        current_schedule = session["current_schedule"]
        
        ctx_logger.info(f"💾 Committing schedule to calendar ({len(current_schedule)} events)")
        
        # Add/update events in calendar
        calendar_manager.add_events_to_calendar(current_schedule)
        
        # Count new vs modified events
        new_count = sum(1 for e in current_schedule if not e.already_in_calendar)
        modified_count = sum(1 for e in current_schedule if e.is_modified)
        
        ctx_logger.info(f"🎉 Commit successful: {new_count} new, {modified_count} moved")
        
        del sessions[req.schedule_id]
        
        return {
            "message": f"Successfully processed {new_count} new and {modified_count} moved events",
            "schedule": [event.dict() for event in current_schedule]
        }
    except Exception as e:
        ctx_logger.error(f"Failed to commit schedule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule/{schedule_id}")
def get_schedule(schedule_id: str, access_token: str):
    """Get the current schedule for a session."""
    if schedule_id not in sessions:
        raise HTTPException(status_code=404, detail="Schedule session not found")
    
    session = sessions[schedule_id]
    user_id = session.get("user_id", "unknown")
    ctx_logger = logging.LoggerAdapter(logger, {"session_id": schedule_id, "user_id": user_id})
    
    try:
        if session["access_token"] != access_token:
            raise HTTPException(status_code=403, detail="Access token mismatch")
        
        return {
            "schedule_id": schedule_id,
            "schedule": [event.dict() for event in session["current_schedule"]],
            "created_at": session["created_at"].isoformat()
        }
    except Exception as e:
        ctx_logger.error(f"Failed to get schedule: {e}", exc_info=True)
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
    user_id = get_user_id(req.access_token, req.id_token)
    ctx_logger = logging.LoggerAdapter(logger, {"session_id": "N/A", "user_id": user_id})
    try:
        ctx_logger.info("📅 Fetching today's events for user")
        calendar_manager = CalendarManager(access_token=req.access_token)
        events = calendar_manager.get_today_events()
        return {"events": [event.model_dump() for event in events]}
    except Exception as e:
        ctx_logger.error(f"Failed to get today's events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/test-event")
def create_test_event(req: TokenRequest):
    """Create a test event using the provided access token."""
    user_id = get_user_id(req.access_token, req.id_token)
    ctx_logger = logging.LoggerAdapter(logger, {"session_id": "N/A", "user_id": user_id})
    try:
        ctx_logger.info("🧪 Creating test event")
        calendar_manager = CalendarManager(access_token=req.access_token)
        event = calendar_manager.create_test_event()
        return {"event": event.model_dump()}
    except Exception as e:
        ctx_logger.error(f"Failed to create test event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/add-events")
def add_events_to_calendar(req: EventRequest):
    """Add multiple events to calendar using the provided access token."""
    user_id = get_user_id(req.access_token, req.id_token)
    ctx_logger = logging.LoggerAdapter(logger, {"session_id": "N/A", "user_id": user_id})
    try:
        ctx_logger.info(f"➕ Adding {len(req.events)} events to calendar")
        calendar_manager = CalendarManager(access_token=req.access_token)
        calendar_manager.add_events_to_calendar(req.events)
        return {"message": f"Successfully added {len(req.events)} events to calendar"}
    except Exception as e:
        ctx_logger.error(f"Failed to add events to calendar: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/current-date")
def get_current_date(req: TokenRequest):
    """Get current date using the provided access token."""
    user_id = get_user_id(req.access_token, req.id_token)
    ctx_logger = logging.LoggerAdapter(logger, {"session_id": "N/A", "user_id": user_id})
    try:
        calendar_manager = CalendarManager(access_token=req.access_token)
        current_date = calendar_manager.get_current_date()
        return {"current_date": current_date}
    except Exception as e:
        ctx_logger.error(f"Failed to get current date: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))