from app.plugin_manager import BasePlugin
from app.websockets import manager
from app.models import PluginSubmission, Event
from app.database import SessionLocal
import random
import time
import os

class Plugin(BasePlugin):
    def __init__(self, plugin_id: str, path: str):
        super().__init__(plugin_id, path)
        self.state = {
            "stage": 0, # 0: Ready, 1: Stage 1, 2: Stage 2, 3: Stage 3, 4: Finished
            "numbers": [],
            "missing_numbers": [],
            "start_time": 0,
            "total_numbers": 100,
            "missing_count": 10
        }
    
    def generate_numbers(self):
        # Generate 1-100 numbers
        all_nums = list(range(1, 101))
        # Randomly remove some
        missing = sorted(random.sample(all_nums, self.state.get("missing_count", 10)))
        present = [n for n in all_nums if n not in missing]
        
        self.state["missing_numbers"] = missing
        self.state["numbers"] = present
        return present, missing

    async def start(self, event_id: int):
        """Initialize original find_numbers logic"""
        self.state["stage"] = 1
        self.generate_numbers()
        await manager.broadcast_to_display({
            "type": "plugin_start",
            "plugin_id": self.plugin_id
        })

    async def stop(self, event_id: int):
        self.state["stage"] = 0

    async def handle_input(self, event_id: int, user_id: int, data: dict):
        """处理用户提交 - 统一接口用于API调用"""
        db = SessionLocal()
        try:
            # 从data中获取answers
            answers = data.get("answers", [])
            
            # 计算答案
            missing = set(self.state["missing_numbers"])
            submitted = set(answers)
            correct = missing.intersection(submitted)
            score = len(correct)
            
            # 保存或更新提交记录
            existing = db.query(PluginSubmission).filter(
                PluginSubmission.event_id == event_id,
                PluginSubmission.plugin_id == self.plugin_id,
                PluginSubmission.user_id == user_id
            ).first()
            
            sub_data = {"answers": answers, "score": score}
            
            if existing:
                existing.data = sub_data
                db.commit()
            else:
                submission = PluginSubmission(
                    event_id=event_id,
                    plugin_id=self.plugin_id,
                    user_id=user_id,
                    data=sub_data
                )
                db.add(submission)
                db.commit()
            
        finally:
            db.close()

    async def get_results(self, event_id: int) -> dict:
        """获取结果统计"""
        db = SessionLocal()
        try:
            subs = db.query(PluginSubmission).filter(
                PluginSubmission.event_id == event_id,
                PluginSubmission.plugin_id == self.plugin_id
            ).all()
            
            scores = [(s.user_id, s.data.get("score", 0)) for s in subs]
            score_values = [score for _, score in scores]
            missing_count = self.state.get("missing_count", 10) or 0
            average_score = sum(score_values) / len(score_values) if score_values else 0
            accuracy = (average_score / missing_count * 100) if missing_count else 0
            top_users = [
                {"user_id": user_id, "score": score}
                for user_id, score in sorted(scores, key=lambda item: item[1], reverse=True)[:5]
            ]
            return {
                "participant_count": len(subs),
                "average_score": average_score,
                "accuracy": accuracy,
                "missing_numbers": self.state.get("missing_numbers", []),
                "top_users": top_users
            }
        finally:
            db.close()
