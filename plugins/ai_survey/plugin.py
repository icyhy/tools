from app.plugin_manager import BasePlugin
from app.websockets import manager
from app.models import PluginSubmission, Event, Interaction
from app.database import SessionLocal
import json

class Plugin(BasePlugin):
    async def start(self, event_id: int):
        # Clear previous submissions for this plugin and event to allow fresh start
        db = SessionLocal()
        try:
            db.query(PluginSubmission).filter(
                PluginSubmission.event_id == event_id,
                PluginSubmission.plugin_id == self.plugin_id
            ).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Failed to clear submissions: {e}")
        finally:
            db.close()

        await manager.broadcast_to_display({"type": "plugin_start", "plugin_id": self.plugin_id})
        await manager.broadcast_to_users({"type": "plugin_start", "plugin_id": self.plugin_id})
        await manager.broadcast_to_host({"type": "plugin_start", "plugin_id": self.plugin_id})

    async def stop(self, event_id: int):
        pass

    async def handle_input(self, event_id: int, user_id: int, data: dict):
        db = SessionLocal()
        try:
            # AI tool survey usually allows updating choice or just one-time submission.
            # Here we follow the vote pattern: re-submission updates the previous one.
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
            
            # Broadcast update to display for real-time results
            results = await self.get_results(event_id)
            await manager.broadcast_to_display({"type": "plugin_update", "plugin_id": self.plugin_id, "data": results})
            
        finally:
            db.close()

    async def get_results(self, event_id: int) -> dict:
        db = SessionLocal()
        try:
            # Get event config to know options
            event = db.query(Event).filter(Event.id == event_id).first()
            
            # Attempt to find configuration from the current active interaction
            config = {}
            if event and event.current_interaction_id:
                interaction = db.query(Interaction).filter(Interaction.id == event.current_interaction_id).first()
                if interaction and interaction.plugin_id == self.plugin_id:
                    config = interaction.config or {}
            
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
