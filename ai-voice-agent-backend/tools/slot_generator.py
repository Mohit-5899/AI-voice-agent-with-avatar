from datetime import date, timedelta
from config import SLOT_CONFIG


def generate_all_slots(from_date: date, days_ahead: int | None = None) -> list[dict]:
    """Generate all possible appointment slots for the next N business days.

    Returns a list of dicts: [{"date": "2026-02-10", "time": "09:00", "doctor": "Dr. Smith"}, ...]
    """
    days_ahead = days_ahead or SLOT_CONFIG["days_ahead"]
    start_hour = SLOT_CONFIG["start_hour"]
    end_hour = SLOT_CONFIG["end_hour"]
    slot_duration = SLOT_CONFIG["slot_duration"]
    doctor = SLOT_CONFIG["doctor_name"]

    slots = []
    current = from_date
    days_added = 0

    while days_added < days_ahead:
        # Skip weekends (Saturday=5, Sunday=6)
        if current.weekday() < 5:
            hour = start_hour
            minute = 0
            while hour < end_hour:
                # Don't add a slot that would extend past end_hour
                slot_end_minutes = hour * 60 + minute + slot_duration
                if slot_end_minutes <= end_hour * 60:
                    slots.append({
                        "date": current.isoformat(),
                        "time": f"{hour:02d}:{minute:02d}",
                        "doctor": doctor,
                    })
                minute += slot_duration
                if minute >= 60:
                    hour += minute // 60
                    minute = minute % 60
            days_added += 1
        current += timedelta(days=1)

    return slots
