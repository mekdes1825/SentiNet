from sim_swap.models import SimUser, SIMState, SIMSwapScenario
from sim_swap.simulator import simulate_sim_reregistration


def test_normal_sim_reregistration():
    user = SimUser(
        user_id="U001",
        phone_number="0900000000"
    )

    event = simulate_sim_reregistration(
        user,
        SIMSwapScenario.NORMAL
    )

    assert user.sim_state == SIMState.VICTIM_CONTROLLED
    assert event.event_type == "SIM_REREGISTRATION"
    assert event.scenario == "normal"
    assert event.old_state == "victim_controlled"
    assert event.new_state == "victim_controlled"


def test_suspicious_sim_reregistration():
    user = SimUser(
        user_id="U002",
        phone_number="0900000001"
    )

    event = simulate_sim_reregistration(
        user,
        SIMSwapScenario.SUSPICIOUS
    )

    assert user.sim_state == SIMState.ATTACKER_CONTROLLED
    assert event.event_type == "SIM_REREGISTRATION"
    assert event.scenario == "suspicious"
    assert event.old_state == "victim_controlled"
    assert event.new_state == "attacker_controlled"
