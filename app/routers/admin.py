from fastapi import APIRouter, Request, Depends, Form, HTTPException, Cookie
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, Participant, Plugin, Interaction

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/login")
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@router.post("/admin/login")
async def admin_login(response: Response, password: str = Form(...), db: Session = Depends(get_db)):
    # Simple check for MVP
    # In reality, verify against DB or env
    # Default is "admin123"
    event = db.query(Event).filter(Event.is_active == True).first()
    # Ensure event exists to check password
    if not event:
        event = Event(title="默认培训活动", host_password_hash="admin123", admin_password_hash="admin123")
        db.add(event)
        db.commit()
        
    if password == event.admin_password_hash or password == "admin123":
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie(key="admin_session", value="authenticated", httponly=True)
        return response
    else:
        return RedirectResponse(url="/admin/login?error=1", status_code=302)

@router.get("/admin")
async def admin_page(request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("admin_session") != "authenticated":
        return RedirectResponse(url="/admin/login")

    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        event = Event(title="默认培训活动", host_password_hash="admin123", admin_password_hash="admin123")
        db.add(event)
        db.commit()
    
    count = db.query(Participant).filter(Participant.event_id == event.id).count()
    
    from app.plugin_manager import plugin_manager
    # get_all_plugins now returns dict of static plugins
    all_plugins = plugin_manager.get_all_plugins()
    
    # Fetch configured interactions
    interactions = db.query(Interaction).filter(Interaction.event_id == event.id).all()
    
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "event": event,
        "count": count,
        "plugins": all_plugins,
        "interactions": interactions
    })

@router.post("/api/admin/update")
async def admin_update(
    request: Request,
    title: str = Form(...),
    logo_url: str = Form(None),
    host_password: str = Form(...),
    admin_password: str = Form(...),
    status: str = Form(...), # pending, running, ended
    db: Session = Depends(get_db)
):
    if request.cookies.get("admin_session") != "authenticated":
        raise HTTPException(status_code=401, detail="Unauthorized")

    event = db.query(Event).filter(Event.is_active == True).first()
    if event:
        event.title = title
        event.logo_url = logo_url
        event.host_password_hash = host_password 
        event.admin_password_hash = admin_password
        event.status = status
        db.commit()
    return {"status": "ok"}

@router.get("/api/admin/interactions")
async def list_interactions(db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        return []
    
    interactions = db.query(Interaction).filter(Interaction.event_id == event.id).all()
    return [{
        "id": i.id,
        "plugin_id": i.plugin_id,
        "name": i.name,
        "config": i.config,
        "is_enabled": i.is_enabled
    } for i in interactions]

@router.post("/api/admin/interactions")
async def create_interaction(data: dict, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=404, detail="No active event")
        
    plugin_id = data.get("plugin_id")
    if not plugin_id:
        raise HTTPException(status_code=400, detail="Plugin ID required")

    # Basic default config if not provided
    config = data.get("config", {})
    name = data.get("name", "New Interaction")

    new_interaction = Interaction(
        event_id=event.id,
        plugin_id=plugin_id,
        name=name,
        config=config,
        is_enabled=False
    )
    
    db.add(new_interaction)
    db.commit()
    db.refresh(new_interaction)
    
    return {"status": "ok", "id": new_interaction.id}

@router.delete("/api/admin/interactions/{interaction_id}")
async def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
         raise HTTPException(status_code=404, detail="Interaction not found")
         
    db.delete(interaction)
    db.commit()
    return {"status": "ok"}
    
@router.post("/api/admin/interactions/{interaction_id}/toggle")
async def toggle_interaction(interaction_id: int, enable: bool, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
         raise HTTPException(status_code=404, detail="Interaction not found")
    
    interaction.is_enabled = enable
    db.commit()
    return {"status": "ok"}

# New Endpoint for Config
@router.post("/api/admin/plugin_config")
async def update_plugin_config(
    request: Request,
    plugin_id: str = Form(...),
    config_json: str = Form(...),
    db: Session = Depends(get_db)
):
    if request.cookies.get("admin_session") != "authenticated":
         raise HTTPException(status_code=401, detail="Unauthorized")

    import json
    try:
        new_config = json.loads(config_json)
    except json.JSONDecodeError:
         # TODO: flash error
         return RedirectResponse(url="/admin?error=invalid_json", status_code=302)

    event = db.query(Event).filter(Event.is_active == True).first()
    if event:
        # Update event-specific config
        current_config = dict(event.plugins_config or {})
        current_config[plugin_id] = new_config
        event.plugins_config = current_config
        
        # Also update global plugin config if needed (optional)
        # plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
        # if plugin:
        #    plugin.config = new_config
        
        db.commit()
        
    return RedirectResponse(url="/admin", status_code=302)

@router.post("/api/admin/reset")
async def admin_reset(db: Session = Depends(get_db)):
    # Deactivate old event
    event = db.query(Event).filter(Event.is_active == True).first()
    if event:
        event.is_active = False
        
    # Create new event
    new_event = Event(title="新培训活动", host_password_hash="admin123")
    db.add(new_event)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)
