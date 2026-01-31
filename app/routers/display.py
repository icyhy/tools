from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, Participant, Interaction
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
    base_url = get_server_url()
    signin_url = f"{base_url}/signin"
    qr_code = generate_qr_base64(signin_url)
    
    # Check current interaction state
    current_interaction_id = None
    if event.current_interaction_id and event.current_plugin_state in ["running", "results"]:
        current_interaction_id = event.current_interaction_id
        
    return templates.TemplateResponse("index.html", {
        "request": request,
        "event": event,
        "participant_count": count,
        "qr_code": qr_code,
        "signin_url": signin_url,
        "current_plugin": current_interaction_id, # Template expects 'current_plugin' variable
        "current_plugin_state": event.current_plugin_state
    })

@router.get("/display/{interaction_id_or_plugin_id}")
async def display_plugin(interaction_id_or_plugin_id: str, request: Request, db: Session = Depends(get_db)):
    """Load plugin display content by interaction ID or plugin name string"""
    interaction = None
    plugin_id = interaction_id_or_plugin_id
    interaction_id = None

    # Try to parse as interaction ID
    if interaction_id_or_plugin_id.isdigit():
        interaction_id = int(interaction_id_or_plugin_id)
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if interaction:
            plugin_id = interaction.plugin_id
    
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
    plugin_templates = plugin_manager.get_templates(plugin_id)
    if not plugin_templates:
        raise HTTPException(status_code=404, detail="Plugin templates not found")
        
    # Config comes from Interaction if available, otherwise from plugin meta
    config = interaction.config.copy() if interaction else plugin.meta.get("config", {})
    
    context = {
        "request": request,
        "config": config,
        "plugin_name": interaction.name if interaction else plugin.name,
        "plugin_meta": plugin.meta,
        "interaction_id": interaction_id or 0,
        "plugin_id": plugin_id
    }
    return plugin_templates.TemplateResponse("display.html", context)

@router.get("/display/results/{interaction_id_or_plugin_id}")
async def display_results(interaction_id_or_plugin_id: str, request: Request, db: Session = Depends(get_db)):
    """Load plugin results page by interaction ID or plugin name"""
    interaction = None
    plugin_id = interaction_id_or_plugin_id
    event_id = None
    
    if interaction_id_or_plugin_id.isdigit():
        iid = int(interaction_id_or_plugin_id)
        interaction = db.query(Interaction).filter(Interaction.id == iid).first()
        if interaction:
            plugin_id = interaction.plugin_id
            event_id = interaction.event_id

    if not event_id:
        # Fallback to active event
        event = db.query(Event).filter(Event.is_active == True).first()
        if event:
            event_id = event.id

    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
    results = await plugin.get_results(event_id)
    
    plugin_templates = plugin_manager.get_templates(plugin_id)
    if not plugin_templates:
        raise HTTPException(status_code=404, detail="Plugin templates not found")
        
    context = {
        "request": request,
        "results": results,
        "config": interaction.config if interaction else plugin.meta.get("config", {}),
        "plugin_name": interaction.name if interaction else plugin.name,
        "plugin_meta": plugin.meta,
        "interaction_id": interaction.id if interaction else 0,
        "plugin_id": plugin_id
    }
    return plugin_templates.TemplateResponse("results.html", context)

@router.get("/display/stats")
async def display_stats(request: Request, db: Session = Depends(get_db)):
    """Show user interaction statistics"""
    event = db.query(Event).filter(Event.is_active == True).first()
    
    # Get top 3 participants by interaction count
    top_participants = db.query(Participant)\
        .filter(Participant.event_id == (event.id if event else None))\
        .order_by(Participant.interaction_count.desc())\
        .limit(3)\
        .all()
        
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "top_participants": top_participants
    })
