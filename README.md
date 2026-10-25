# SentiNet

Mobile-money fraud simulation and real-time behavioural detection. Fictional users, virtual money, no real telecom or banking. One Flask app, one SQLite file.

## Run it

    pip install -r requirements.txt
    python app.py            # http://127.0.0.1:5000

Chart.js loads from a CDN. For an offline demo, download `chart.umd.min.js` into `area5_dashboard/static/` and change the `<script>` tag in `area5_dashboard/templates/dashboard.html`.

`app.py` adds the area folders to the Python path and registers their template and static folders, so modules can import each other by name (`from db import ...`, `from events import log_event`). Keep `area4_detection/events.py` as the only module named `events` on that path. `sim_swap/events.py` is a separate SIM-swap event helper and is not imported by the app.

Hardened mode (weaknesses switched off, for a before/after demo): set `SENTINET_HARDENED=1` before `python app.py`.

## Test accounts and default PINs (simulation only)

These fictional accounts are seeded by `db.py` (`EED_USERS`). No real people, numbers or PINs are involved. Use them to log in to the USSD simulator for a normal drill.

| Participant | Phone (simulated) | Default PIN | Starting balance | Birth year |
|---|---|---|---|---|
| Abebe Kebede | 0900000001 | 1234 | 25,000 ETB | 1990 |
| Tigist Alemu | 0900000002 | 4321 | 18,000 ETB | 1988 |
| Dawit Tesfaye | 0900000003 | 1111 | 12,000 ETB | 1995 |
| Hana Mulugeta | 0900000004 | 2222 | 30,000 ETB | 1992 |
| Samuel Bekele | 0900000005 | 3333 | 9,000 ETB | 1985 |
| Marta Girma | 0900000006 | 4444 | 15,000 ETB | 1998 |
| Unknown Recipient | 0900000099 | 0000 | 100 ETB | 1980 |

`Unknown Recipient` is a passive transfer target for the suspicious-transfer scenario. It is not a participant, so do not log in with it during a normal drill.

### Running a normal drill

1. Start the server: `python app.py`
2. Open the USSD simulator (`templates/phone.html`) and log in as a participant with their phone number and default PIN.
3. Do normal activity: check the balance, send money to other participants.
4. Open the dashboard and confirm no alerts fire. This gives the detector a clean baseline before you run the SIM-swap and takeover scenario.

To change a PIN or balance, edit `EED_USERS` in `db.py` and re-seed the database.

The default PINs are for the lab only. They are stored hashed (see weakness 4 below), so this table is the only place they appear in plain text.

## Files and the work area each one covers

| File | Work area |
|---|---|
| `area1_phishing/phishing.py`, `area1_phishing/templates/phish_*.html` | 1. Phishing and human risk |
| `sim_swap/sim.py`, `templates/sim.html` | 2. SIM-swap |
| `ussd.py`, `templates/phone.html` | 3. USSD and mobile money |
| `area4_detection/detection.py`, `area4_detection/events.py` | 4. Detection engine, shared event log |
| `area5_dashboard/dashboard.py`, `area5_dashboard/templates/dashboard.html`, `area5_dashboard/templates/rules.html`, `area5_dashboard/static/dashboard.js` | 5. Dashboard |
| `db.py`, `demo.py`, `templates/demo.html`, `templates/base.html`, `app.py` | 6. Integration, scenarios, testing |

## The shared event format (table `events`)

`ts` (epoch seconds), `source` (phishing, sim, ussd, response, detector), `event_type`, `user_id`, `phone`, `session_id`, `device_id`, `details` (JSON). Every component writes through `events.log_event()`. A JSON-lines copy goes to `logs/events.jsonl`.

## Event names

phishing: message_opened, link_clicked, form_interaction, credential_submission_attempt, teachable_moment_viewed
sim: sim_reregistration, sim_restored
ussd: session_created (details.new_device), device_rejected, auth_success, pin_failed, balance_checked, pin_reset_requested, pin_reset_completed, reset_verification_failed, pin_changed, transfer_initiated, transfer_completed, transfer_blocked
response: transfers_restricted, transfers_released
detector: alert_raised, alert_escalated

## Detection rules (editable on the Rules page)

| Rule | Fires when | Points |
|---|---|---|
| R1 | PIN reset requested within 120 s of a SIM re-registration | 50 |
| R2 | 3 or more wrong PINs within 300 s | 25 |
| R3 | Session from an unfamiliar handset, then PIN reset, PIN change or transfer within 300 s | 20 |
| R4 | 2 or more account changes within 600 s of a SIM re-registration | 20 |
| R5 | Transfer within 600 s of a PIN reset | 30 |
| R6 | Another rule fired and the user's Human Risk Index is 60 or higher | 5 |

Levels: 25+ MEDIUM, 50+ HIGH, 80+ CRITICAL. Scores add up, capped at 100. Rules are re-run after every event, so the alert appears at the PIN reset (HIGH) and escalates at the transfer (CRITICAL).

## Human Risk Index

Per participant, each behaviour counts once: message opened 10, link clicked 30, form interaction 20, submission attempt 40 (max 100). The dashboard shows the average across participants.

## Controlled weaknesses (lab only)

1. PIN reset trusts the phone number alone (no second check).
2. Sessions never expire and are not tied to a handset.
3. No lockout after wrong PINs.
4. PINs hashed with unsalted MD5.

## Safety

Fictional data only. Phishing form inputs have no `name` attribute and the submit route never reads the request body, so typed values cannot be stored. Drills require a consent tick-box. Fictional brand "SentiPay" and a fictional dial code.
