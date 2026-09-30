from datetime import datetime, timedelta, timezone

from .events import DetectionEvent
from .monitor import RealTimeMonitor


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


def test_monitor_detects_takeover_as_events_arrive():
    base_time = datetime.now(timezone.utc)

    monitor = RealTimeMonitor(window_seconds=300)

    first_alerts = monitor.add_event(
        make_event(
            "SIM_REREGISTRATION",
            "USER-001",
            base_time.isoformat(),
            "sim_swap",
            details={"scenario": "suspicious"},
        )
    )

    assert first_alerts == []

    second_alerts = monitor.add_event(
        make_event(
            "pin.reset",
            "USER-001",
            (base_time + timedelta(seconds=60)).isoformat(),
            "mobile_money",
            outcome="success",
        )
    )

    assert len(second_alerts) >= 1

    critical_alerts = [
        alert
        for alert in second_alerts
        if alert.risk_level == "CRITICAL"
    ]

    assert critical_alerts == []

    third_alerts = monitor.add_event(
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
        )
    )

    critical_alerts = [
        alert
        for alert in third_alerts
        if alert.risk_level == "CRITICAL"
    ]

    assert len(critical_alerts) == 1
    assert critical_alerts[0].rule_id == "ATO-003"


def test_monitor_keeps_users_separate():
    base_time = datetime.now(timezone.utc)

    monitor = RealTimeMonitor(window_seconds=300)

    monitor.add_event(
        make_event(
            "SIM_REREGISTRATION",
            "USER-001",
            base_time.isoformat(),
            "sim_swap",
        )
    )

    alerts = monitor.add_event(
        make_event(
            "pin.reset",
            "USER-002",
            (base_time + timedelta(seconds=60)).isoformat(),
            "mobile_money",
            outcome="success",
        )
    )

    assert alerts == []


def test_monitor_rejects_invalid_event():
    monitor = RealTimeMonitor()

    try:
        monitor.add_event({"event_type": "SIM_REREGISTRATION"})
    except TypeError:
        pass
    else:
        raise AssertionError("Expected TypeError for invalid event")