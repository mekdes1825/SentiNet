from typing import Any

from .events import DetectionEvent


def _get_value(event: Any, field: str, default: Any = "") -> Any:
    """Read a field from either an object or a dictionary."""
    if isinstance(event, dict):
        return event.get(field, default)

    return getattr(event, field, default)


def _get_details(event: Any) -> dict[str, Any]:
    """Return event details without exposing sensitive credentials."""
    details = _get_value(event, "details", {})

    if isinstance(details, dict):
        return dict(details)

    return {}


def adapt_sim_swap_event(event: Any) -> DetectionEvent:
    """
    Convert an Area 2 SIM-swap event into a DetectionEvent.

    Supports the official sim_swap/events.py structure:
        event_type
        user_id
        phone_number
        old_state
        new_state
        scenario
        timestamp
    """

    event_type = _get_value(event, "event_type")

    if event_type != "SIM_REREGISTRATION":
        raise ValueError(
            "Expected an Area 2 SIM_REREGISTRATION event"
        )

    user_id = _get_value(event, "user_id")
    timestamp = _get_value(event, "timestamp")

    if not user_id:
        raise ValueError("SIM-swap event is missing user_id")

    if not timestamp:
        raise ValueError("SIM-swap event is missing timestamp")

    details = _get_details(event)

    details.update(
        {
            "scenario": _get_value(event, "scenario"),
            "old_state": _get_value(event, "old_state"),
            "new_state": _get_value(event, "new_state"),
        }
    )

    return DetectionEvent(
        event_type="SIM_REREGISTRATION",
        user_id=user_id,
        timestamp=timestamp,
        source="sim_swap",
        outcome="success",
        details=details,
        phone_number=_get_value(event, "phone_number"),
    )


def adapt_mobile_money_event(event: Any) -> DetectionEvent:
    """
    Convert an Area 3 mobile-money event into a DetectionEvent.

    Area 3 events contain:
        event_type
        timestamp
        user_id
        account_id
        phone_number
        session_id
        outcome
        details
    """

    event_type = _get_value(event, "event_type")

    supported_types = {
        "auth.attempt",
        "auth.success",
        "auth.failure",
        "account.balance_viewed",
        "transaction.transfer",
        "pin.change",
        "pin.reset",
    }

    if event_type not in supported_types:
        raise ValueError(
            f"Unsupported mobile-money event type: {event_type}"
        )

    user_id = _get_value(event, "user_id")
    timestamp = _get_value(event, "timestamp")

    if not user_id:
        raise ValueError("Mobile-money event is missing user_id")

    if not timestamp:
        raise ValueError("Mobile-money event is missing timestamp")

    return DetectionEvent(
        event_type=event_type,
        user_id=user_id,
        timestamp=timestamp,
        source="mobile_money",
        outcome=_get_value(event, "outcome"),
        details=_get_details(event),
        account_id=_get_value(event, "account_id"),
        phone_number=_get_value(event, "phone_number"),
        session_id=_get_value(event, "session_id"),
    )


def adapt_event(event: Any) -> DetectionEvent:
    """
    Automatically adapt an Area 2 or Area 3 event.
    """

    event_type = _get_value(event, "event_type")

    if event_type == "SIM_REREGISTRATION":
        return adapt_sim_swap_event(event)

    if event_type in {
        "auth.attempt",
        "auth.success",
        "auth.failure",
        "account.balance_viewed",
        "transaction.transfer",
        "pin.change",
        "pin.reset",
    }:
        return adapt_mobile_money_event(event)

    raise ValueError(
        f"Unsupported event type: {event_type}"
    )