# Work Area 2 Technical Notes

## Scope
Implements only the fictional SIM re-registration state model. SIM state starts as `victim_controlled`. A normal replacement keeps account control with the fictional user; a suspicious event changes it to `attacker_controlled`.

## Shared event schema
- `event_id`: unique UUID
- `event_type`: stable integration key, `sim.reregistration`
- `timestamp`: ISO-8601 UTC timestamp
- `user_id`, `phone_number`, `sim_id`: synthetic identifiers
- `previous_state`, `new_state`: transition values
- `actor`: scenario label, not verified identity
- `details`: scenario, whether control changed, and environment marker

Work Area 4 can correlate `sim.reregistration` with `pin.reset` using `user_id` and timestamps. The team should agree on exact field names before integration.

## Test matrix
| Case | Input | Expected |
|---|---|---|
| Normal re-registration | suspicious=false | State remains victim_controlled |
| Suspicious re-registration | suspicious=true | State becomes attacker_controlled |
| Blank actor | actor is whitespace | Reject |
| Naive timestamp | timestamp lacks timezone | Reject |

## Limitations
In-memory only; restart clears events. No database, web server, telecom API, real credentials, or real transaction support. These are intentional MVP boundaries.
