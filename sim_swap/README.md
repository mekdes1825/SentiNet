# SentiNet Simulated SIM-Swap

## Purpose

This component simulates SIM re-registration scenarios using fictional
users, phone numbers, and SIM states.

It does not interact with real telecom networks, SIM cards, mobile-money
systems, or real user data.

## Components

- `models.py` — Defines simulated users, SIM states, and scenarios.
- `simulator.py` — Simulates SIM re-registration and state transitions.
- `events.py` — Creates structured event records.
- `demo.py` — Demonstrates a suspicious SIM re-registration.
- `../tests/test_sim_swap.py` — Tests the simulation behavior.

## SIM States

- `victim_controlled`
- `attacker_controlled`

## Scenarios

### Normal

A normal re-registration preserves victim control.

`victim_controlled → victim_controlled`

### Suspicious

A suspicious re-registration changes control from the victim to the
simulated attacker.

`victim_controlled → attacker_controlled`

A suspicious transition is rejected if the user is already
attacker-controlled.

## Event Format

Each event contains:

- `event_type`
- `user_id`
- `phone_number`
- `old_state`
- `new_state`
- `scenario`
- `timestamp`

The event type is `SIM_REREGISTRATION`. Timestamps are recorded in UTC
using ISO 8601 format.

Example:

```json
{
  "event_type": "SIM_REREGISTRATION",
  "user_id": "U001",
  "phone_number": "0900000000",
  "old_state": "victim_controlled",
  "new_state": "attacker_controlled",
  "scenario": "suspicious",
  "timestamp": "2026-10-23T10:13:40+00:00"
}
```

The timestamp above is illustrative.

## Run the Demo

From the repository root:

```bash
python3 -m sim_swap.demo
```

## Run Tests

From the repository root:

```bash
python3 -m pytest -q
```

The tests cover normal and suspicious transitions, invalid scenarios,
and repeated suspicious transitions.

## Integration

The event fields and event type should be coordinated with the
SentiNet detection-engine team before the shared event contract is
finalized.
