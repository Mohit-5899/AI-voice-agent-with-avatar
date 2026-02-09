import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from agent_definition import AppointmentAgent


class TestAppointmentAgentTools:
    """Test that each tool calls the right function, publishes events, and returns JSON."""

    @pytest.fixture
    def agent(self):
        return AppointmentAgent()

    @pytest.fixture
    def mock_ctx(self):
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.room = MagicMock()
        ctx.session.room.local_participant = MagicMock()
        ctx.session.room.local_participant.publish_data = AsyncMock()
        return ctx

    # ---- identify_user ----

    @pytest.mark.asyncio
    async def test_identify_user_calls_tool_and_publishes(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.identify_user_by_phone", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"found": True, "name": "John", "phone": "+123"}

            result = await agent.identify_user(mock_ctx, phone_number="+123")

        # Verify tool function was called
        mock_fn.assert_called_once_with("+123")
        # Verify result is JSON
        parsed = json.loads(result)
        assert parsed["found"] is True
        assert parsed["name"] == "John"
        # Verify data channel events published (started + completed)
        assert mock_ctx.session.room.local_participant.publish_data.call_count == 2

    # ---- fetch_slots ----

    @pytest.mark.asyncio
    async def test_fetch_slots_returns_summary(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.fetch_available_slots", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = [
                {"date": "2026-02-10", "time": "09:00", "doctor": "Dr. Smith"},
                {"date": "2026-02-10", "time": "09:30", "doctor": "Dr. Smith"},
            ]

            result = await agent.fetch_slots(mock_ctx, preferred_date="2026-02-10")

        parsed = json.loads(result)
        assert parsed["total_available"] == 2
        assert len(parsed["slots"]) == 2

    @pytest.mark.asyncio
    async def test_fetch_slots_limits_to_10(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.fetch_available_slots", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = [{"date": "2026-02-10", "time": f"{9+i//2:02d}:{(i%2)*30:02d}", "doctor": "Dr. Smith"} for i in range(16)]

            result = await agent.fetch_slots(mock_ctx)

        parsed = json.loads(result)
        assert len(parsed["slots"]) == 10  # Capped at 10
        assert parsed["total_available"] == 16  # Total is accurate

    # ---- book_appointment ----

    @pytest.mark.asyncio
    async def test_book_appointment_success(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.book_appointment", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"success": True, "appointment": {"id": "abc"}}

            result = await agent.book_appointment(
                mock_ctx,
                phone_number="+123",
                patient_name="John",
                appointment_date="2026-02-10",
                appointment_time="09:00",
                reason="Checkup",
            )

        mock_fn.assert_called_once_with("+123", "John", "2026-02-10", "09:00", "Checkup")
        parsed = json.loads(result)
        assert parsed["success"] is True

    @pytest.mark.asyncio
    async def test_book_appointment_empty_reason_becomes_none(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.book_appointment", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"success": True, "appointment": {"id": "abc"}}

            await agent.book_appointment(
                mock_ctx,
                phone_number="+123",
                patient_name="John",
                appointment_date="2026-02-10",
                appointment_time="09:00",
                reason="",
            )

        # Empty reason should be passed as None
        mock_fn.assert_called_once_with("+123", "John", "2026-02-10", "09:00", None)

    # ---- retrieve_appointments ----

    @pytest.mark.asyncio
    async def test_retrieve_appointments(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.retrieve_appointments", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = [
                {"id": "1", "appointment_date": "2026-02-10"},
                {"id": "2", "appointment_date": "2026-02-11"},
            ]

            result = await agent.retrieve_appointments(mock_ctx, phone_number="+123")

        parsed = json.loads(result)
        assert parsed["count"] == 2
        assert len(parsed["appointments"]) == 2

    # ---- cancel_appointment ----

    @pytest.mark.asyncio
    async def test_cancel_appointment_success(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.cancel_appointment", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"success": True, "cancelled": {"id": "abc"}}

            result = await agent.cancel_appointment(mock_ctx, appointment_id="abc")

        parsed = json.loads(result)
        assert parsed["success"] is True

    @pytest.mark.asyncio
    async def test_cancel_appointment_not_found(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.cancel_appointment", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"success": False, "error": "Appointment not found or already cancelled"}

            result = await agent.cancel_appointment(mock_ctx, appointment_id="nonexistent")

        parsed = json.loads(result)
        assert parsed["success"] is False

    # ---- modify_appointment ----

    @pytest.mark.asyncio
    async def test_modify_appointment_success(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.modify_appointment", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"success": True, "updated": {"id": "abc"}}

            result = await agent.modify_appointment(
                mock_ctx, appointment_id="abc", new_date="2026-02-12", new_time="14:00"
            )

        mock_fn.assert_called_once_with("abc", "2026-02-12", "14:00")
        parsed = json.loads(result)
        assert parsed["success"] is True

    @pytest.mark.asyncio
    async def test_modify_appointment_empty_strings_become_none(self, agent, mock_ctx):
        with patch("agent_definition.appointment_tools.modify_appointment", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"success": True, "updated": {"id": "abc"}}

            await agent.modify_appointment(mock_ctx, appointment_id="abc", new_date="", new_time="14:00")

        mock_fn.assert_called_once_with("abc", None, "14:00")

    # ---- end_conversation ----

    @pytest.mark.asyncio
    async def test_end_conversation_publishes_summary(self, agent, mock_ctx):
        result = await agent.end_conversation(mock_ctx, summary="Booked appointment for Feb 10")

        parsed = json.loads(result)
        assert parsed["summary"] == "Booked appointment for Feb 10"
        assert parsed["message"] == "Conversation ended"
        # Should publish: tool_call started, call_summary, tool_call completed = 3 publish_data calls
        assert mock_ctx.session.room.local_participant.publish_data.call_count == 3


class TestPublishToolEvent:
    """Test the _publish_tool_event helper."""

    @pytest.mark.asyncio
    async def test_publishes_json_bytes(self):
        agent = AppointmentAgent()
        ctx = MagicMock()
        ctx.session.room.local_participant.publish_data = AsyncMock()

        from models import ToolCallEvent
        event = ToolCallEvent.now("test_tool", "started", {"key": "value"})
        await agent._publish_tool_event(ctx, event)

        call_args = ctx.session.room.local_participant.publish_data.call_args
        payload = call_args.kwargs.get("payload") or call_args[1].get("payload") or call_args[0][0]
        assert isinstance(payload, bytes)
        parsed = json.loads(payload.decode("utf-8"))
        assert parsed["tool_name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_handles_missing_room_gracefully(self):
        """Should not crash when room is None."""
        agent = AppointmentAgent()
        ctx = MagicMock()
        ctx.session.room = None

        from models import ToolCallEvent
        event = ToolCallEvent.now("test", "started", {})
        # Should not raise
        await agent._publish_tool_event(ctx, event)

    @pytest.mark.asyncio
    async def test_handles_publish_error_gracefully(self):
        """Should log warning but not crash on publish error."""
        agent = AppointmentAgent()
        ctx = MagicMock()
        ctx.session.room.local_participant.publish_data = AsyncMock(side_effect=Exception("Network error"))

        from models import ToolCallEvent
        event = ToolCallEvent.now("test", "started", {})
        # Should not raise
        await agent._publish_tool_event(ctx, event)
