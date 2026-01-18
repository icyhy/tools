from fastapi import APIRouter, Request, Depends, Form, Response, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, Participant
from app.plugin_manager import plugin_manager
import uuid
import random

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/signin")
async def signin_page(request: Request, db: Session = Depends(get_db)):
    # Check event status
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event or event.status != "running":
        # Check if user is trying to be host? No, generic signin page.
        # But wait, Host needs to sign in to start the event?
        # Typically Host signs in via same page.
        # If event is pending, User should see "Waiting", but Host should be able to login?
        # Let's allow login page, but maybe show a warning or handle in post?
        # Actually, user requirement: "Otherwise, signin page ... shows no training".
        # But if it shows "No training", how does Host login to start it?
        # Maybe Host logs in via Admin? No, Host is separate role.
        # Let's assume Host uses same signin page.
        # So we should show the page, but maybe with a note.
        # OR: The requirement means "User entering signin page will see No Training".
        # Let's render a different template or pass a flag if not running.
        pass

    # Check if already signed in
    session_token = request.cookies.get("session_token")
    if session_token:
        participant = db.query(Participant).filter(Participant.session_token == session_token).first()
        if participant:
            if participant.role == "host":
                return RedirectResponse(url="/mobile/host", status_code=302)
            else:
                return RedirectResponse(url="/mobile/home", status_code=302)
    
    if not event or event.status != "running":
         return templates.TemplateResponse("mobile_no_training.html", {"request": request, "event": event})
                
    return templates.TemplateResponse("mobile_signin.html", {"request": request})

from app.websockets import manager

@router.post("/api/signin")
async def signin(
    request: Request, 
    response: Response,
    name: str = Form(...), 
    department: str = Form(None),
    role: str = Form("user"), # user or host
    host_password: str = Form(None),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        # Should not happen if display page accessed first, but handle it
        event = Event(title="Default Event", host_password_hash="admin123")
        db.add(event)
        db.commit()
    
    # Handle Host Logic
    if role == "host":
        # Simple check (plain text match for MVP as requested 'admin123' default)
        # In real world, verify hash.
        # User requested: "主持人密码由后台配置...默认admin123"
        if host_password != "admin123" and host_password != event.host_password_hash:
             return templates.TemplateResponse("mobile_signin.html", {
                 "request": request, 
                 "error": "主持人密码错误"
             })
    
    # Create Participant
    session_token = str(uuid.uuid4())
    code4 = f"{random.randint(1000, 9999)}"
    
    participant = Participant(
        event_id=event.id,
        session_token=session_token,
        name=name,
        department=department,
        role=role,
        code4=code4
    )
    db.add(participant)
    db.commit()

    # Notify Display to update count
    count = db.query(Participant).filter(Participant.event_id == event.id).count()
    await manager.broadcast_to_display({"type": "stats_update", "count": count})
    
    # Set Cookie
    redirect_url = "/mobile/host" if role == "host" else "/mobile/home"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(key="session_token", value=session_token, httponly=True)
    return response

@router.get("/mobile/home")
async def mobile_home(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        return RedirectResponse(url="/signin")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant:
        return RedirectResponse(url="/signin")
        
    event = db.query(Event).filter(Event.is_active == True).first()
    
    current_plugin = None
    if event and event.current_plugin_id and event.current_plugin_state == "running":
        current_plugin = event.current_plugin_id
        
    return templates.TemplateResponse("mobile_home.html", {
        "request": request, 
        "participant": participant,
        "current_plugin": current_plugin
    })

@router.get("/mobile/host")
async def mobile_host(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        return RedirectResponse(url="/signin")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        return RedirectResponse(url="/signin")
        
    return templates.TemplateResponse("mobile_host.html", {
        "request": request, 
        "participant": participant,
        "plugins": plugin_manager.plugins  # Pass dict, not values()
    })

@router.get("/mobile/plugin/{plugin_id}")
async def mobile_plugin(plugin_id: str, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        return RedirectResponse(url="/signin")
    
    # Check participant
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant:
        return RedirectResponse(url="/signin")
    
    # Get plugin templates dynamically
    plugin_templates = plugin_manager.get_templates(plugin_id)
    if not plugin_templates:
        raise HTTPException(status_code=404, detail="Plugin not found")
         
    # Return appropriate template based on role
    if participant.role == "host":
        return plugin_templates.TemplateResponse("host.html", {"request": request})
    else:
        return plugin_templates.TemplateResponse("user.html", {"request": request})

@router.get("/user/{plugin_id}")
async def user_plugin(plugin_id: str, request: Request, db: Session = Depends(get_db)):
    plugin_templates = plugin_manager.get_templates(plugin_id)
    if not plugin_templates:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin_templates.TemplateResponse("user.html", {"request": request})

@router.get("/api/training/status")
async def get_training_status(db: Session = Depends(get_db)):
    """获取当前培训状态 - 用于前端轮询"""
    import time
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        return {
            "status": "no_event",
            "plugin_id": None,
            "plugin_state": None,
            "participant_count": 0,
            "timestamp": time.time()
        }
    
    # Count participants for this event
    participant_count = db.query(Participant).filter(Participant.event_id == event.id).count()
    
    return {
        "status": event.status,  # 'running' or 'idle'
        "plugin_id": event.current_plugin_id,
        "plugin_state": event.current_plugin_state,  # 'running', 'results', 'idle'
        "participant_count": participant_count,
        "timestamp": time.time()
    }

@router.get("/api/plugin/{plugin_id}/missing")
async def get_missing_numbers(plugin_id: str, phase: int = 1, db: Session = Depends(get_db)):
    """Get missing numbers for the find numbers game - specific phase"""
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event or not event.plugin_data:
        return {"missing_numbers": []}
    
    import json
    plugin_data = json.loads(event.plugin_data)
    phase_key = f"phase{phase}_missing"
    return {"missing_numbers": plugin_data.get(phase_key, [])}

@router.post("/api/plugin/{plugin_id}/submit")
async def submit_plugin_answer(plugin_id: str, data: dict, request: Request, db: Session = Depends(get_db)):
    """Handle user submission for plugin"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant:
        raise HTTPException(status_code=403, detail="Forbidden")

    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=400, detail="No active event")
        
    if event.current_plugin_id != plugin_id or event.current_plugin_state != "running":
        raise HTTPException(status_code=400, detail="Plugin not running")

    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
        
    await plugin.handle_input(event.id, participant.id, data)
    return {"status": "ok"}

@router.post("/api/plugin/{plugin_id}/start")
async def start_plugin(plugin_id: str, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        raise HTTPException(status_code=403, detail="Forbidden")

    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=400, detail="No active event")

    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
        
    # Update Event State
    event.current_plugin_id = plugin_id
    event.current_plugin_state = "running"
    db.commit()
    
    await plugin.start(event.id)
    
    # Broadcast plugin start to display so it can reload and show game content
    await manager.broadcast_to_display({
        "type": "plugin_start",
        "plugin_id": plugin_id
    })
    
    return {"status": "ok"}

import asyncio

@router.post("/api/plugin/countdown")
async def plugin_countdown(request: Request, data: dict, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        raise HTTPException(status_code=403, detail="Forbidden")

    seconds = data.get("seconds", 10)
    
    # Broadcast countdown start
    await manager.broadcast_to_display({"type": "countdown_start", "seconds": seconds})
    
    # Schedule stop task (in background or simple asyncio.sleep for MVP)
    # Note: blocking the request with sleep is bad practice for production, 
    # but for this MVP single-process server it works if we use asyncio.create_task 
    # or just let the client (host or display) trigger the end?
    # Actually, the user requirement implies "Time ends -> auto show results".
    # Best way: Server background task.
    
    asyncio.create_task(run_countdown_and_stop(seconds, request, db))
    
    return {"status": "ok"}

@router.post("/api/plugin/set_phase")
async def set_plugin_phase(request: Request, data: dict, db: Session = Depends(get_db)):
    """Set the phase/stage of the current plugin"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        raise HTTPException(status_code=403, detail="Forbidden")

    phase = data.get("phase", 1)
    
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=400, detail="No active event")
    
    # Broadcast phase change to display and users
    await manager.broadcast_to_display({
        "type": "plugin_phase_change", 
        "phase": phase,
        "plugin_id": event.current_plugin_id
    })
    await manager.broadcast_to_users({
        "type": "plugin_phase_change", 
        "phase": phase,
        "plugin_id": event.current_plugin_id
    })
    
    return {"status": "ok", "phase": phase}

@router.post("/api/plugin/stop")
async def stop_plugin(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        raise HTTPException(status_code=403, detail="Forbidden")

    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=400, detail="No active event")

    if event.current_plugin_id:
        plugin = plugin_manager.get_plugin(event.current_plugin_id)
        if plugin:
            await plugin.stop(event.id)
            
    event.current_plugin_state = "results"
    db.commit()
    
    # Broadcast stop/results
    await manager.broadcast_to_display({"type": "plugin_end", "plugin_id": event.current_plugin_id})
    await manager.broadcast_to_users({"type": "plugin_end", "plugin_id": event.current_plugin_id})
    await manager.broadcast_to_host({"type": "plugin_end", "plugin_id": event.current_plugin_id})
    
    return {"status": "ok"}

async def run_countdown_and_stop(seconds: int, request: Request, db: Session):
    await asyncio.sleep(seconds)
    # We need a fresh DB session here ideally, or handle careful scope.
    # Re-using 'db' from dependency might be closed.
    # So let's instantiate a new session or call the stop_plugin logic internally.
    # For MVP simplicity, let's just trigger the broadcast "plugin_end" and update DB.
    # But wait, we need to update DB state to 'results'.
    
    from app.database import SessionLocal
    new_db = SessionLocal()
    try:
        event = new_db.query(Event).filter(Event.is_active == True).first()
        if event and event.current_plugin_state == "running":
             event.current_plugin_state = "results"
             new_db.commit()
             
             if event.current_plugin_id:
                await manager.broadcast_to_display({"type": "plugin_end", "plugin_id": event.current_plugin_id})
                await manager.broadcast_to_users({"type": "plugin_end", "plugin_id": event.current_plugin_id})
                await manager.broadcast_to_host({"type": "plugin_end", "plugin_id": event.current_plugin_id})
    except Exception as e:
        print(f"Error in countdown task: {e}")
    finally:
        new_db.close()

@router.post("/api/plugin/reset")
async def reset_plugin(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        raise HTTPException(status_code=403, detail="Forbidden")

    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=400, detail="No active event")

    # Stop current plugin if any
    if event.current_plugin_id:
        plugin = plugin_manager.get_plugin(event.current_plugin_id)
        if plugin:
            await plugin.stop(event.id)

    # Reset state to idle
    event.current_plugin_id = None
    event.current_plugin_state = "idle"
    db.commit()
    
    # Broadcast reset
    await manager.broadcast_to_display({"type": "plugin_reset"})
    await manager.broadcast_to_users({"type": "plugin_reset"})
    await manager.broadcast_to_host({"type": "plugin_reset"})
    
    return {"status": "ok"}

@router.get("/api/plugin/{plugin_id}/config")
async def get_plugin_config(plugin_id: str, db: Session = Depends(get_db)):
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
        
    event = db.query(Event).filter(Event.is_active == True).first()
    config = {}
    if event and event.plugins_config:
        config = event.plugins_config.get(plugin_id, {})
        
    if not config:
        config = plugin.meta.get("config", {})
        
    return config

@router.post("/api/plugin/{plugin_id}/submit")
async def submit_plugin(plugin_id: str, request: Request, data: dict, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant:
        raise HTTPException(status_code=403, detail="Forbidden")

    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=400, detail="No active event")
        
    if event.current_plugin_id != plugin_id or event.current_plugin_state != "running":
        raise HTTPException(status_code=400, detail="Plugin not running")

    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
        
    await plugin.handle_input(event.id, participant.id, data)
    return {"status": "ok"}

@router.get("/host/{plugin_id}")
async def host_plugin(plugin_id: str, request: Request, db: Session = Depends(get_db)):
    plugin_templates = plugin_manager.get_templates(plugin_id)
    if not plugin_templates:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin_templates.TemplateResponse("host.html", {"request": request})
