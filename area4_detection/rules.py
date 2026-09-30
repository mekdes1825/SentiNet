from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class DetectionAlert:
    """
    Represents a suspicious behavioral pattern detected by Area 4.
    """

    rule_id: str
    rule_name: str
    risk_level: str
    score: int
    user_id: str
    reason: str
    matched_events: list[str]
    timestamp: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert the alert into a dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "risk_level": self.risk_level,
            "score": self.score,
            "user_id": self.user_id,
            "reason": self.reason,
            "matched_events": list(self.matched_events),
            "timestamp": self.timestamp,
            "details": dict(self.details),
        }


def _parse_timestamp(timestamp: str) -> datetime:
    """Convert an ISO timestamp into a timezone-aware datetime."""
    value = timestamp.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _event_type(event: Any) -> str:
    """Get the event type from a DetectionEvent or dictionary."""
    if isinstance(event, dict):
        return event.get("event_type", "")

    return getattr(event, "event_type", "")


def _user_id(event: Any) -> str:
    """Get the user ID from a DetectionEvent or dictionary."""
    if isinstance(event, dict):
        return event.get("user_id", "")

    return getattr(event, "user_id", "")


def _timestamp(event: Any) -> str:
    """Get the timestamp from a DetectionEvent or dictionary."""
    if isinstance(event, dict):
        return event.get("timestamp", "")

    return getattr(event, "timestamp", "")


def _details(event: Any) -> dict[str, Any]:
    """Get event details from a DetectionEvent or dictionary."""
    if isinstance(event, dict):
        return event.get("details", {})

    return getattr(event, "details", {})


def _make_alert(
    rule_id: str,
    rule_name: str,
    risk_level: str,
    score: int,
    user_id: str,
    reason: str,
    matched_events: list[str],
    details: dict[str, Any] | None = None,
) -> DetectionAlert:
    """Create a standardized detection alert."""
    return DetectionAlert(
        rule_id=rule_id,
        rule_name=rule_name,
        risk_level=risk_level,
        score=score,
        user_id=user_id,
        reason=reason,
        matched_events=matched_events,
        timestamp=datetime.now(timezone.utc).isoformat(),
        details=details or {},
    )


def detect_sim_swap_followed_by_pin_reset(
    events: list[Any],
    window_seconds: int = 300,
) -> list[DetectionAlert]:
    """
    Detect a PIN reset occurring shortly after SIM re-registration.

    Area 2 produces:
        SIM_REREGISTRATION

    Area 3 produces:
        pin.reset

    Both events must belong to the same user and occur within
    the configured time window.
    """
    alerts = []

    sim_events = [
        event for event in events
        if _event_type(event) == "SIM_REREGISTRATION"
    ]

    reset_events = [
        event for event in events
        if _event_type(event) == "pin.reset"
    ]

    for sim_event in sim_events:
        sim_time = _parse_timestamp(_timestamp(sim_event))
        user_id = _user_id(sim_event)

        for reset_event in reset_events:
            if _user_id(reset_event) != user_id:
                continue

            reset_time = _parse_timestamp(_timestamp(reset_event))
            elapsed = (reset_time - sim_time).total_seconds()

            if 0 <= elapsed <= window_seconds:
                alerts.append(
                    _make_alert(
                        rule_id="ATO-001",
                        rule_name="SIM Re-registration followed by PIN reset",
                        risk_level="HIGH",
                        score=75,
                        user_id=user_id,
                        reason=(
                            "A PIN reset occurred shortly after "
                            "SIM re-registration."
                        ),
                        matched_events=[
                            "SIM_REREGISTRATION",
                            "pin.reset",
                        ],
                        details={
                            "window_seconds": window_seconds,
                            "elapsed_seconds": elapsed,
                            "sim_scenario": _details(sim_event).get(
                                "scenario"
                            ),
                        },
                    )
                )

    return alerts


def detect_sim_swap_followed_by_transfer(
    events: list[Any],
    window_seconds: int = 300,
) -> list[DetectionAlert]:
    """
    Detect a virtual transfer occurring shortly after SIM re-registration.
    """
    alerts = []

    sim_events = [
        event for event in events
        if _event_type(event) == "SIM_REREGISTRATION"
    ]

    transfer_events = [
        event for event in events
        if _event_type(event) == "transaction.transfer"
        and (
            event.get("outcome") == "success"
            if isinstance(event, dict)
            else getattr(event, "outcome", "") == "success"
        )
    ]

    for sim_event in sim_events:
        sim_time = _parse_timestamp(_timestamp(sim_event))
        user_id = _user_id(sim_event)

        for transfer_event in transfer_events:
            if _user_id(transfer_event) != user_id:
                continue

            transfer_time = _parse_timestamp(_timestamp(transfer_event))
            elapsed = (transfer_time - sim_time).total_seconds()

            if 0 <= elapsed <= window_seconds:
                alerts.append(
                    _make_alert(
                        rule_id="ATO-002",
                        rule_name="SIM Re-registration followed by transfer",
                        risk_level="HIGH",
                        score=80,
                        user_id=user_id,
                        reason=(
                            "A virtual money transfer occurred shortly "
                            "after SIM re-registration."
                        ),
                        matched_events=[
                            "SIM_REREGISTRATION",
                            "transaction.transfer",
                        ],
                        details={
                            "window_seconds": window_seconds,
                            "elapsed_seconds": elapsed,
                            "transfer": _details(transfer_event),
                        },
                    )
                )

    return alerts


def detect_full_account_takeover_pattern(
    events: list[Any],
    window_seconds: int = 300,
) -> list[DetectionAlert]:
    """
    Detect the strongest simulated account-takeover sequence:

        SIM_REREGISTRATION
                +
             pin.reset
                +
          transaction.transfer

    All three events must belong to the same user and occur in
    chronological order within the configured time window.
    """
    alerts = []

    for sim_event in events:
        if _event_type(sim_event) != "SIM_REREGISTRATION":
            continue

        user_id = _user_id(sim_event)
        sim_time = _parse_timestamp(_timestamp(sim_event))

        user_events = [
            event for event in events
            if _user_id(event) == user_id
        ]

        reset_events = [
            event for event in user_events
            if _event_type(event) == "pin.reset"
        ]

        transfer_events = [
            event for event in user_events
            if _event_type(event) == "transaction.transfer"
            and (
                event.get("outcome") == "success"
                if isinstance(event, dict)
                else getattr(event, "outcome", "") == "success"
            )
        ]

        for reset_event in reset_events:
            reset_time = _parse_timestamp(_timestamp(reset_event))

            if not 0 <= (reset_time - sim_time).total_seconds() <= window_seconds:
                continue

            for transfer_event in transfer_events:
                transfer_time = _parse_timestamp(_timestamp(transfer_event))

                if not reset_time <= transfer_time:
                    continue

                if (transfer_time - sim_time).total_seconds() > window_seconds:
                    continue

                alerts.append(
                    _make_alert(
                        rule_id="ATO-003",
                        rule_name="Full simulated account-takeover pattern",
                        risk_level="CRITICAL",
                        score=100,
                        user_id=user_id,
                        reason=(
                            "SIM re-registration was followed by a PIN reset "
                            "and a successful virtual transfer within the "
                            "configured time window."
                        ),
                        matched_events=[
                            "SIM_REREGISTRATION",
                            "pin.reset",
                            "transaction.transfer",
                        ],
                        details={
                            "window_seconds": window_seconds,
                            "elapsed_seconds": (
                                transfer_time - sim_time
                            ).total_seconds(),
                        },
                    )
                )

    return alerts