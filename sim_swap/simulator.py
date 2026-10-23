from .models import SimUser, SIMState, SIMSwapScenario
from .events import SIMSwapEvent


def simulate_sim_reregistration(
    user: SimUser,
    scenario: SIMSwapScenario,
) -> SIMSwapEvent:
    if not isinstance(scenario, SIMSwapScenario):
        raise ValueError("Unknown SIM-swap scenario")

    old_state = user.sim_state.value

    if scenario == SIMSwapScenario.NORMAL:
        new_state = user.sim_state

    elif scenario == SIMSwapScenario.SUSPICIOUS:
        if user.sim_state != SIMState.VICTIM_CONTROLLED:
            raise ValueError(
                "Suspicious SIM re-registration requires "
                "victim-controlled state"
            )

        new_state = SIMState.ATTACKER_CONTROLLED

    else:
        raise ValueError("Unknown SIM-swap scenario")

    user.sim_state = new_state

    return SIMSwapEvent.create(
        user_id=user.user_id,
        phone_number=user.phone_number,
        old_state=old_state,
        new_state=new_state.value,
        scenario=scenario.value,
    )
