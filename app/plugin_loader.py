import importlib
import os
import json
from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Participant, Plugin as PluginModel
from app.websockets import manager

# Plugin Registry
loaded_plugins = {}
plugin_router = APIRouter()

# Helper to load plugins
def load_plugins():
    plugins_dir = "app/plugins"
    if not os.path.exists(plugins_dir):
        return

    for name in os.listdir(plugins_dir):
        path = os.path.join(plugins_dir, name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "plugin.py")):
            try:
                module = importlib.import_module(f"app.plugins.{name}.plugin")
                # Assume class name is PascalCase of folder name + Plugin, or standardized
                # For MVP, let's look for a class named 'FindNumbersPlugin' specifically or generic
                # Better: scan for class with id
                
                # Dynamic instantiation
                if hasattr(module, "FindNumbersPlugin"):
                    instance = module.FindNumbersPlugin(manager)
                    loaded_plugins[instance.id] = instance
                    print(f"Loaded plugin: {instance.name}")
            except Exception as e:
                print(f"Failed to load plugin {name}: {e}")

# Call load on startup
load_plugins()

# Dynamic Routes for Plugins
@plugin_router.get("/display/{plugin_id}")
async def plugin_display(plugin_id: str, request: Request):
    if plugin_id not in loaded_plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # We need to render the plugin's template. 
    # Since templates are in subfolders, we need to tell Jinja2
    # Simple hack: read file content and use Template(str) or configure Jinja loader
    # For MVP: Read content and return HTMLResponse or use Jinja with multiple dirs
    
    # Better approach: Add plugin dirs to Jinja templates
    plugin_templates = Jinja2Templates(directory=f"app/plugins/{plugin_id}/templates")
    return plugin_templates.TemplateResponse("display.html", {"request": request})

@plugin_router.get("/user/{plugin_id}")
async def plugin_user(plugin_id: str, request: Request):
    if plugin_id not in loaded_plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    plugin_templates = Jinja2Templates(directory=f"app/plugins/{plugin_id}/templates")
    return plugin_templates.TemplateResponse("user.html", {"request": request})

@plugin_router.get("/host/{plugin_id}")
async def plugin_host(plugin_id: str, request: Request):
    if plugin_id not in loaded_plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    plugin_templates = Jinja2Templates(directory=f"app/plugins/{plugin_id}/templates")
    return plugin_templates.TemplateResponse("host.html", {"request": request})

@plugin_router.post("/api/plugin/{plugin_id}/control")
async def plugin_control(plugin_id: str, payload: dict = Body(...)):
    if plugin_id not in loaded_plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = loaded_plugins[plugin_id]
    action = payload.get("action")
    
    if action == "start":
        stage = payload.get("stage", 1)
        await plugin.start_stage(stage)
    elif action == "stop":
        await plugin.stop()
    
    return {"status": "ok"}

@plugin_router.post("/api/plugin/{plugin_id}/input")
async def plugin_input(plugin_id: str, request: Request, payload: dict = Body(...)):
    if plugin_id not in loaded_plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=403, detail="Not signed in")
        
    plugin = loaded_plugins[plugin_id]
    await plugin.handle_user_input(session_token, payload)
    return {"status": "ok"}
