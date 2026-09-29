# Work Area 3 Technical Documentation

## Purpose
Provide a small USSD-like mobile-money environment for the SentiNet scenario. It supports account authentication, balance inquiry, virtual transfers, PIN change, and a controlled fictional PIN-reset event.

## Menu concept
1. Check virtual balance
2. Transfer virtual funds
3. Change demo PIN
4. Reset demo PIN
0. Exit

The CLI runs deterministic demo flows; the Python class exposes the actions for future Flask/UI integration.

## Detection integration
Work Area 4 may correlate:
- `sim.reregistration` followed by `pin.reset` for the same `user_id` within the agreed time window.
- Repeated `auth.failure` events.
- `transaction.transfer` shortly after a reset or suspicious session.

Use `timestamp`, `user_id`, `session_id`, `event_type`, and `details`. Agree field names with the team before integration.

## Test matrix
| Test | Expected result |
|---|---|
| Correct demo PIN | Authentication success |
| Three incorrect PIN attempts | Account locked |
| Authenticated transfer within balance | Virtual balance decreases |
| Transfer without authentication | Rejected |
| PIN reset without demo approval flag | Rejected |
| Event log inspection | No PIN value appears |

## Boundaries
In-memory state only; no database persistence or web interface in this MVP. No real banking, telecom, real money, OTP, or personal data.
