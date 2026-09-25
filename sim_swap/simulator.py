from .models import SimUser, SIMState, SIMSwapScenario
from .events import SIMSwapEvent


def simulate_sim_reregistration(
    user: SimUser,
    scenario: SIMSwapScenario,
) -> SIMSwapEvent:

    old_state = user.sim_state.value

    if scenario == SIMSwapScenario.NORMAL:
        user.sim_state = SIMState.VICTIM_CONTROLLED

    elif scenario == SIMSwapScenario.SUSPICIOUS:
        user.sim_state = SIMState.ATTACKER_CONTROLLED

    else:
        raise ValueError("Unknown SIM-swap scenario")

    new_state = user.sim_state.value

    return SIMSwapEvent.create(
        user_id=user.user_id,
        phone_number=user.phone_number,
        old_state=old_state,
        new_state=new_state,
        scenario=scenario.value,
    )
