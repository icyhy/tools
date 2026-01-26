from fastapi import APIRouter, Request, Depends, Form, Response, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, Participant
from app.models import Event, Participant, Interaction
from app.plugin_manager import plugin_manager
import uuid
import random
import asyncio

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/signin")
async def signin_page(request: Request, db: Session = Depends(get_db)):
    # Check event status
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event or event.status != "running":
         return templates.TemplateResponse("mobile_no_training.html", {"request": request, "event": event})
                
    # Check if already signed in
    session_token = request.cookies.get("session_token")
    if session_token:
        participant = db.query(Participant).filter(Participant.session_token == session_token).first()
        if participant:
            if participant.role == "host":
                return RedirectResponse(url="/mobile/host", status_code=302)
            else:
                return RedirectResponse(url="/mobile/home", status_code=302)
    
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
        if host_password != "admin123" and host_password != event.host_password_hash:
             return templates.TemplateResponse("mobile_signin.html", {
                 "request": request, 
                 "error": "主持人密码错误"
             })
    
    # Check if participant already exists for this event and name (and user role)
    if role == "user":
        existing_participant = db.query(Participant).filter(
            Participant.event_id == event.id,
            Participant.name == name,
            Participant.role == "user"
        ).first()

        if existing_participant:
            session_token = str(uuid.uuid4())
            existing_participant.session_token = session_token
            if department:
                existing_participant.department = department
            db.commit()
            
            redirect_url = "/mobile/home"
            response = RedirectResponse(url=redirect_url, status_code=302)
            response.set_cookie(key="session_token", value=session_token, httponly=True)
            return response
    
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
    
    current_interaction_id = None
    if event and event.current_interaction_id and event.current_plugin_state == "running":
        current_interaction_id = event.current_interaction_id
        
    return templates.TemplateResponse("mobile_home.html", {
        "request": request, 
        "participant": participant,
        "current_plugin": current_interaction_id
    })

@router.get("/mobile/host")
async def mobile_host(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        return RedirectResponse(url="/signin")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        return RedirectResponse(url="/signin")
        
    event = db.query(Event).filter(Event.is_active == True).first()
    interactions = []
    if event:
        interactions = db.query(Interaction)\
            .filter(Interaction.event_id == event.id, Interaction.is_enabled == True)\
            .all()
        
    return templates.TemplateResponse("mobile_host.html", {
        "request": request, 
        "participant": participant,
        "interactions": interactions
    })

@router.get("/mobile/plugin/{interaction_id}")
async def mobile_plugin(interaction_id: int, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        return RedirectResponse(url="/signin")
    
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant:
        return RedirectResponse(url="/signin")
    
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
         raise HTTPException(status_code=404, detail="Interaction not found")

    plugin_id = interaction.plugin_id
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
         raise HTTPException(status_code=404, detail="Plugin code not found")

    plugin_templates = plugin_manager.get_templates(plugin_id)
    if not plugin_templates:
        raise HTTPException(status_code=404, detail="Plugin templates not found")

    context = {
        "request": request,
        "config": interaction.config,
        "plugin_name": interaction.name,
        "plugin_meta": plugin.meta,
        "interaction_id": interaction.id
    }

    if participant.role == "host":
        return plugin_templates.TemplateResponse("host.html", context)
    else:
        return plugin_templates.TemplateResponse("user.html", context)

@router.post("/api/host/show_stats")
async def host_show_stats(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role not in ["host", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    event = db.query(Event).filter(Event.is_active == True).first()
    if event:
        await manager.broadcast({
            "type": "show_stats"
        })
        event.current_plugin_state = "stats"
        db.commit()
    
    return {"status": "ok"}

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
    
    participant_count = db.query(Participant).filter(Participant.event_id == event.id).count()
    
    return {
        "status": event.status,  # 'running' or 'idle'
        "plugin_id": event.current_interaction_id, # Returning interaction_id as plugin_id for frontend compat
        "plugin_state": event.current_plugin_state,  # 'running', 'results', 'idle'
        "participant_count": participant_count,
        "timestamp": time.time()
    }

@router.get("/api/plugin/{interaction_id}/missing")
async def get_missing_numbers(interaction_id: int, phase: int = 1, db: Session = Depends(get_db)):
    """Get missing numbers for the find numbers game - specific phase"""
    # Note: Plugin data storage might need refactoring if it was keyed by ID. 
    # Current implementation uses 'plugin_data' column in Event (legacy/general).
    # For now we keep using 'plugin_data' but check if we need to scope by interaction.
    # The original implementation used 'plugin_data' on Event. 
    # If multiple interactions use this, they will overwrite each other. 
    # Ideally Interaction model should store state, or PluginSubmission.
    # For MVP of 'Find Numbers', assuming one instance per event is fine, OR we key by interaction_id.
    
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event or not event.plugin_data:
        return {"missing_numbers": []}
    
    plugin_data = event.plugin_data or {}
    phase_key = f"phase{phase}_missing"
    return {"missing_numbers": plugin_data.get(phase_key, [])}

@router.post("/api/plugin/{interaction_id}/submit")
async def submit_plugin_answer(interaction_id: int, data: dict, request: Request, db: Session = Depends(get_db)):
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
        
    if event.current_interaction_id != interaction_id or event.current_plugin_state != "running":
        raise HTTPException(status_code=400, detail="Plugin not running")

    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
        
    plugin = plugin_manager.get_plugin(interaction.plugin_id)
    if not plugin:
         raise HTTPException(status_code=404, detail="Plugin code not found")

    try:
        # TODO: update handle_input to accept interaction_id if needed, or stick to event_id
        # Ideally we pass interaction_id so plugin can store submissions keyed by it.
        # But BasePlugin.handle_input signature is (event_id, user_id, data).
        # We can pass interaction_id in 'data' or update method signature.
        # Let's pass it in data for minimal refactor of Plugin interface.
        data['_interaction_id'] = interaction_id
        await plugin.handle_input(event.id, participant.id, data)
        
        participant.interaction_count = (participant.interaction_count or 0) + 1
        db.commit()
    except Exception as e:
        print(f"Plugin input error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"status": "ok"}

@router.get("/api/stats/count")
async def get_stats_count(db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        return {"count": 0}
    count = db.query(Participant).filter(Participant.event_id == event.id).count()
    return {"count": count}

@router.post("/api/plugin/{interaction_id}/start")
async def start_plugin(interaction_id: int, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        raise HTTPException(status_code=403, detail="Forbidden")

    event = db.query(Event).filter(Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=400, detail="No active event")

    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
         raise HTTPException(status_code=404, detail="Interaction not found")
         
    plugin = plugin_manager.get_plugin(interaction.plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
        
    # Update Event State
    event.current_interaction_id = interaction_id
    event.current_plugin_state = "running"
    # Legacy field cleanup if necessary (current_plugin_id)
    db.commit()
    
    # Pass interaction config if needed? 
    # 'start' method might need to know which interaction it is.
    # We can overload 'start' to take interaction_id or just event_id.
    # Currently it takes event_id.
    await plugin.start(event.id)
    
    await manager.broadcast_to_display({
        "type": "plugin_start",
        "plugin_id": interaction_id # Send interaction ID as plugin_id
    })
    
    return {"status": "ok"}

@router.post("/api/plugin/countdown")
async def plugin_countdown(request: Request, data: dict, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    participant = db.query(Participant).filter(Participant.session_token == session_token).first()
    if not participant or participant.role != "host":
        raise HTTPException(status_code=403, detail="Forbidden")

    seconds = data.get("seconds", 10)
    
    await manager.broadcast_to_display({"type": "countdown_start", "seconds": seconds})
    
    asyncio.create_task(run_countdown_and_stop(seconds, request, db))
    
    return {"status": "ok"}

@router.post("/api/plugin/set_phase")
async def set_plugin_phase(request: Request, data: dict, db: Session = Depends(get_db)):
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
    
    # Broadcast phase change
    await manager.broadcast_to_display({
        "type": "plugin_phase_change", 
        "phase": phase,
        "plugin_id": event.current_interaction_id
    })
    await manager.broadcast_to_users({
        "type": "plugin_phase_change", 
        "phase": phase,
        "plugin_id": event.current_interaction_id
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

    interaction_id = event.current_interaction_id
    if interaction_id:
        # We need plugin_id to stop it? 
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if interaction:
             plugin = plugin_manager.get_plugin(interaction.plugin_id)
             if plugin:
                 await plugin.stop(event.id)
            
    event.current_plugin_state = "results"
    db.commit()
    
    # Broadcast stop/results
    await manager.broadcast_to_display({"type": "plugin_end", "plugin_id": interaction_id})
    await manager.broadcast_to_users({"type": "plugin_end", "plugin_id": interaction_id})
    await manager.broadcast_to_host({"type": "plugin_end", "plugin_id": interaction_id})
    
    return {"status": "ok"}

async def run_countdown_and_stop(seconds: int, request: Request, db: Session):
    await asyncio.sleep(seconds)
    
    from app.database import SessionLocal
    new_db = SessionLocal()
    try:
        event = new_db.query(Event).filter(Event.is_active == True).first()
        if event and event.current_plugin_state == "running":
             event.current_plugin_state = "results"
             new_db.commit()
             
             if event.current_interaction_id:
                await manager.broadcast_to_display({"type": "plugin_end", "plugin_id": event.current_interaction_id})
                await manager.broadcast_to_users({"type": "plugin_end", "plugin_id": event.current_interaction_id})
                await manager.broadcast_to_host({"type": "plugin_end", "plugin_id": event.current_interaction_id})
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

    if event.current_interaction_id:
        interaction = db.query(Interaction).filter(Interaction.id == event.current_interaction_id).first()
        if interaction:
            plugin = plugin_manager.get_plugin(interaction.plugin_id)
            if plugin:
                await plugin.stop(event.id)

    event.current_interaction_id = None
    event.current_plugin_state = "idle"
    db.commit()
    
    await manager.broadcast_to_display({"type": "plugin_reset"})
    await manager.broadcast_to_users({"type": "plugin_reset"})
    await manager.broadcast_to_host({"type": "plugin_reset"})
    
    return {"status": "ok"}

@router.get("/api/plugin/{interaction_id}/config")
async def get_plugin_config(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
         raise HTTPException(status_code=404, detail="Interaction not found")
    
    config = interaction.config or {}
    # Merge with default if needed, or just return interaction config
    # Previously we merged with plugin.meta.config
    
    plugin = plugin_manager.get_plugin(interaction.plugin_id)
    if plugin:
        default_config = plugin.meta.get("config", {})
        # Merge: default updated by interaction config
        final_config = default_config.copy()
        final_config.update(config)
        return final_config
        
    return config
