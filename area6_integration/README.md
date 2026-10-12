# SentiNet — Work Area 6: Integration, Testing & Documentation

## Purpose

Work Area 6 connects the existing components through a small, explicit event
normalization boundary and records the current integration status. It does not
replace the existing work-area implementations.

## What this starter adds

- `bridge.py`: converts supported event shapes into Area 4's `DetectionEvent`
  contract. It handles the root `sim_swap` package's `sim.reregistration` name
  as well as the legacy Area 2 event format and Area 3 events through the
  existing Area 4 adapter.
- Area 1 phishing events (`phishing_viewed`, `phishing_clicked`, and
  `form_submitted`) can be represented in the shared event shape. They are not
  currently used by Area 4's account-takeover rules because the phishing events
  are session-oriented and the detector has no phishing rule yet.
- Automated tests for normalization and the SIM re-registration → PIN-reset
  detection path.

## Run tests

From the repository root, use:

```bash
python -m pytest -q
```

If pytest is not installed:

```bash
python -m pip install pytest Flask
python -m pytest -q
```

## Current integration findings

1. Area 4's adapter accepts the legacy event type `SIM_REREGISTRATION`.
2. The root `sim_swap` package emits `sim.reregistration`, with fields such as
   `previous_state` and `new_state`. The bridge translates this schema.
3. Area 3's event types are supported by the Area 4 adapter, including
   `pin.reset` and `transaction.transfer`.
4. Area 1 stores events in its own SQLite database and currently records
   `phishing_viewed`, `phishing_clicked`, and `form_submitted`. It is not yet
   connected to Area 4's live monitor.
5. Area 5's dashboard uses hard-coded mock alerts. It is not yet fetching the
   output of `RealTimeMonitor.summary()` from a server endpoint.
6. `SentiNet_Work_Area_2` and `SentiNet_Work_Area_3` contain separate packages
   both named `sentinet`; run their local demos/tests from their own folders to
   avoid Python importing the wrong `sentinet` package.

## End-to-end test scenario

Use only synthetic identifiers and simulated events:

1. Emit a suspicious simulated SIM re-registration for `USER-DEMO-1`.
2. Emit a successful fictional PIN reset for the same user within 300 seconds.
3. Confirm Area 4 produces a HIGH `ATO-001` alert.
4. Emit a successful virtual transfer for the same user within the detection
   window and confirm the relevant transfer/takeover rule is evaluated.
5. Confirm a legitimate-use scenario without the suspicious sequence does not
   create the same takeover alert.
6. Record test result, expected result, actual result, and any issue in the
   project issue tracker.

## Safety and limitations

All test identities and phone/account values are fictional. Do not connect this
simulation to real telecom or banking systems. Never place passwords, PINs, OTPs,
access tokens, or real customer information in events or screenshots. The bridge
normalizes event formats; it does not establish that an actor is genuine.

## Suggested next tasks

- Add a versioned shared event schema and contract tests for every producer.
- Add a small API endpoint that returns `RealTimeMonitor.summary()` and connect
  the dashboard to that endpoint.
- Decide how Area 1 sessions map to synthetic users before adding cross-area
  phishing correlation rules; do not infer that mapping from missing IDs.
- Add a root-level test command/CI workflow and a bug/acceptance-test template.
