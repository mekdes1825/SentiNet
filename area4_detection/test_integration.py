from datetime import datetime, timedelta, timezone

from .adapter import adapt_event
from .monitor import RealTimeMonitor


def test_area2_and_area3_end_to_end_takeover_detection():
    base_time = datetime.now(timezone.utc)

    # Area 2: simulated SIM re-registration event
    area2_sim_event = {
        "event_type": "SIM_REREGISTRATION",
        "user_id": "USER-001",
        "phone_number": "+251900000001",
        "old_state": "victim_controlled",
        "new_state": "attacker_controlled",
        "scenario": "suspicious",
        "timestamp": base_time.isoformat(),
    }

    # Area 3: simulated PIN reset event
    area3_pin_reset_event = {
        "event_id": "EVENT-001",
        "event_type": "pin.reset",
        "timestamp": (
            base_time + timedelta(seconds=60)
        ).isoformat(),
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

    # Area 3: simulated successful virtual transfer
    area3_transfer_event = {
        "event_id": "EVENT-002",
        "event_type": "transaction.transfer",
        "timestamp": (
            base_time + timedelta(seconds=120)
        ).isoformat(),
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

    monitor = RealTimeMonitor(window_seconds=300)

    # Adapt Area 2 event and send it to the detector.
    sim_event = adapt_event(area2_sim_event)
    alerts = monitor.add_event(sim_event)

    assert alerts == []

    # Adapt the Area 3 PIN-reset event.
    pin_reset_event = adapt_event(area3_pin_reset_event)
    alerts = monitor.add_event(pin_reset_event)

    # PIN reset after SIM re-registration should create a HIGH alert.
    high_alerts = [
        alert
        for alert in alerts
        if alert.risk_level == "HIGH"
    ]

    assert len(high_alerts) == 1
    assert high_alerts[0].rule_id == "ATO-001"

    # Adapt the Area 3 transfer event.
    transfer_event = adapt_event(area3_transfer_event)
    alerts = monitor.add_event(transfer_event)

    # The complete attack chain should now create a CRITICAL alert.
    critical_alerts = [
        alert
        for alert in alerts
        if alert.risk_level == "CRITICAL"
    ]

    assert len(critical_alerts) == 1

    critical_alert = critical_alerts[0]

    assert critical_alert.rule_id == "ATO-003"
    assert critical_alert.user_id == "USER-001"

    assert "SIM_REREGISTRATION" in critical_alert.matched_events
    assert "pin.reset" in critical_alert.matched_events
    assert "transaction.transfer" in critical_alert.matched_events

    # Confirm the monitor has recorded the complete event chain.
    recent_events = monitor.get_recent_events()

    assert len(recent_events) == 3
    assert recent_events[0].event_type == "SIM_REREGISTRATION"
    assert recent_events[1].event_type == "pin.reset"
    assert recent_events[2].event_type == "transaction.transfer"