"""In-memory diagnostics event history for the Victron MK3 integration."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DiagnosticsEventLog:
    """Keep a bounded in-memory history of recent diagnostics events."""

    def __init__(self, maxlen: int = 50) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def record(
        self,
        operation: str,
        error: BaseException | Enum | str | None = None,
        **details: Any,
    ) -> None:
        """Record a diagnostics event."""
        event: dict[str, Any] = {
            "time": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
        }
        if error is not None:
            if isinstance(error, BaseException):
                event["exception"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                }
            elif isinstance(error, Enum):
                event["message"] = error.name.lower()
            else:
                event["message"] = str(error)
        if details:
            event["details"] = details
        self._events.append(event)

    def as_list(self) -> list[dict[str, Any]]:
        """Return recorded events in oldest-to-newest order."""
        return list(self._events)
