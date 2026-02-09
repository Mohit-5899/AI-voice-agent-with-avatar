import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from tools.slot_generator import generate_all_slots


class TestSlotGenerator:
    """Tests for the slot generation logic."""

    def test_generates_slots_for_weekdays_only(self):
        """Slots should only be generated for Mon-Fri, never Sat/Sun."""
        # 2026-02-09 is a Monday
        slots = generate_all_slots(date(2026, 2, 9), days_ahead=5)

        dates_in_slots = set(s["date"] for s in slots)
        for d_str in dates_in_slots:
            d = date.fromisoformat(d_str)
            assert d.weekday() < 5, f"{d_str} is a weekend day (weekday={d.weekday()})"

    def test_generates_correct_number_of_days(self):
        """Should generate slots for exactly N business days."""
        slots = generate_all_slots(date(2026, 2, 9), days_ahead=3)
        dates = set(s["date"] for s in slots)
        assert len(dates) == 3

    def test_slot_times_within_business_hours(self):
        """All slots should be between 9:00 and 16:30 (last slot ending at 17:00)."""
        slots = generate_all_slots(date(2026, 2, 9), days_ahead=1)

        for slot in slots:
            hour, minute = map(int, slot["time"].split(":"))
            total_minutes = hour * 60 + minute
            assert total_minutes >= 9 * 60, f"Slot {slot['time']} is before 9:00"
            # Last slot at 16:30, ends at 17:00
            assert total_minutes <= 16 * 60 + 30, f"Slot {slot['time']} is after 16:30"

    def test_slots_are_30_minutes_apart(self):
        """Consecutive slots on the same day should be 30 minutes apart."""
        slots = generate_all_slots(date(2026, 2, 9), days_ahead=1)

        for i in range(1, len(slots)):
            if slots[i]["date"] != slots[i - 1]["date"]:
                continue
            h1, m1 = map(int, slots[i - 1]["time"].split(":"))
            h2, m2 = map(int, slots[i]["time"].split(":"))
            diff = (h2 * 60 + m2) - (h1 * 60 + m1)
            assert diff == 30, f"Gap between {slots[i-1]['time']} and {slots[i]['time']} is {diff}min"

    def test_16_slots_per_day(self):
        """9:00 to 16:30 in 30-min intervals = 16 slots per day."""
        slots = generate_all_slots(date(2026, 2, 9), days_ahead=1)
        assert len(slots) == 16

    def test_doctor_name_in_all_slots(self):
        """Every slot should include the doctor name."""
        slots = generate_all_slots(date(2026, 2, 9), days_ahead=1)
        for slot in slots:
            assert slot["doctor"] == "Dr. Smith"

    def test_skips_weekends(self):
        """Starting from a Friday, next day should be Monday."""
        # 2026-02-13 is a Friday
        slots = generate_all_slots(date(2026, 2, 13), days_ahead=2)
        dates = sorted(set(s["date"] for s in slots))
        assert dates[0] == "2026-02-13"  # Friday
        assert dates[1] == "2026-02-16"  # Monday (skipped Sat/Sun)

    def test_starting_on_saturday(self):
        """If starting on Saturday, first slots should be on Monday."""
        # 2026-02-14 is a Saturday
        slots = generate_all_slots(date(2026, 2, 14), days_ahead=1)
        dates = set(s["date"] for s in slots)
        assert "2026-02-14" not in dates  # Saturday
        assert "2026-02-15" not in dates  # Sunday
        assert "2026-02-16" in dates      # Monday

    def test_default_days_ahead_is_5(self):
        """When days_ahead is not provided, should use config default (5)."""
        slots = generate_all_slots(date(2026, 2, 9))
        dates = set(s["date"] for s in slots)
        assert len(dates) == 5

    def test_slot_format(self):
        """Each slot should have date, time, and doctor keys."""
        slots = generate_all_slots(date(2026, 2, 9), days_ahead=1)
        for slot in slots:
            assert "date" in slot
            assert "time" in slot
            assert "doctor" in slot
            # Date format: YYYY-MM-DD
            assert len(slot["date"]) == 10
            # Time format: HH:MM
            assert len(slot["time"]) == 5
