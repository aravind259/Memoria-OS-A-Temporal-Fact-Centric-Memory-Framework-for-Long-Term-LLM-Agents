import math
from datetime import datetime
from app.core import clock


class EbbinghausDecayEngine:
    """
    Computes retentive memory strength based on an adapted Ebbinghaus Forgetting Curve formula:
    
        R(t) = exp(- delta_t / (S * (1 + ln(1 + access_count))))
        
    Where:
      - delta_t: Time elapsed since creation/last access (in hours)
      - S: Memory stability score derived from importance (0.1 to 1.0)
      - access_count: Number of times this memory was retrieved and accessed
    """

    def calculate_retention(
        self,
        created_at_iso: str,
        importance: float = 0.5,
        access_count: int = 0,
        current_time: datetime = None
    ) -> float:
        if not current_time:
            current_time = clock.get_now()

        try:
            # Handle trailing Z if present for ISO format compatibility
            clean_iso = created_at_iso.rstrip("Z")
            created_at = datetime.fromisoformat(clean_iso)
            delta_hours = max(0.0, (current_time - created_at).total_seconds() / 3600.0)
        except Exception:
            delta_hours = 0.0

        # Base stability factor (hours): importance 0.1..1.0 maps to 24..240 hours horizon
        stability = max(0.1, importance) * 48.0  # Scale importance to stability horizon (in hours)
        
        # Reinforcement factor from access count (logarithmic boost)
        reinforcement = 1.0 + math.log(1.0 + max(0, access_count))

        effective_half_life = stability * reinforcement

        # Exponential retention formula
        retention = math.exp(-delta_hours / effective_half_life)
        return round(retention, 4)

