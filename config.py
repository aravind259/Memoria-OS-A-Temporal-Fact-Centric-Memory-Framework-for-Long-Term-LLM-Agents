import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Background Memory Lifecycle Scheduler Settings
LIFECYCLE_SCHEDULER_ENABLED = os.getenv("LIFECYCLE_SCHEDULER_ENABLED", "True").lower() in ("true", "1", "yes")
LIFECYCLE_INTERVAL_SECONDS = float(os.getenv("LIFECYCLE_INTERVAL_SECONDS", "60.0"))
LIFECYCLE_DECAY_THRESHOLD = float(os.getenv("LIFECYCLE_DECAY_THRESHOLD", "0.15"))
LIFECYCLE_IMPORTANT_THRESHOLD = float(os.getenv("LIFECYCLE_IMPORTANT_THRESHOLD", "0.65"))

print(f"[CONFIG] Gemini API Key configured: {bool(GEMINI_API_KEY)}")
print(f"[CONFIG] Lifecycle Scheduler Enabled={LIFECYCLE_SCHEDULER_ENABLED}, Interval={LIFECYCLE_INTERVAL_SECONDS}s, DecayThreshold={LIFECYCLE_DECAY_THRESHOLD}")