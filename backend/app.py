from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

@app.get("/health")
def health():
    return {"status": "really healthy"}

# @app.post("/schedule")
# async def create_schedule(req: ScheduleRequest):
#     return    

# @app.post("/feedback")
# async def update_schedule(req: FeedbackRequest):
#     return

# @app.post("/sync")
# async def sync_schedule(req: SyncRequest):
#     return