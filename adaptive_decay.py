import math
from datetime import datetime
from typing import Dict, Any, Optional
from app.core import clock

class AdaptiveDecayEngine:
    """
    Adaptive Ebbinghaus Decay & Memory Strategy Engine:
    Dynamically adjusts memory stability parameters based on access patterns, user feedback signals,
    category importance, and context drift rates.
    """

    def __init__(self, base_decay_half_life: float = 48.0):
        self.base_decay_half_life = base_decay_half_life

    def calculate_adaptive_stability(
        self,
        importance: float,
        access_count: int,
        user_feedback_score: float = 1.0,
        category: str = "Fact"
    ) -> float:
        """
        Calculates dynamic stability S considering category persistence and user reinforcement.
        Preferences, Goals, and Skills decay slower than generic Facts or Ephemeral notes.
        """
        category_weights = {
            "Preference": 2.5,
            "Skill": 2.2,
            "Health": 2.2,
            "Goal": 1.8,
            "Project": 1.5,
            "Fact": 1.0,
            "Conversation": 0.5
        }
        cat_weight = category_weights.get(category, 1.0)
        
        # Feedback multiplier (0.5 for explicit correction/negative, 2.0 for explicit user validation)
        feedback_mult = max(0.2, min(3.0, user_feedback_score))
        
        # Base stability horizon in hours
        base_stability = max(0.1, importance) * self.base_decay_half_life * cat_weight * feedback_mult
        
        # Logarithmic access count reinforcement
        reinforcement = 1.0 + math.log(1.0 + max(0, access_count))
        
        return round(base_stability * reinforcement, 2)

    def calculate_retention(
        self,
        created_at_iso: str,
        importance: float = 0.5,
        access_count: int = 0,
        user_feedback_score: float = 1.0,
        category: str = "Fact",
        current_time: Optional[datetime] = None
    ) -> float:
        """
        Returns retention probability R(t) in [0.0, 1.0].
        """
        if not current_time:
            current_time = clock.get_now()

        try:
            clean_iso = created_at_iso.rstrip("Z")
            created_at = datetime.fromisoformat(clean_iso)
            delta_hours = max(0.0, (current_time - created_at).total_seconds() / 3600.0)
        except Exception:
            delta_hours = 0.0

        stability = self.calculate_adaptive_stability(
            importance=importance,
            access_count=access_count,
            user_feedback_score=user_feedback_score,
            category=category
        )

        retention = math.exp(-delta_hours / max(0.1, stability))
        return round(retention, 4)

    def should_page_out_to_cold_archive(
        self,
        retention_score: float,
        status: str,
        importance: float
    ) -> bool:
        """
        Determines if memory should be swapped out from active vector RAM to cold archive storage.
        - Superseded memories are paged out immediately.
        - Memories with retention < 0.15 and low importance (< 0.6) are paged out.
        """
        if status.lower() == "superseded":
            return True
        if retention_score < 0.15 and importance < 0.6:
            return True
        return False
