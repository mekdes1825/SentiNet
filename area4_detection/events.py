from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class DetectionEvent:
    """
    Standard event format used by the Area 4 behavioral detection engine.

    This format preserves the important fields produced by the
    SIM-Swap and Mobile-Money simulation components.
    """

    event_type: str
    user_id: str
    timestamp: str
    source: str
    outcome: str = ""
    details: dict[str, Any] | None = None
    account_id: str = ""
    phone_number: str = ""
    session_id: str = ""

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert the detection event into a dictionary."""
        return {
            "event_type": self.event_type,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "outcome": self.outcome,
            "details": dict(self.details),
            "account_id": self.account_id,
            "phone_number": self.phone_number,
            "session_id": self.session_id,
        }

    @classmethod
    def create(
        cls,
        event_type: str,
        user_id: str,
        source: str,
        outcome: str = "",
        details: dict[str, Any] | None = None,
        timestamp: str | None = None,
        account_id: str = "",
        phone_number: str = "",
        session_id: str = "",
    ) -> "DetectionEvent":
        """
        Create a standardized detection event.

        If no timestamp is supplied, the current UTC time is used.
        """
        return cls(
            event_type=event_type,
            user_id=user_id,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            source=source,
            outcome=outcome,
            details=details or {},
            account_id=account_id,
            phone_number=phone_number,
            session_id=session_id,
        )