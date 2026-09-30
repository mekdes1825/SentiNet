# SentiNet — Work Area 3: USSD & Mobile-Money Simulation

A local-only, fictional USSD-style menu and mobile-money account simulator. No telecom/bank APIs, real money, real credentials, OTPs, or network calls.

## Requirements
Python 3.10+; standard library only.

## Run demos
```bash
python -m sentinet.cli
python -m sentinet.cli --scenario transfer
python -m sentinet.cli --scenario failed-auth
python -m unittest discover -s tests -v
```

## Implemented
- Synthetic account, phone, demo PIN, and virtual balance
- Authentication and three-failure lockout
- Balance view, virtual transfer, PIN change, controlled demo PIN reset
- Structured timestamped events for Work Area 4
- Test cases for authentication, lockout, transfer, reset, and credential-safe event logging

## Event types
`auth.success`, `auth.failure`, `account.balance_viewed`, `transaction.transfer`, `pin.change`, `pin.reset`.

Events include `event_id`, `event_type`, `timestamp`, `user_id`, `account_id`, `phone_number`, `session_id`, `outcome`, and `details`. PIN values are never placed in event records.

## Safety
All identifiers and values are synthetic. Currency label `SIM-ETB` denotes simulated units, not Ethiopian birr or redeemable funds. The demo PIN is in-memory only and must not be reused as a real PIN.
