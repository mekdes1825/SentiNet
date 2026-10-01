from datetime import datetime, timedelta, timezone

from .events import DetectionEvent
from .rules import (
    detect_full_account_takeover_pattern,
    detect_sim_swap_followed_by_pin_reset,
    detect_sim_swap_followed_by_transfer,
)


def make_event(
    event_type,
    user_id,
    timestamp,
    source,
    outcome="",
    details=None,
):
    return DetectionEvent(
        event_type=event_type,
        user_id=user_id,
        timestamp=timestamp,
        source=source,
        outcome=outcome,
        details=details or {},
    )


def test_sim_swap_followed_by_pin_reset():
    base_time = datetime.now(timezone.utc)

    events = [
        make_event(
            "SIM_REREGISTRATION",
            "USER-001",
            base_time.isoformat(),
            "sim_swap",
            details={"scenario": "suspicious"},
        ),
        make_event(
            "pin.reset",
            "USER-001",
            (base_time + timedelta(seconds=60)).isoformat(),
            "mobile_money",
            outcome="success",
        ),
    ]

    alerts = detect_sim_swap_followed_by_pin_reset(events, window_seconds=300)

    assert len(alerts) == 1
    assert alerts[0].rule_id == "ATO-001"
    assert alerts[0].risk_level == "HIGH"


def test_sim_swap_followed_by_transfer():
    base_time = datetime.now(timezone.utc)

    events = [
        make_event(
            "SIM_REREGISTRATION",
            "USER-001",
            base_time.isoformat(),
            "sim_swap",
            details={"scenario": "suspicious"},
        ),
        make_event(
            "transaction.transfer",
            "USER-001",
            (base_time + timedelta(seconds=120)).isoformat(),
            "mobile_money",
            outcome="success",
            details={
                "amount": "500",
                "currency": "SIM-ETB",
                "virtual_only": True,
            },
        ),
    ]

    alerts = detect_sim_swap_followed_by_transfer(
        events,
        window_seconds=300,
    )

    assert len(alerts) == 1
    assert alerts[0].rule_id == "ATO-002"
    assert alerts[0].risk_level == "HIGH"


def test_events_outside_time_window_do_not_trigger():
    base_time = datetime.now(timezone.utc)

    events = [
        make_event(
            "SIM_REREGISTRATION",
            "USER-001",
            base_time.isoformat(),
            "sim_swap",
        ),
        make_event(
            "pin.reset",
            "USER-001",
            (base_time + timedelta(seconds=301)).isoformat(),
            "mobile_money",
            outcome="success",
        ),
    ]

    alerts = detect_sim_swap_followed_by_pin_reset(
        events,
        window_seconds=300,
    )

    assert alerts == []


def test_successful_transfer_is_required():
    base_time = datetime.now(timezone.utc)

    events = [
        make_event(
            "SIM_REREGISTRATION",
            "USER-001",
            base_time.isoformat(),
            "sim_swap",
        ),
        make_event(
            "transaction.transfer",
            "USER-001",
            (base_time + timedelta(seconds=60)).isoformat(),
            "mobile_money",
            outcome="rejected",
        ),
    ]

    alerts = detect_sim_swap_followed_by_transfer(
        events,
        window_seconds=300,
    )

    assert alerts == []


def test_full_takeover_requires_correct_event_order():
    base_time = datetime.now(timezone.utc)

    events = [
        make_event(
            "pin.reset",
            "USER-001",
            base_time.isoformat(),
            "mobile_money",
            outcome="success",
        ),
        make_event(
            "SIM_REREGISTRATION",
            "USER-001",
            (base_time + timedelta(seconds=60)).isoformat(),
            "sim_swap",
        ),
        make_event(
            "transaction.transfer",
            "USER-001",
            (base_time + timedelta(seconds=120)).isoformat(),
            "mobile_money",
            outcome="success",
        ),
    ]

    alerts = detect_full_account_takeover_pattern(
        events,
        window_seconds=300,
    )

    assert alerts == []