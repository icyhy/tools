import random
import time
from typing import List, Dict, Any, Optional
from app.database import SessionLocal
from app.models import Event, PluginSubmission

class FindNumbersPlugin:
    def __init__(self):
        self.id = "find_numbers"
        self.plugin_id = "find_numbers"  # 添加这个属性用于兼容性
        self.name = "找数字规律"
        self.state = {
            "stage": 0, # 0: Ready, 1: Stage 1, 2: Stage 2, 3: Stage 3, 4: Finished
            "numbers": [],
            "missing_numbers": [],
            "start_time": 0,
            "end_time": 0,
            "results": {}, # user_id -> {score: int, answers: List[int]}
            "total_numbers": 100,
            "missing_count": 10
        }
    
    def generate_numbers(self):
        # Generate 1-100 numbers
        all_nums = list(range(1, 101))
        # Randomly remove some
        missing = sorted(random.sample(all_nums, self.state["missing_count"]))
        present = [n for n in all_nums if n not in missing]
        
        self.state["missing_numbers"] = missing
        self.state["numbers"] = present
        return present, missing

    def start_stage(self, stage: int):
        self.state["stage"] = stage
        self.state["results"] = {}
        
        self.generate_numbers()
        self.state["start_time"] = time.time()
        self.state["end_time"] = self.state["start_time"] + 30
        
        return {
            "type": "game_start",
            "plugin_id": self.id,
            "stage": stage,
            "numbers": self.state["numbers"],
            "duration": 30,
            "missing_count": len(self.state["missing_numbers"])
        }

    def stop_stage(self):
        stats = self.calculate_stats()
        self.state["stage"] = 0
        
        return {
            "type": "game_end",
            "plugin_id": self.id,
            "results": stats
        }

    def handle_submit(self, user_id: str, answers: List[int]):
        # Validate answers
        missing = set(self.state["missing_numbers"])
        submitted = set(answers)
        
        correct = missing.intersection(submitted)
        score = len(correct)
        
        self.state["results"][user_id] = {
            "score": score,
            "total_missing": len(missing),
            "answers": answers,
            "correct_count": len(correct)
        }
        
        return {
            "user_id": user_id,
            "score": score,
            "correct": list(correct)
        }
    
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
            
            submission_data = {
                "answers": answers,
                "score": score,
                "correct_count": len(correct),
                "stage": self.state["stage"]
            }
            
            if existing:
                existing.data = submission_data
                db.commit()
            else:
                submission = PluginSubmission(
                    event_id=event_id,
                    plugin_id=self.plugin_id,
                    user_id=user_id,
                    data=submission_data
                )
                db.add(submission)
                db.commit()
            
            # 更新内存中的结果
            self.state["results"][str(user_id)] = {
                "score": score,
                "total_missing": len(missing),
                "answers": answers,
                "correct_count": len(correct)
            }
            
        finally:
            db.close()

    def calculate_stats(self):
        total_users = len(self.state["results"])
        if total_users == 0:
            return {"accuracy": 0, "completion_rate": 0, "top_users": [], "missing_numbers": self.state["missing_numbers"]}
            
        total_possible_score = len(self.state["missing_numbers"]) * total_users
        total_actual_score = sum(r["score"] for r in self.state["results"].values())
        
        # Sort users by score
        sorted_users = sorted(
            [{"user_id": k, "score": v["score"]} for k, v in self.state["results"].items()], 
            key=lambda x: x["score"], 
            reverse=True
        )
        
        return {
            "accuracy": (total_actual_score / total_possible_score) * 100 if total_possible_score > 0 else 0,
            "participant_count": total_users,
            "missing_numbers": self.state["missing_numbers"],
            "top_users": sorted_users[:5] # Top 5
        }
    
    async def get_results(self, event_id: int) -> dict:
        """获取结果统计"""
        return self.calculate_stats()

plugin_instance = FindNumbersPlugin()
