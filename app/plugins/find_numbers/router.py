from fastapi import APIRouter, Request, Depends, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Participant
from app.websockets import manager
from app.plugins.find_numbers.plugin import plugin_instance
import os

router = APIRouter(prefix="/api/plugin/find_numbers", tags=["plugin-find-numbers"])
# Use plugin's own templates directory
templates = Jinja2Templates(directory="app/plugins/find_numbers/templates")

@router.post("/start")
async def start_game(
    request: Request, 
    data: dict = Body(...), 
    db: Session = Depends(get_db)
):
    # Security check: ensure user is host (check session_token)
    session_token = request.cookies.get("session_token")
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    stage = data.get("stage", 1)
    event_payload = plugin_instance.start_stage(stage)
    
    # Broadcast to all
    await manager.broadcast(event_payload)
    return {"status": "started", "stage": stage}

@router.post("/stop")
async def stop_game(
    request: Request,
    db: Session = Depends(get_db)
):
    # Security check
    session_token = request.cookies.get("session_token")
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    event_payload = plugin_instance.stop_stage()
    await manager.broadcast(event_payload)
    return {"status": "stopped"}

@router.post("/submit")
async def submit_answer(
    request: Request,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    session_token = request.cookies.get("session_token")
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant:
        raise HTTPException(status_code=401, detail="Not logged in")
        
    answers = data.get("answers", [])
    result = plugin_instance.handle_submit(str(participant.id), answers)
    return result

# Route to serve the plugin specific pages (embedded or standalone)
# For MVP, we might just render them directly when requested via /display/find_numbers etc.
# But let's add a helper here to return the HTML string if needed by the main router
