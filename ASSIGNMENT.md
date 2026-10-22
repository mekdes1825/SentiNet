# Member 6 — App Integration, Demo, and Setup

## Files in this package
- `app.py`
- `demo.py`
- `templates/demo.html`
- `db.py`
- `README.md`
- `requirements.txt`
- `.gitignore`

## Purpose
Review app startup, blueprint registration, database initialization, demo scenario, and setup instructions. Coordinate with the project owner before changing shared interfaces.

## Review checklist
- [ ] Setup instructions match the current app.
- [ ] All blueprints register and app starts with the documented command.
- [ ] Demo scenario works from a clean database.
- [ ] Database schema/helpers stay compatible with all modules.
- [ ] No secrets, real credentials, or real financial data are included.

## Git workflow
1. Start from the latest shared repository baseline in your own feature branch.
2. Compare your assigned files with the branch before copying anything.
3. Make only your agreed, reviewable changes; do not overwrite unrelated files.
4. Run the relevant checks and record what you tested.
5. Commit and push your branch; open a pull request for review. Do not merge directly to main.

See `../SHARED_INTEGRATION_CONTRACT.md` for shared interfaces and safety boundaries.
