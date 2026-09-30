from datetime import datetime, timezone

from .adapter import adapt_event
from .events import DetectionEvent


def test_adapt_area2_sim_swap_event():
    timestamp = datetime.now(timezone.utc).isoformat()

    area2_event = {
        "event_type": "SIM_REREGISTRATION",
        "user_id": "USER-001",
        "phone_number": "+251900000001",
        "old_state": "victim_controlled",
        "new_state": "attacker_controlled",
        "scenario": "suspicious",
        "timestamp": timestamp,
    }

    event = adapt_event(area2_event)

    assert isinstance(event, DetectionEvent)
    assert event.event_type == "SIM_REREGISTRATION"
    assert event.user_id == "USER-001"
    assert event.source == "sim_swap"
    assert event.outcome == "success"
    assert event.phone_number == "+251900000001"
    assert event.details["scenario"] == "suspicious"
    assert event.details["old_state"] == "victim_controlled"
    assert event.details["new_state"] == "attacker_controlled"


def test_adapt_area3_pin_reset_event():
    timestamp = datetime.now(timezone.utc).isoformat()

    area3_event = {
        "event_id": "EVENT-001",
        "event_type": "pin.reset",
        "timestamp": timestamp,
        "user_id": "USER-001",
        "account_id": "ACC-001",
        "phone_number": "+251900000001",
        "session_id": "SESSION-001",
        "outcome": "success",
        "details": {
            "method": "fictional_demo_approval",
            "requires_reauthentication": True,
        },
    }

    event = adapt_event(area3_event)

    assert isinstance(event, DetectionEvent)
    assert event.event_type == "pin.reset"
    assert event.user_id == "USER-001"
    assert event.source == "mobile_money"
    assert event.outcome == "success"
    assert event.account_id == "ACC-001"
    assert event.phone_number == "+251900000001"
    assert event.session_id == "SESSION-001"
    assert event.details["method"] == "fictional_demo_approval"


def test_adapt_area3_transfer_event():
    timestamp = datetime.now(timezone.utc).isoformat()

    area3_event = {
        "event_id": "EVENT-002",
        "event_type": "transaction.transfer",
        "timestamp": timestamp,
        "user_id": "USER-001",
        "account_id": "ACC-001",
        "phone_number": "+251900000001",
        "session_id": "SESSION-001",
        "outcome": "success",
        "details": {
            "amount": "500",
            "currency": "SIM-ETB",
            "recipient_id": "ACC-RECIPIENT-DEMO",
            "virtual_only": True,
        },
    }

    event = adapt_event(area3_event)

    assert event.event_type == "transaction.transfer"
    assert event.user_id == "USER-001"
    assert event.outcome == "success"
    assert event.details["amount"] == "500"
    assert event.details["virtual_only"] is True


def test_unsupported_event_is_rejected():
    unknown_event = {
        "event_type": "unknown.event",
        "user_id": "USER-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        adapt_event(unknown_event)
    except ValueError as error:
        assert "Unsupported event type" in str(error)
    else:
        raise AssertionError("Expected ValueError for unsupported event")