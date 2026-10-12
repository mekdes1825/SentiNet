# SentiNet Work Area 6 — Test Plan

| ID | Scenario | Expected result | Current coverage |
|---|---|---|---|
| INT-01 | Normalize root `sim_swap` event | Area 4 event with `SIM_REREGISTRATION` type | Automated |
| INT-02 | Normalize phishing click with session ID only | Session retained; no invented user identity | Automated |
| INT-03 | SIM re-registration followed by PIN reset for same synthetic user within 300 seconds | HIGH `ATO-001` alert | Automated |
| INT-04 | Unknown event type | Clear `ValueError` | Automated |
| INT-05 | Suspicious SIM event followed by virtual transfer | Transfer-related alert is evaluated | Existing Area 4 integration test; bridge coverage should be expanded |
| INT-06 | Legitimate use without suspicious sequence | No takeover alert for that sequence | Existing component tests; add a unified scenario test |
| INT-07 | Dashboard fetches current monitor summary | Dashboard shows live alerts, not fixture data | Not implemented; dashboard currently uses mock data |
| INT-08 | Area 1 event appears in cross-area timeline | Phishing event normalized and stored with session ID | Normalization only; persistent unified storage not implemented |

## Defect log template

- **Issue ID:**
- **Component:**
- **Steps to reproduce:**
- **Expected result:**
- **Actual result:**
- **Severity:**
- **Environment / Python version:**
- **Test added:**
- **Fix verified by:**
- **Status:** Open / In progress / Fixed / Verified
