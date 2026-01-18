from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, Participant
from app.utils import generate_qr_base64, get_server_url
from app.plugin_manager import plugin_manager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def display_index(request: Request, db: Session = Depends(get_db)):
    # Get current active event or create one if none exists (MVP simplified)
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        # Auto-create default event for MVP convenience
        event = Event(title="新培训活动", host_password_hash="admin123") # TODO: Hash password
        db.add(event)
        db.commit()
        db.refresh(event)
    
    # Count participants
    count = db.query(Participant).filter(Participant.event_id == event.id).count()
    
    # Generate QR code for signin page
    # Use server IP address instead of localhost for mobile access
    base_url = get_server_url()
    signin_url = f"{base_url}/signin"
    qr_code = generate_qr_base64(signin_url)
    
    # Check current plugin state
    current_plugin = None
    if event.current_plugin_id and event.current_plugin_state == "running":
        current_plugin = event.current_plugin_id
    elif event.current_plugin_id and event.current_plugin_state == "results":
        current_plugin = event.current_plugin_id # Or a specific results page
        
    return templates.TemplateResponse("index.html", {
        "request": request,
        "event": event,
        "participant_count": count,
        "qr_code": qr_code,
        "signin_url": signin_url,
        "current_plugin": current_plugin,
        "current_plugin_state": event.current_plugin_state
    })

@router.get("/display/{plugin_id}")
async def display_plugin(plugin_id: str, request: Request):
    """Load plugin display content"""
    plugin_templates = plugin_manager.get_templates(plugin_id)
    if not plugin_templates:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin_templates.TemplateResponse("display.html", {"request": request})

@router.get("/display/results/{plugin_id}")
async def display_results(plugin_id: str, request: Request, db: Session = Depends(get_db)):
    """Load plugin results page"""
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
        
    # Get results data from current active event
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
         raise HTTPException(status_code=404, detail="No active event")
         
    results = await plugin.get_results(event.id)
    
    plugin_templates = plugin_manager.get_templates(plugin_id)
    if not plugin_templates:
        raise HTTPException(status_code=404, detail="Plugin templates not found")
        
    return plugin_templates.TemplateResponse("results.html", {"request": request, "results": results})
