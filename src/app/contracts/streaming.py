from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


EventType = Literal[
    "input",
    "output",
    "partial",
    "error",
    "complete",
    "heartbeat",
    "cancel",
]


@dataclass(slots=True)
class StreamEvent:
    event_type: EventType
    session_id: str
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
