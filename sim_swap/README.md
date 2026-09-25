# SentiNet Simulated SIM-Swap

## Purpose

This component simulates SIM re-registration scenarios using fictional
users, phone numbers, and SIM states.

It is designed for the SentiNet fraud-detection simulation and does not
interact with real telecom networks, SIM cards, mobile-money systems,
or real user data.

## Components

- `models.py` - Defines fictional users, SIM states, and SIM-swap scenarios.
- `simulator.py` - Performs simulated SIM re-registration.
- `events.py` - Creates structured SIM-swap event records.
- `demo.py` - Demonstrates a simulated suspicious SIM re-registration.

## SIM States

The simulation uses two states:

- `victim_controlled`
- `attacker_controlled`

## Scenarios

### Normal

A normal SIM re-registration keeps the SIM under the user's control.

```text
victim_controlled → victim_controlled
