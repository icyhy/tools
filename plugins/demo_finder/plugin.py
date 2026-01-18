from app.plugins import BasePlugin
from app.websockets import manager
from app.models import PluginSubmission
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
        # Save submission
        db = SessionLocal()
        try:
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
            submissions = db.query(PluginSubmission).filter(
                PluginSubmission.event_id == event_id,
                PluginSubmission.plugin_id == self.plugin_id
            ).all()
            
            total_submissions = len(submissions)
            # Logic: Correct answer is 16 (1, 2, 4, 8, 16)
            correct_count = 0
            for sub in submissions:
                # data is stored as JSON, ensure we check the right key
                val = sub.data.get("value")
                if str(val).strip() == "16":
                    correct_count += 1
            
            return {
                "total": total_submissions,
                "correct": correct_count
            }
        finally:
            db.close()
