"""Command-line demo for SentiNet Work Area 2."""
import argparse, json
from datetime import datetime, timezone
from .sim_swap import SimRecord, SimSwapSimulator


def main() -> None:
    parser = argparse.ArgumentParser(description="SentiNet fictional SIM-swap demo")
    parser.add_argument("command", choices=["demo"])
    parser.add_argument("--scenario", choices=["normal", "suspicious"], default="suspicious")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    sim = SimSwapSimulator(SimRecord("USR-001", "+251-900-000-001", "SIM-001"))
    event = sim.reregister(actor="fictional_authorized_user" if args.scenario == "normal" else "simulated_unknown_actor",
                           suspicious=args.scenario == "suspicious", timestamp=datetime.now(timezone.utc))
    result = {"scenario": args.scenario, "current_state": sim.snapshot(), "event": event.to_dict()}
    print(json.dumps(result, indent=2) if args.json else
          f"Scenario: {args.scenario}\\nState: {sim.record.state}\\nEvent: {event.event_type}\\nTimestamp: {event.timestamp}")

if __name__ == "__main__":
    main()
