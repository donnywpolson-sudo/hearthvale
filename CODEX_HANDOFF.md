# Snapshot
- Stack: Python 3.11, Panda3D, pytest
- Entry point: `python -m game.main`
- Focused tests: `python -B -m pytest -p no:cacheprovider tests/test_quest.py tests/test_validation.py`
- Current status: a new data-only mid-game quest, `forge_reserve`, is linked to a new `Forge Keeper` NPC near the smithing area.

# Changes
- Updated `game/data/quests.json` to add the `forge_reserve` quest with smithing, combat, and banking objectives plus coin, Smithing XP, and Attack XP rewards.
- Updated `game/data/world.json` to add `forge_keeper_01` at tile `[12, 14]`, linked to `forge_reserve`.
- Expanded `tests/test_quest.py` with shipped-quest coverage for `forge_reserve`, including one-time reward application across two skill rewards.
- Expanded `tests/test_validation.py` to assert the new quest and NPC link in shipped data.

# Checks
- `python -B -m game.tools.validate_data`: passed
- `python -B -m pytest -p no:cacheprovider tests/test_quest.py tests/test_validation.py`: passed (`51 passed`)

# Remaining Work
- Manual in-game verification is still needed because this batch did not run `python -m game.main`.
- Pre-existing unrelated worktree change remains in `AUDIT.md`.

# Next Prompt
Continue from `CODEX_HANDOFF.md`.

Next selected scope: manually verify the new `Forge Keeper` quest path in-game and fix only the smallest data-level issues if the smoke test exposes one.

Rules:
- Do not change save/auth, launcher/build, or unrelated gameplay systems.
- Do not add dependencies or protected/clone content.
- Preserve user work and do not commit.
- Keep scope limited to `game/data/quests.json`, `game/data/world.json`, and the smallest related test updates if a data fix is needed.

Task:
- Run `python -m game.main`.
- Log into a local test account, talk to the `Forge Keeper`, and verify the `Forge reserve` objective flow, NPC placement, completion text, and rewards.
- If the smoke test finds a data issue, make only the smallest data/test fix needed and rerun `python -B -m game.tools.validate_data` plus `python -B -m pytest -p no:cacheprovider tests/test_quest.py tests/test_validation.py`.

Stop when:
- The `Forge Keeper` quest is confirmed reachable and readable in-game, or one minimal data-only fix is applied and the targeted checks pass.
- Do not copy protected content, preserve user work, and do not commit.
