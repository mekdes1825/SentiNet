# SentiNet

Mobile-money fraud simulation and real-time behavioural detection. Fictional users, virtual money, no real telecom or banking. One Flask app, one SQLite file.

## Run it

    pip install -r requirements.txt
    python app.py            # http://127.0.0.1:5000

Chart.js loads from a CDN. For an offline demo, download `chart.umd.min.js` into `static/` and change the `<script>` tag in `templates/dashboard.html`.

Hardened mode (weaknesses switched off, for a before/after demo): set `SENTINET_HARDENED=1` before `python app.py`.

## Files and the work area each one covers

| File | Work area |
|---|---|
| `phishing.py`, `templates/phish_*.html` | 1. Phishing and human risk |
| `sim.py`, `templates/sim.html` | 2. SIM-swap |
| `ussd.py`, `templates/phone.html` | 3. USSD and mobile money |
| `detection.py`, `events.py` | 4. Detection engine, shared event log |
| `dashboard.py`, `templates/dashboard.html`, `static/dashboard.js`, `templates/rules.html` | 5. Dashboard |
| `db.py`, `demo.py`, `templates/demo.html`, `app.py` | 6. Integration, scenarios, testing |

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
