# Member 3 — USSD, Virtual Wallet, and PIN Reset

## Files in this package
- `ussd.py`
- `templates/phone.html`

## Purpose
Carefully trace the full USSD menu, virtual wallet, PIN reset, verification, and transfer flow. The PIN-reset logic is the highest-priority review area.

## Review checklist
- [ ] Document the exact current PIN-reset steps before proposing changes.
- [ ] Test both successful and failed reset/verification paths.
- [ ] Test wrong-PIN handling and transfer success/blocking paths.
- [ ] Confirm all money and accounts are simulated; do not connect to real services.
- [ ] Record discrepancies as a short issue list instead of silently changing shared event names.

## Git workflow
1. Start from the latest shared repository baseline in your own feature branch.
2. Compare your assigned files with the branch before copying anything.
3. Make only your agreed, reviewable changes; do not overwrite unrelated files.
4. Run the relevant checks and record what you tested.
5. Commit and push your branch; open a pull request for review. Do not merge directly to main.

See `../SHARED_INTEGRATION_CONTRACT.md` for shared interfaces and safety boundaries.
