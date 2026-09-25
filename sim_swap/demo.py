import json

from sim_swap.models import SimUser, SIMSwapScenario
from sim_swap.simulator import simulate_sim_reregistration


def main():
    user = SimUser(
        user_id="U001",
        phone_number="0900000000"
    )

    print("=== SentiNet SIM-Swap Simulation ===")
    print(f"User: {user.user_id}")
    print(f"Phone: {user.phone_number}")
    print(f"Initial SIM state: {user.sim_state.value}")

    event = simulate_sim_reregistration(
        user,
        SIMSwapScenario.SUSPICIOUS
    )

    print("\nSIM re-registration simulated.")
    print(f"Scenario: {event.scenario}")
    print(f"New SIM state: {user.sim_state.value}")

    print("\nGenerated event:")
    print(json.dumps(event.to_dict(), indent=4))


if __name__ == "__main__":
    main()
