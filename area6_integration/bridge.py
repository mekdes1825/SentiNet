"""Normalize events from SentiNet work areas for the Area 4 detector.

This module is an integration boundary only. It does not contact telecom or
financial systems and does not treat an event's actor label as proof of identity.
"""
from __future__ import annotations

from typing import Any

from area4_detection.adapter import adapt_event
from area4_detection.events import DetectionEvent


PHISHING_EVENT_TYPES = {
    "phishing_viewed",
    "phishing_clicked",
    "form_submitted",
}


def _value(event: Any, name: str, default: Any = "") -> Any:
    if isinstance(event, dict):
        return event.get(name, default)
    return getattr(event, name, default)


def normalize_event(event: Any) -> DetectionEvent:
    """Convert supported Area 1/2/3 event shapes to the Area 4 event contract.

    Supported inputs:
    - Area 2's legacy ``SIM_REREGISTRATION`` event.
    - Root ``sim_swap`` package's ``sim.reregistration`` event.
    - Area 3 mobile-money event dictionaries/objects supported by Area 4.
    - Area 1's basic phishing timeline events.

    Raises ValueError for unknown event types or missing required fields.
    """
    event_type = _value(event, "event_type")

    # The newer root sim_swap package uses a different event name/field schema
    # than Area 4's original adapter expects. Translate it at this boundary.
    if event_type == "sim.reregistration":
        details = _value(event, "details", {})
        if not isinstance(details, dict):
            details = {}
        normalized = {
            "event_type": "SIM_REREGISTRATION",
            "user_id": _value(event, "user_id"),
            "phone_number": _value(event, "phone_number"),
            "old_state": _value(event, "previous_state"),
            "new_state": _value(event, "new_state"),
            "scenario": details.get("scenario", ""),
            "timestamp": _value(event, "timestamp"),
        }
        return adapt_event(normalized)

    # Area 1 events are currently session-oriented and are not wired into
    # Area 4's takeover rules. Preserve them in the common event shape without
    # pretending a session ID is a verified user/account identity.
    if event_type in PHISHING_EVENT_TYPES:
        timestamp = _value(event, "timestamp")
        session_id = _value(event, "session_id")
        if not timestamp:
            raise ValueError("Phishing event is missing timestamp")
        if not session_id:
            raise ValueError("Phishing event is missing session_id")
        return DetectionEvent(
            event_type=event_type,
            user_id=str(_value(event, "user_id") or ""),
            timestamp=str(timestamp),
            source="phishing",
            outcome="",
            details={"source_event_id": _value(event, "id", "")},
            session_id=str(session_id),
        )

    # Existing Area 4 adapter already supports Area 2's legacy format and
    # Area 3's mobile-money event types.
    return adapt_event(event)
