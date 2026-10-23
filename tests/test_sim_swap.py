import pytest

from sim_swap.models import SimUser, SIMState, SIMSwapScenario
from sim_swap.simulator import simulate_sim_reregistration


def test_normal_sim_reregistration():
    user = SimUser(
        user_id="U001",
        phone_number="0900000000",
    )

    event = simulate_sim_reregistration(
        user,
        SIMSwapScenario.NORMAL,
    )

    assert user.sim_state == SIMState.VICTIM_CONTROLLED
    assert event.event_type == "SIM_REREGISTRATION"
    assert event.scenario == "normal"
    assert event.old_state == "victim_controlled"
    assert event.new_state == "victim_controlled"


def test_suspicious_sim_reregistration():
    user = SimUser(
        user_id="U002",
        phone_number="0900000001",
    )

    event = simulate_sim_reregistration(
        user,
        SIMSwapScenario.SUSPICIOUS,
    )

    assert user.sim_state == SIMState.ATTACKER_CONTROLLED
    assert event.event_type == "SIM_REREGISTRATION"
    assert event.scenario == "suspicious"
    assert event.old_state == "victim_controlled"
    assert event.new_state == "attacker_controlled"


def test_invalid_scenario_is_rejected():
    user = SimUser(
        user_id="U003",
        phone_number="0900000002",
    )

    with pytest.raises(ValueError, match="Unknown SIM-swap scenario"):
        simulate_sim_reregistration(user, "suspicious")


def test_repeated_suspicious_transition_is_rejected():
    user = SimUser(
        user_id="U004",
        phone_number="0900000003",
    )

    simulate_sim_reregistration(user, SIMSwapScenario.SUSPICIOUS)

    with pytest.raises(ValueError, match="requires victim-controlled state"):
        simulate_sim_reregistration(user, SIMSwapScenario.SUSPICIOUS)

    assert user.sim_state == SIMState.ATTACKER_CONTROLLED


def test_normal_reregistration_preserves_attacker_state():
    user = SimUser(
        user_id="U005",
        phone_number="0900000004",
        sim_state=SIMState.ATTACKER_CONTROLLED,
    )

    event = simulate_sim_reregistration(
        user,
        SIMSwapScenario.NORMAL,
    )

    assert user.sim_state == SIMState.ATTACKER_CONTROLLED
    assert event.old_state == "attacker_controlled"
    assert event.new_state == "attacker_controlled"
    assert event.scenario == "normal"
