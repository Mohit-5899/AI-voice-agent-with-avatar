from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, timezone


class ToolCallEvent(BaseModel):
    """Published to frontend via LiveKit data channel for tool call visualization."""
    tool_name: str
    status: Literal["started", "completed", "error"]
    arguments: dict
    result: Optional[dict] = None
    timestamp: str

    @classmethod
    def now(cls, tool_name: str, status: str, arguments: dict, result: dict | None = None):
        return cls(
            tool_name=tool_name,
            status=status,
            arguments=arguments,
            result=result,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
