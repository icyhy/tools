from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app.websockets import manager

# Create tables
import app.models
Base.metadata.create_all(bind=engine)

app = FastAPI(title="互动培训系统")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Load plugins
from app.plugin_manager import plugin_manager

@app.on_event("startup")
async def startup_event():
    plugin_manager.load_plugins()

# Mount plugins static
import os
if not os.path.exists("plugins"):
    os.makedirs("plugins")
app.mount("/plugins", StaticFiles(directory="plugins"), name="plugins")

from app.routers import display, mobile, admin
# from app.plugin_loader import plugin_router # Comment out old dynamic loader if it exists or conflicts

app.include_router(display.router)
app.include_router(mobile.router)
app.include_router(admin.router)
# app.include_router(plugin_router)

@app.websocket("/ws/{role}")
async def websocket_endpoint(websocket: WebSocket, role: str):
    await manager.connect(websocket, role)
    try:
        while True:
            # Keep alive and listen for messages (e.g. from host)
            data = await websocket.receive_text()
            # Echo or process (Simple ping/pong or logic)
            # await manager.broadcast(f"Client says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, role)

# @app.get("/")
# async def root(request: Request):
#    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
