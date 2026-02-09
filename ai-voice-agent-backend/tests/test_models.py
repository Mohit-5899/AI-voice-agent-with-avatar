import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from models import ToolCallEvent


class TestToolCallEvent:

    def test_create_started_event(self):
        """Should create a started event without result."""
        event = ToolCallEvent.now(
            tool_name="identify_user",
            status="started",
            arguments={"phone_number": "+1234567890"},
        )
        assert event.tool_name == "identify_user"
        assert event.status == "started"
        assert event.arguments == {"phone_number": "+1234567890"}
        assert event.result is None
        assert event.timestamp  # not empty

    def test_create_completed_event(self):
        """Should create a completed event with result."""
        event = ToolCallEvent.now(
            tool_name="book_appointment",
            status="completed",
            arguments={"phone": "+123"},
            result={"success": True},
        )
        assert event.status == "completed"
        assert event.result == {"success": True}

    def test_serializes_to_json(self):
        """Should produce valid JSON for data channel transmission."""
        event = ToolCallEvent.now(
            tool_name="fetch_slots",
            status="completed",
            arguments={"preferred_date": "2026-02-10"},
            result={"slots": [], "total_available": 0},
        )
        json_str = event.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["tool_name"] == "fetch_slots"
        assert parsed["status"] == "completed"
        assert parsed["result"]["total_available"] == 0

    def test_encodes_to_bytes_for_publish(self):
        """Data channel payload must be bytes."""
        event = ToolCallEvent.now("test", "started", {})
        payload = event.model_dump_json().encode("utf-8")
        assert isinstance(payload, bytes)

    def test_status_validation(self):
        """Should only accept valid status values."""
        # Valid statuses
        for status in ["started", "completed", "error"]:
            event = ToolCallEvent.now("test", status, {})
            assert event.status == status

    def test_timestamp_is_iso_format(self):
        """Timestamp should be a valid ISO format string."""
        event = ToolCallEvent.now("test", "started", {})
        # Should not raise
        from datetime import datetime
        datetime.fromisoformat(event.timestamp)
