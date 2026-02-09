import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass

# Add backend root to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@dataclass
class MockSupabaseResponse:
    """Mock Supabase query response."""
    data: list


class MockSupabaseQuery:
    """Chainable mock for Supabase query builder."""

    def __init__(self, response_data: list | None = None):
        self._response_data = response_data or []

    def select(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def neq(self, *args, **kwargs):
        return self

    def gte(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def execute(self):
        return MockSupabaseResponse(data=self._response_data)


class MockSupabaseClient:
    """Mock Supabase client with configurable table responses."""

    def __init__(self):
        self._table_responses: dict[str, list] = {}

    def set_response(self, data: list):
        """Set the response data for the next table query."""
        self._next_response = data

    def table(self, name: str):
        return MockSupabaseQuery(getattr(self, "_next_response", []))


@pytest.fixture
def mock_supabase():
    """Provides a mock Supabase client and patches get_supabase."""
    client = MockSupabaseClient()
    with patch("tools.appointment_tools.get_supabase", return_value=client):
        yield client


@pytest.fixture
def mock_room():
    """Provides a mock LiveKit room with local_participant.publish_data."""
    room = MagicMock()
    room.local_participant = MagicMock()
    room.local_participant.publish_data = AsyncMock()
    return room


@pytest.fixture
def mock_context(mock_room):
    """Provides a mock RunContext with session.room."""
    context = MagicMock()
    context.session = MagicMock()
    context.session.room = mock_room
    return context
