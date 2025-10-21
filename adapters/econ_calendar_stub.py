# Minimal stub — replace with a real calendar (e.g., FRED releases, Econoday/Investing license, or your own curated CSV)
from __future__ import annotations
from datetime import datetime




def get_today_calendar(timezone_str: str = "America/New_York"):
    # Replace with real pulls later. This keeps the pipeline working today.
    today = datetime.now().strftime("%Y-%m-%d")
    return [
    {"time_et": "08:30", "name": "Initial Jobless Claims", "consensus": "n/a", "source": "BLS"},
    {"time_et": "10:00", "name": "Existing Home Sales", "consensus": "n/a", "source": "NAR"},
    ]