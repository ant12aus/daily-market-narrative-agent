from __future__ import annotations
from datetime import datetime

def get_today_calendar(timezone_str: str = "America/New_York"):
    return [
        {"time_et": "08:30", "name": "Initial Jobless Claims", "consensus": "n/a", "source": "BLS"},
        {"time_et": "10:00", "name": "Existing Home Sales", "consensus": "n/a", "source": "NAR"},
    ]
