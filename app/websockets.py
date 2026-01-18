from fastapi import WebSocket
from typing import List, Dict

class ConnectionManager:
    def __init__(self):
        # active_connections: List[WebSocket] = []
        # Store connections by role or event for better targeting later
        self.active_connections: Dict[str, List[WebSocket]] = {
            "display": [],
            "host": [],
            "user": []
        }

    async def connect(self, websocket: WebSocket, role: str = "user"):
        await websocket.accept()
        if role not in self.active_connections:
            self.active_connections[role] = []
        self.active_connections[role].append(websocket)

    def disconnect(self, websocket: WebSocket, role: str = "user"):
        if role in self.active_connections:
            if websocket in self.active_connections[role]:
                self.active_connections[role].remove(websocket)

    async def broadcast(self, message: dict):
        # Broadcast to all
        for role_conns in self.active_connections.values():
            for connection in role_conns:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Handle broken pipe or closed connection
                    pass
    
    async def broadcast_to_display(self, message: dict):
        for connection in self.active_connections["display"]:
             try:
                await connection.send_json(message)
             except Exception:
                pass

    async def broadcast_to_host(self, message: dict):
        for connection in self.active_connections["host"]:
             try:
                await connection.send_json(message)
             except Exception:
                pass

    async def broadcast_to_users(self, message: dict):
        for connection in self.active_connections["user"]:
             try:
                await connection.send_json(message)
             except Exception:
                pass

manager = ConnectionManager()
