# SentiNet — Work Area 2: Simulated SIM-Swap

A safe, local-only simulation of fictional phone-number/SIM ownership changes. It uses synthetic identities and never contacts telecom, banking, or real-money systems.

## Features
- Fictional user/phone/SIM records
- SIM states and ownership transition (victim-controlled → attacker-controlled)
- Timestamped, structured events with shared event fields
- Normal and suspicious scenarios
- CLI demo and automated tests
- JSON event output suitable for integration with Work Area 4

## Requirements
Python 3.10+; no third-party dependencies.

## Run
```bash
python -m sentinet.cli demo
python -m sentinet.cli demo --scenario suspicious --json
python -m unittest discover -s tests -v
```

## Event contract
Each event contains:
`event_id`, `event_type`, `timestamp`, `user_id`, `phone_number`, `sim_id`, `previous_state`, `new_state`, `actor`, `details`.

`event_type` is `sim.reregistration`. Suggested detection rule: correlate this event with `pin.reset` for the same `user_id` within a short window (e.g., 10 minutes). Work Area 4 should consume events, not trust the actor field as proof of identity.

## Scenarios
- `normal`: fictional user re-registers their SIM through a legitimate flow.
- `suspicious`: a simulated unauthorized actor changes the SIM control state. No real phone number or credentials are used.

## Safety
All names, numbers, IDs, and balances are fictional placeholders. The package has no network calls and does not store PINs or OTPs.
