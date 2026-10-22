# SentiNet: Dashboard, Alerts and Rules UI (Member 5)

The analyst-facing part of SentiNet. It shows live security alerts, explains why each one was raised, lets an analyst respond, and lets them tune the detection rules.

## What this module does

- **Security dashboard (`/dashboard`)**: summary cards, an alert list, an alert detail panel, two charts, an accounts table and a live event feed. The page polls the server every 3 seconds.
- **Alert response**: for a selected alert the analyst can restrict transfers, release transfers, or mark the alert resolved.
- **Rules page (`/rules`)**: view each detection rule and edit its time window, points and on/off switch.

## Files

| File | Role |
|---|---|
| `dashboard.py` | Flask blueprint with the pages and JSON API |
| `templates/dashboard.html` | Dashboard layout (extends `base.html`) |
| `templates/rules.html` | Rules editor page |
| `static/dashboard.js` | Polling, rendering, charts and alert actions |
| `static/style.css` | Styling |

## Routes and API

| Method | Route | Purpose |
|---|---|---|
| GET | `/dashboard` | Dashboard page |
| GET | `/api/state` | All dashboard data in one JSON response |
| GET | `/api/alerts/<id>` | One alert plus its event timeline |
| POST | `/api/alerts/<id>/action` | Body `{"action": "restrict" or "release" or "resolve"}` |
| GET / POST | `/rules` | View rules / save one rule |

### `/api/state` response shape

```json
{
  "now": 1761130000.0,
  "alerts": [{"id", "user_id", "user", "phone", "score", "level", "rules", "explanation", "recommended", "status", "first_ts", "updated", "restricted"}],
  "users": [{"name", "phone", "sim_state", "device", "hri", "risk", "restricted"}],
  "events": [{"id", "ts", "source", "type", "user", "details"}],
  "counts": {"<event_type>": 0},
  "scenario_rates": [{"scenario": "label", "rate": 0}],
  "metrics": {"active", "top_level", "hri", "sim", "pin_reset", "failed", "flagged_transfers"}
}
```

## How scores and levels work

Each triggered rule adds points. Scores are summed and capped at 100.

| Score | Level |
|---|---|
| 25+ | MEDIUM |
| 50+ | HIGH |
| 80+ | CRITICAL |

Rules are re-evaluated after every event, so changes made on the Rules page apply to the next event.

## Dependencies

This module depends on other parts of the project that are not in this folder:

- `db.py`: `query`, `execute`, `VISIBLE`
- `detection.py`: `human_risk`
- `events.py`: `log_event`
- `phishing.py`: `SCENARIOS`
- `templates/base.html`: the shared layout
- Chart.js 4.4.1, loaded from cdnjs (needs internet access during the demo)

## Running it

From the project root, with the shared app set up, run the Flask app and open `/dashboard` and `/rules`. Run the attack chain from the Demo control page to generate alerts.

## Manual test checklist

- [ ] `/dashboard` and `/rules` load with no template errors or browser console errors
- [ ] After running the attack chain, alerts appear and the cards and charts update
- [ ] Selecting an alert shows its explanation, recommended response and timeline
- [ ] Restrict, Release and Resolve each take effect after the next refresh
- [ ] Editing a rule and pressing Save persists the change
- [ ] Phishing, SIM and phone pages still look correct after the CSS changes

## Known limitations

- There is no login or access control on the dashboard or the action endpoints. This is acceptable for a local demo only.
- Forms have no CSRF protection.
- The page polls every 3 seconds rather than using websockets.
- Charts need the Chart.js CDN to be reachable.

## AI assistance disclosure

Parts of this code were generated with AI assistance and then reviewed and integrated by the team. Each member is responsible for understanding and being able to explain their own module.

## Team

Member 5: Dashboard, Alerts and Rules UI. Part of the SentiNet project.
