from app.plugin_manager import BasePlugin
from app.websockets import manager
from app.models import PluginSubmission, Event
from app.database import SessionLocal
import json
import random

class Plugin(BasePlugin):
    async def start(self, event_id: int):
        """Initialize the game - generate missing numbers for all 3 phases"""
        # Generate 3 independent sets of 10 missing numbers each
        phase1_missing = random.sample(range(1, 101), 10)
        phase2_missing = random.sample(range(1, 101), 10)
        phase3_missing = random.sample(range(1, 101), 10)
        
        phase1_missing.sort()
        phase2_missing.sort()
        phase3_missing.sort()
        
        # Store all phase data in Event.plugin_data
        db = SessionLocal()
        try:
            event = db.query(Event).filter(Event.id == event_id).first()
            if event:
                event.plugin_data = json.dumps({
                    "phase1_missing": phase1_missing,
                    "phase2_missing": phase2_missing,
                    "phase3_missing": phase3_missing
                })
                db.commit()
        finally:
            db.close()
        
        # Broadcast start to all clients
        await manager.broadcast_to_display({"type": "plugin_start", "plugin_id": self.plugin_id})
        await manager.broadcast_to_users({"type": "plugin_start", "plugin_id": self.plugin_id})
        await manager.broadcast_to_host({"type": "plugin_start", "plugin_id": self.plugin_id})

    async def stop(self, event_id: int):
        """Stop the game"""
        pass

    async def handle_input(self, event_id: int, user_id: int, data: dict):
        """Handle user submission for a specific phase"""
        # Get phase-specific missing numbers from Event
        db = SessionLocal()
        try:
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event or not event.plugin_data:
                return
            
            plugin_data = json.loads(event.plugin_data)
            
            # Get the phase and submitted numbers
            phase = data.get("phase", 1)
            submitted = data.get("submitted_numbers", [])
            submitted_set = set(submitted)
            
            # Get the correct missing numbers for this phase
            phase_key = f"phase{phase}_missing"
            missing_numbers = set(plugin_data.get(phase_key, []))
            
            # Calculate score (correct guesses)
            correct_guesses = submitted_set & missing_numbers
            score = len(correct_guesses)
            
            # Check if user already submitted for this phase
            existing = db.query(PluginSubmission).filter(
                PluginSubmission.event_id == event_id,
                PluginSubmission.plugin_id == self.plugin_id,
                PluginSubmission.user_id == user_id
            ).first()
            
            if existing:
                # Update existing submission
                submission_data = json.loads(existing.data) if isinstance(existing.data, str) else existing.data
                submission_data[f"phase{phase}_submitted"] = submitted
                submission_data[f"phase{phase}_score"] = score
                existing.data = json.dumps(submission_data)
                db.commit()
            else:
                # Create new submission
                submission = PluginSubmission(
                    event_id=event_id,
                    plugin_id=self.plugin_id,
                    user_id=user_id,
                    data=json.dumps({
                        f"phase{phase}_submitted": submitted,
                        f"phase{phase}_score": score
                    })
                )
                db.add(submission)
                db.commit()
        finally:
            db.close()

    async def get_results(self, event_id: int) -> dict:
        """Calculate and return statistics for all phases"""
        db = SessionLocal()
        try:
            # Get missing numbers for all phases
            event = db.query(Event).filter(Event.id == event_id).first()
            phase_data = {
                "phase1_missing": [],
                "phase2_missing": [],
                "phase3_missing": []
            }
            if event and event.plugin_data:
                plugin_data = json.loads(event.plugin_data)
                phase_data = plugin_data
            
            # Get all submissions
            submissions = db.query(PluginSubmission).filter(
                PluginSubmission.event_id == event_id,
                PluginSubmission.plugin_id == self.plugin_id
            ).all()
            
            total_participants = len(submissions)
            if total_participants == 0:
                return {
                    "total_participants": 0,
                    "phase1": {"average": 0, "max": 0, "missing": phase_data.get("phase1_missing", [])},
                    "phase2": {"average": 0, "max": 0, "missing": phase_data.get("phase2_missing", [])},
                    "phase3": {"average": 0, "max": 0, "missing": phase_data.get("phase3_missing", [])}
                }
            
            # Collect scores for each phase
            phase1_scores = []
            phase2_scores = []
            phase3_scores = []
            
            for sub in submissions:
                submission_data = json.loads(sub.data) if isinstance(sub.data, str) else sub.data
                
                if "phase1_score" in submission_data:
                    phase1_scores.append(submission_data["phase1_score"])
                if "phase2_score" in submission_data:
                    phase2_scores.append(submission_data["phase2_score"])
                if "phase3_score" in submission_data:
                    phase3_scores.append(submission_data["phase3_score"])
            
            # Calculate statistics for each phase
            def calc_stats(scores):
                if not scores:
                    return {"average": 0, "max": 0}
                return {
                    "average": round(sum(scores) / len(scores), 1),
                    "max": max(scores)
                }
            
            return {
                "total_participants": total_participants,
                "phase1": {
                    **calc_stats(phase1_scores),
                    "missing": phase_data.get("phase1_missing", [])
                },
                "phase2": {
                    **calc_stats(phase2_scores),
                    "missing": phase_data.get("phase2_missing", [])
                },
                "phase3": {
                    **calc_stats(phase3_scores),
                    "missing": phase_data.get("phase3_missing", [])
                }
            }
        finally:
            db.close()

# Create plugin instance
import os
plugin_instance = Plugin(
    plugin_id="demo_finder",
    path=os.path.dirname(__file__)
)
