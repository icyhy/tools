import random
import time
from typing import List, Dict, Any, Optional

class FindNumbersPlugin:
    def __init__(self):
        self.id = "find_numbers"
        self.name = "找数字规律"
        self.state = {
            "stage": 0, # 0: Ready, 1: Stage 1, 2: Stage 2, 3: Stage 3, 4: Finished
            "numbers": [],
            "missing_numbers": [],
            "start_time": 0,
            "end_time": 0,
            "results": {}, # user_id -> {score: int, answers: List[int]}
            "total_numbers": 100, # 0-100 actually 101 numbers usually, but let's say 1-100 or 0-99. Requirement says "0~100".
            "missing_count": 10
        }
    
    def generate_numbers(self):
        # Generate 0-100 numbers
        all_nums = list(range(101))
        # Randomly remove some
        missing = sorted(random.sample(all_nums, self.state["missing_count"]))
        present = [n for n in all_nums if n not in missing]
        
        self.state["missing_numbers"] = missing
        self.state["numbers"] = present
        return present, missing

    def start_stage(self, stage: int):
        self.state["stage"] = stage
        self.state["results"] = {} # Reset results for the new stage? Or keep cumulative? Usually per stage logic.
        # Let's reset for each stage as they are distinct "games" in a way, or just phases.
        # Requirement: "后台统计用户正确率及查找完成率" per stage.
        
        self.generate_numbers()
        self.state["start_time"] = time.time()
        self.state["end_time"] = self.state["start_time"] + 30 # 30s duration
        
        return {
            "type": "game_start",
            "plugin_id": self.id,
            "stage": stage,
            "numbers": self.state["numbers"],
            "duration": 30,
            "missing_count": len(self.state["missing_numbers"])
        }

    def stop_stage(self):
        # Calculate final results
        # In a real plugin system, this might save to DB
        return {
            "type": "game_end",
            "plugin_id": self.id,
            "stage": self.state["stage"],
            "results": self.calculate_stats()
        }

    def handle_submit(self, user_id: str, answers: List[int]):
        # Validate answers
        # answers should be a list of integers
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

    def calculate_stats(self):
        total_users = len(self.state["results"])
        if total_users == 0:
            return {"accuracy": 0, "completion_rate": 0, "top_users": []}
            
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

plugin_instance = FindNumbersPlugin()
