from fastapi import APIRouter, Request, Depends, Form, HTTPException, Cookie
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, Participant, Plugin

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
    all_plugins = plugin_manager.plugins
    
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "event": event,
        "count": count,
        "plugins": all_plugins
    })

@router.post("/api/admin/update")
async def admin_update(
    request: Request,
    title: str = Form(...),
    logo_url: str = Form(None),
    host_password: str = Form(...),
    admin_password: str = Form(...),
    status: str = Form(...), # pending, running, ended
    enabled_plugins: list = Form([]), # List of checked plugins
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
        event.enabled_plugins = enabled_plugins
        db.commit()
    return RedirectResponse(url="/admin", status_code=302)

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
