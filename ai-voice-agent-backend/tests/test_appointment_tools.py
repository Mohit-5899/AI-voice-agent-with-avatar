import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from tests.conftest import MockSupabaseClient, MockSupabaseQuery, MockSupabaseResponse
from tools import appointment_tools


# --- Helper to create a mock client with specific chained responses ---

class SequentialMockClient:
    """Mock client that returns different responses for sequential table() calls."""

    def __init__(self, responses: list[list]):
        self._responses = responses
        self._call_index = 0

    def table(self, name: str):
        if self._call_index < len(self._responses):
            data = self._responses[self._call_index]
            self._call_index += 1
            return MockSupabaseQuery(data)
        return MockSupabaseQuery([])


# ============================================================
# identify_user_by_phone
# ============================================================

class TestIdentifyUser:

    @pytest.mark.asyncio
    async def test_found_user(self, mock_supabase):
        """Should return found=True with name when user exists."""
        mock_supabase.set_response([
            {"patient_name": "John Doe", "phone_number": "+1234567890"}
        ])
        result = await appointment_tools.identify_user_by_phone("+1234567890")
        assert result["found"] is True
        assert result["name"] == "John Doe"
        assert result["phone"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_supabase):
        """Should return found=False when no matching phone number."""
        mock_supabase.set_response([])
        result = await appointment_tools.identify_user_by_phone("+9999999999")
        assert result["found"] is False
        assert result["phone"] == "+9999999999"


# ============================================================
# fetch_available_slots
# ============================================================

class TestFetchAvailableSlots:

    @pytest.mark.asyncio
    async def test_returns_slots_excluding_booked(self, mock_supabase):
        """Should filter out already-booked slots."""
        mock_supabase.set_response([
            {"appointment_date": "2026-02-09", "appointment_time": "09:00:00"}
        ])
        with patch("tools.appointment_tools.generate_all_slots") as mock_gen:
            mock_gen.return_value = [
                {"date": "2026-02-09", "time": "09:00", "doctor": "Dr. Smith"},
                {"date": "2026-02-09", "time": "09:30", "doctor": "Dr. Smith"},
                {"date": "2026-02-09", "time": "10:00", "doctor": "Dr. Smith"},
            ]
            result = await appointment_tools.fetch_available_slots()

        # 09:00 should be filtered out (booked)
        times = [s["time"] for s in result]
        assert "09:00" not in times
        assert "09:30" in times
        assert "10:00" in times

    @pytest.mark.asyncio
    async def test_filters_by_preferred_date(self, mock_supabase):
        """Should only return slots for the preferred date."""
        mock_supabase.set_response([])
        with patch("tools.appointment_tools.generate_all_slots") as mock_gen:
            mock_gen.return_value = [
                {"date": "2026-02-09", "time": "09:00", "doctor": "Dr. Smith"},
                {"date": "2026-02-10", "time": "09:00", "doctor": "Dr. Smith"},
            ]
            result = await appointment_tools.fetch_available_slots("2026-02-09")

        assert len(result) == 1
        assert result[0]["date"] == "2026-02-09"

    @pytest.mark.asyncio
    async def test_all_booked_returns_empty(self, mock_supabase):
        """Should return empty list if all slots are booked."""
        mock_supabase.set_response([
            {"appointment_date": "2026-02-09", "appointment_time": "09:00:00"},
        ])
        with patch("tools.appointment_tools.generate_all_slots") as mock_gen:
            mock_gen.return_value = [
                {"date": "2026-02-09", "time": "09:00", "doctor": "Dr. Smith"},
            ]
            result = await appointment_tools.fetch_available_slots()

        assert result == []

    @pytest.mark.asyncio
    async def test_no_booked_returns_all(self, mock_supabase):
        """Should return all slots when nothing is booked."""
        mock_supabase.set_response([])
        with patch("tools.appointment_tools.generate_all_slots") as mock_gen:
            mock_gen.return_value = [
                {"date": "2026-02-09", "time": "09:00", "doctor": "Dr. Smith"},
                {"date": "2026-02-09", "time": "09:30", "doctor": "Dr. Smith"},
            ]
            result = await appointment_tools.fetch_available_slots()

        assert len(result) == 2


# ============================================================
# book_appointment
# ============================================================

class TestBookAppointment:

    @pytest.mark.asyncio
    async def test_successful_booking(self):
        """Should insert and return success when slot is free."""
        client = SequentialMockClient([
            [],  # First call: check existing (empty = slot is free)
            [{"id": "abc-123", "phone_number": "+1234567890", "patient_name": "John",
              "appointment_date": "2026-02-10", "appointment_time": "09:00",
              "reason": "Checkup", "status": "scheduled"}],  # Second call: insert
        ])
        with patch("tools.appointment_tools.get_supabase", return_value=client):
            result = await appointment_tools.book_appointment(
                "+1234567890", "John", "2026-02-10", "09:00", "Checkup"
            )
        assert result["success"] is True
        assert result["appointment"]["patient_name"] == "John"

    @pytest.mark.asyncio
    async def test_double_booking_rejected(self):
        """Should reject booking when slot is already taken."""
        client = SequentialMockClient([
            [{"id": "existing-123"}],  # First call: slot already booked
        ])
        with patch("tools.appointment_tools.get_supabase", return_value=client):
            result = await appointment_tools.book_appointment(
                "+1234567890", "John", "2026-02-10", "09:00"
            )
        assert result["success"] is False
        assert "already booked" in result["error"]

    @pytest.mark.asyncio
    async def test_default_reason(self):
        """Should use 'General checkup' when no reason provided."""
        client = SequentialMockClient([
            [],  # slot is free
            [{"id": "abc", "reason": "General checkup", "phone_number": "+1234567890",
              "patient_name": "Jane", "appointment_date": "2026-02-10",
              "appointment_time": "10:00", "status": "scheduled"}],
        ])
        with patch("tools.appointment_tools.get_supabase", return_value=client):
            result = await appointment_tools.book_appointment(
                "+1234567890", "Jane", "2026-02-10", "10:00", None
            )
        assert result["success"] is True


# ============================================================
# retrieve_appointments
# ============================================================

class TestRetrieveAppointments:

    @pytest.mark.asyncio
    async def test_returns_scheduled_appointments(self, mock_supabase):
        """Should return list of scheduled appointments."""
        mock_supabase.set_response([
            {"id": "1", "appointment_date": "2026-02-10", "appointment_time": "09:00",
             "status": "scheduled", "patient_name": "John"},
            {"id": "2", "appointment_date": "2026-02-11", "appointment_time": "10:00",
             "status": "scheduled", "patient_name": "John"},
        ])
        result = await appointment_tools.retrieve_appointments("+1234567890")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_no_appointments_returns_empty(self, mock_supabase):
        """Should return empty list when user has no appointments."""
        mock_supabase.set_response([])
        result = await appointment_tools.retrieve_appointments("+9999999999")
        assert result == []


# ============================================================
# cancel_appointment
# ============================================================

class TestCancelAppointment:

    @pytest.mark.asyncio
    async def test_successful_cancellation(self, mock_supabase):
        """Should return success when appointment found and cancelled."""
        mock_supabase.set_response([
            {"id": "abc-123", "status": "cancelled"}
        ])
        result = await appointment_tools.cancel_appointment("abc-123")
        assert result["success"] is True
        assert result["cancelled"]["id"] == "abc-123"

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, mock_supabase):
        """Should return error when appointment not found."""
        mock_supabase.set_response([])
        result = await appointment_tools.cancel_appointment("nonexistent-id")
        assert result["success"] is False
        assert "not found" in result["error"]


# ============================================================
# modify_appointment
# ============================================================

class TestModifyAppointment:

    @pytest.mark.asyncio
    async def test_successful_modification(self):
        """Should update and return success when new slot is available."""
        client = SequentialMockClient([
            # 1st: get current appointment
            [{"appointment_date": "2026-02-10", "appointment_time": "09:00:00"}],
            # 2nd: check if new slot is available (empty = free)
            [],
            # 3rd: perform update
            [{"id": "abc-123", "appointment_date": "2026-02-11",
              "appointment_time": "10:00", "status": "scheduled"}],
        ])
        with patch("tools.appointment_tools.get_supabase", return_value=client):
            result = await appointment_tools.modify_appointment(
                "abc-123", new_date="2026-02-11", new_time="10:00"
            )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_modify_to_booked_slot_rejected(self):
        """Should reject modification when new slot is already booked."""
        client = SequentialMockClient([
            # 1st: get current appointment
            [{"appointment_date": "2026-02-10", "appointment_time": "09:00:00"}],
            # 2nd: check new slot (occupied)
            [{"id": "other-appointment"}],
        ])
        with patch("tools.appointment_tools.get_supabase", return_value=client):
            result = await appointment_tools.modify_appointment(
                "abc-123", new_date="2026-02-11", new_time="10:00"
            )
        assert result["success"] is False
        assert "already booked" in result["error"]

    @pytest.mark.asyncio
    async def test_no_changes_specified(self, mock_supabase):
        """Should return error when neither date nor time provided."""
        result = await appointment_tools.modify_appointment("abc-123")
        assert result["success"] is False
        assert "No changes" in result["error"]

    @pytest.mark.asyncio
    async def test_modify_nonexistent_appointment(self):
        """Should return error when appointment doesn't exist."""
        client = SequentialMockClient([
            [],  # 1st: appointment not found
        ])
        with patch("tools.appointment_tools.get_supabase", return_value=client):
            result = await appointment_tools.modify_appointment(
                "nonexistent", new_date="2026-02-11"
            )
        assert result["success"] is False
        assert "not found" in result["error"]
