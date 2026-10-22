# SentiNet — Area 4: Detection & Event Logging

## Overview

Area 4 provides detection logic and event logging for SentiNet. It is designed to help identify suspicious activity by evaluating recorded security events and assessing potential human and account-related risks.

## Files

```text
area4_detection/
├── detection.py
├── events.py
└── README.md
```

### `detection.py`

Contains detection and risk-assessment logic. It evaluates event patterns and assigns risk scores to help identify potentially suspicious activity.

The detection rules cover patterns such as:

- SIM registration and PIN-reset activity
- Repeated PIN failures
- Activity from a new device
- Sensitive account actions
- Account changes and transfers
- Phishing-related risk signals

Alerts are categorized according to risk severity.

### `events.py`

Provides event-logging functionality. It records security events and connects event recording with detection evaluation.

## Integration Requirements

This implementation imports shared database functionality from `db.py`. The main SentiNet application must provide compatible database functions and tables.

The detection module also expects the database to contain the event, rule, alert, and user information required by its logic.

The module must be connected to the main application and tested with the expected database schema before it can be considered operational.

## Security Considerations

- Use authorized test data and controlled environments.
- Avoid recording passwords, PINs, or other secrets in event details.
- Restrict access to event logs and generated alerts.
- Validate event data before using it in detection decisions.

## Development Status

The replacement implementation consists of `detection.py` and `events.py`. Integration and functional testing are still required to verify database compatibility, event processing, risk scoring, and alert generation within SentiNet.
