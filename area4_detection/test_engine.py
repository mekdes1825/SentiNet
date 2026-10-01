from datetime import datetime, timedelta, timezone

from .engine import BehavioralDetectionEngine
from .events import DetectionEvent


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


def test_full_account_takeover_pattern():
    base_time = datetime.now(timezone.utc)

    events = [
        make_event(
            "SIM_REREGISTRATION",
            "USER-001",
            base_time.isoformat(),
            "sim_swap",
            details={
                "scenario": "suspicious",
                "control_changed": True,
            },
        ),
        make_event(
            "pin.reset",
            "USER-001",
            (base_time + timedelta(seconds=60)).isoformat(),
            "mobile_money",
            outcome="success",
            details={
                "method": "fictional_demo_approval",
            },
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

    engine = BehavioralDetectionEngine(window_seconds=300)

    alerts = engine.analyze(events)

    assert len(alerts) >= 1

    critical_alerts = [
        alert
        for alert in alerts
        if alert.risk_level == "CRITICAL"
    ]

    assert len(critical_alerts) == 1

    alert = critical_alerts[0]

    assert alert.rule_id == "ATO-003"
    assert alert.user_id == "USER-001"
    assert "SIM_REREGISTRATION" in alert.matched_events
    assert "pin.reset" in alert.matched_events
    assert "transaction.transfer" in alert.matched_events


def test_unrelated_user_events_do_not_trigger_takeover():
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
            "USER-002",
            (base_time + timedelta(seconds=60)).isoformat(),
            "mobile_money",
            outcome="success",
        ),
    ]

    engine = BehavioralDetectionEngine(window_seconds=300)

    alerts = engine.analyze(events)

    assert alerts == []