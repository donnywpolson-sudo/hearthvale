# Next Codex Prompt

Source report: reports\audit\AUDIT_REPORT_20260622_210730.md
Latest report pointer: reports\audit\AUDIT_REPORT_LATEST.md
Selected batch prompt path: reports\audit\NEXT_REMEDIATION_PROMPT.md
Selected batch: Time progression plumbing
Severity: Medium

Implement exactly one small, testable improvement: make Hearthvale time advance during gameplay while preserving existing save/load behavior.

Scope:
- Update only the smallest set of files needed for time progression and its display.
- Preserve user work and do not touch unrelated systems.
- Do not copy protected content.
- Do not commit.

Task:
- Change the time model so it advances from `GAME_MINUTES_PER_REAL_SECOND` instead of resetting to fixed noon every frame.
- Keep save/load compatibility intact.
- Update the focused tests so the new behavior is covered.

Validation:
- `python -B -m pytest -p no:cacheprovider tests/test_time.py tests/test_save.py`
- `python -B -m game.tools.validate_data`
- Optional manual smoke: `python -m game.main` and confirm the clock advances.

Stop when:
- Time advances in play, save/load still works, the focused tests pass, and no unrelated files were modified.
