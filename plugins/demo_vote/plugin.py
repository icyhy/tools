from app.plugins import BasePlugin
from app.websockets import manager
from app.models import PluginSubmission, Event
from app.database import SessionLocal
import json

class Plugin(BasePlugin):
    async def start(self, event_id: int):
        await manager.broadcast_to_display({"type": "plugin_start", "plugin_id": self.plugin_id})
        await manager.broadcast_to_users({"type": "plugin_start", "plugin_id": self.plugin_id})
        await manager.broadcast_to_host({"type": "plugin_start", "plugin_id": self.plugin_id})

    async def stop(self, event_id: int):
        pass

    async def handle_input(self, event_id: int, user_id: int, data: dict):
        db = SessionLocal()
        try:
            # Check if user already voted? For MVP allow re-vote or multiple?
            # Let's simple append for now. Or uniqueness?
            # Usually voting is once.
            existing = db.query(PluginSubmission).filter(
                PluginSubmission.event_id == event_id,
                PluginSubmission.plugin_id == self.plugin_id,
                PluginSubmission.user_id == user_id
            ).first()
            
            if existing:
                existing.data = data
            else:
                submission = PluginSubmission(
                    event_id=event_id,
                    plugin_id=self.plugin_id,
                    user_id=user_id,
                    data=data
                )
                db.add(submission)
            db.commit()
        finally:
            db.close()

    async def get_results(self, event_id: int) -> dict:
        db = SessionLocal()
        try:
            # Get event config to know options
            event = db.query(Event).filter(Event.id == event_id).first()
            config = event.plugins_config.get(self.plugin_id) if event.plugins_config else {}
            if not config:
                config = self.meta.get("config", {})
                
            options = config.get("options", [])
            
            submissions = db.query(PluginSubmission).filter(
                PluginSubmission.event_id == event_id,
                PluginSubmission.plugin_id == self.plugin_id
            ).all()
            
            # Count votes
            counts = {opt: 0 for opt in options}
            total = 0
            
            for sub in submissions:
                choice = sub.data.get("value")
                if choice in counts:
                    counts[choice] += 1
                total += 1
            
            return {
                "total": total,
                "counts": counts,
                "question": config.get("question")
            }
        finally:
            db.close()
