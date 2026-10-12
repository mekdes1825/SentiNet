from datetime import datetime, timedelta, timezone

import pytest

from area6_integration.bridge import normalize_event
from area4_detection.monitor import RealTimeMonitor


def test_normalize_new_root_sim_swap_event():
    event = {
        "event_id": "demo-1",
        "event_type": "sim.reregistration",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": "USER-DEMO-1",
        "phone_number": "PHONE-DEMO-1",
        "previous_state": "victim_controlled",
        "new_state": "attacker_controlled",
        "details": {"scenario": "suspicious", "control_changed": True},
    }
    normalized = normalize_event(event)
    assert normalized.event_type == "SIM_REREGISTRATION"
    assert normalized.source == "sim_swap"
    assert normalized.user_id == "USER-DEMO-1"
    assert normalized.details["scenario"] == "suspicious"


def test_area1_phishing_event_preserves_session_without_inventing_identity():
    event = {
        "id": 12,
        "event_type": "phishing_clicked",
        "session_id": "SESSION-DEMO-1",
        "user_id": None,
        "timestamp": "2026-10-12T10:00:00+00:00",
    }
    normalized = normalize_event(event)
    assert normalized.source == "phishing"
    assert normalized.event_type == "phishing_clicked"
    assert normalized.user_id == ""
    assert normalized.session_id == "SESSION-DEMO-1"


def test_normalized_sim_swap_and_pin_reset_trigger_area4_alert():
    base = datetime.now(timezone.utc).replace(microsecond=0)
    sim = normalize_event({
        "event_type": "sim.reregistration",
        "timestamp": base.isoformat(),
        "user_id": "USER-DEMO-2",
        "phone_number": "PHONE-DEMO-2",
        "previous_state": "victim_controlled",
        "new_state": "attacker_controlled",
        "details": {"scenario": "suspicious"},
    })
    reset = normalize_event({
        "event_type": "pin.reset",
        "timestamp": (base + timedelta(seconds=1)).isoformat(),
        "user_id": "USER-DEMO-2",
        "account_id": "ACCOUNT-DEMO-2",
        "phone_number": "PHONE-DEMO-2",
        "session_id": "SESSION-DEMO-2",
        "outcome": "success",
        "details": {"method": "fictional_demo_approval"},
    })
    monitor = RealTimeMonitor(window_seconds=300)
    monitor.add_event(sim)
    alerts = monitor.add_event(reset)
    assert any(alert.rule_id == "ATO-001" for alert in alerts)


def test_unknown_event_is_rejected():
    with pytest.raises(ValueError, match="Unsupported event type"):
        normalize_event({"event_type": "not.a.real.event"})
