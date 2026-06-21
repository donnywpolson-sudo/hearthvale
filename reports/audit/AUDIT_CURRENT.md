# Hearthvale Reusable Audit Prompt

You are auditing the local Hearthvale project at `C:\Users\donny\Desktop\hearthvale`.

Goal: inspect the current repository and produce one concise, evidence-based audit report of what should improve. This is read-only unless the user explicitly asks you to create or update report files under `reports\audit`. Do not fix code, data, tests, saves, generated files, launcher files, or docs during the audit.

## Hard Rules

* Verify `pwd`, `git rev-parse --show-toplevel`, and `git status --short` before deeper inspection. Stop if the path or repo root is wrong.
* Treat every modified or untracked file as user work. Do not clean, reset, checkout, stash, revert, delete, migrate, format, regenerate, commit, or install dependencies.
* Skip `.venv/`, `.pytest_cache/`, `__pycache__/`, `*.pyc`, `build/`, `dist/`, `logs/`, binary files, and real user data.
* Do not inspect real account/save contents unless explicitly asked: `users.db`, `saves/`, `savegame.json`.
* Do not run the game, launcher, build script, formatter, installer, or full pytest unless the user explicitly asks. Ask the user to run full/expensive checks when needed.
* Evidence must be concise: `path:line`, function/class/config key, command, or test name. Do not paste large source files or full logs.
* Code/docs mentioning a feature is not proof it is playable. Classify audited systems exactly as `fully implemented`, `partially implemented`, `partially wired`, `present but unused`, `stub/TODO`, `missing`, or `manually unverified`.
* Do not recommend protected clone content. Translate classic grindable RPG feel into original Hearthvale-safe mechanics, names, lore, items, quests, UI, progression, visuals, and audio.

## Required Context

Read targeted files only:

* `AGENTS.md`, `CODEX_HANDOFF.md` if present, `README.md`, `requirements.txt`, `.gitignore`
* `.codex\META_AUDIT.md` and `.codex\AUDIT.md` if present and readable; never write to `.codex`
* `game/settings.py`, `game/main.py`, `game/engine/app.py`
* `game/engine/save.py`, `game/engine/auth.py`, `game/engine/validation.py`, `game/tools/validate_data.py`
* Targeted files in `game/systems/`, `game/world/`, `game/ui/`, `game/data/`, `tests/`
* `launcher/`, `Hearthvale.spec`, `docs/`, and `GRAPHICS_ANIMATION_NOTE.md` only when relevant to launcher/build, assets, visuals, audio, originality, or docs drift

Expected stack and commands:

* Stack: Python 3.11, Panda3D, pytest
* Run: `python -m game.main`
* Validate data: `python -m game.tools.validate_data`
* Tests: `python -m pytest`
* Launcher build: `.\launcher\build_launcher.ps1`

## Required Searches

Use `rg` when available. Keep results summarized.

```powershell
rg -n "TODO|FIXME|pass|NotImplemented|stub|animation|sprite|tileset|audio|music|settings|save|schema|migration|inventory|equipment|bank|shop|combat|skill|XP|level|quest|dialogue|npc|trade|market|economy|auth|account|launcher|build" AGENTS.md README.md requirements.txt docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
rg -ni "runescape|osrs|stardew|runite|\brune\b" AGENTS.md README.md docs launcher game tests -g "!*.pyc" -g "!__pycache__/**"
```

Classify protected-term hits as policy text, legacy compatibility/migration coverage, generated/ignored drift, or unsafe active content drift.

## Safe Checks

Inspect `game/tools/validate_data.py` first. If it is read-only, run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m game.tools.validate_data
```

Run only targeted pytest checks that directly support audit findings and appear read-only, for example:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m pytest -p no:cacheprovider tests\test_validation.py tests\test_launcher.py
```

Run `git status --short` after checks and report whether the worktree changed.

## Systems To Audit

Audit implemented state, reachability, tests, risks, and highest-yield improvements for:

* Core loop: gather, process/craft, sell/use, level, unlock
* Skills/progression: XP curves, levels, unlocks, rewards, milestones, grind quality
* Gathering/resource nodes: depletion, respawn, tiers, tools, feedback
* Inventory/equipment/items: definitions, stackability, requirements, drops
* Crafting/processing: cooking, smelting, smithing, timing, XP, unlocks
* Combat: mobs, styles, damage, death, drops, equipment stats, ranged/magic
* Economy: coins, shops, buy/sell behavior, scarcity, resource dependency
* Banking/storage: UI reachability, deposit/withdraw, persistence
* NPCs/dialogue/quests: state, objective tracking, rewards, original activity design
* World/interaction: map size, pathfinding, object reachability, context actions, scenery
* UI/HUD/input: feedback, tabs, login, settings, accessibility/low friction
* Visuals/animation/assets/audio/style: procedural renderer hooks, placeholder geometry, authored asset gaps, audio/music gaps
* Time/persistence/routines: fixed or advancing time, routines, save/load/account boundaries
* Save/account/auth: local-only posture, username safety, migrations, legacy compatibility, user-data risk
* Data/schema validation: JSON coverage, cross-file references, originality guard, schema drift
* Tests: coverage, failing/skipped checks, manual checks
* Launcher/build/docs: launcher resolution, build script side effects, generated-output boundaries, README drift
* Originality/IP safety: active data, docs, tests, launcher, generated files, and recommendation wording

## Target Game Feel

Evaluate whether current systems support an original single-player grindable RPG with long-term account growth, meaningful skilling, multiple valid goals, gather-process-sell/use-level-unlock loops, scarcity, risk, visible milestones, simple sticky combat, memorable original NPC/quest/activity content, clear feedback, low friction, and safe nostalgic texture.

If social/community, trading, market, multiplayer, online-account, daily routine, or live-service goals are discussed, verify implemented support or label them `missing` or `manually unverified`.

## Prioritization

Rank recommendations by:

1. Failing validation/tests or save/data/originality risk.
2. Player value and core-loop impact.
3. Small safe scope and reuse of existing systems.
4. Testability.
5. Minimal refactor and no new dependencies.

Avoid broad rewrites, speculative architecture, generated-file churn, and clone-like feature requests.

## Required Report Format

Output exactly:

# Snapshot

* Local path:
* Repo root:
* Git status before:
* Git status after:
* Stack:
* Entry points:
* Run command:
* Test command:
* Data files:
* Save/account files:
* Checks run:
* Checks result:
* Worktree changed after checks:

# System Inventory

System | Status | Evidence | Notes

# Findings

Severity | Finding | Evidence | Why it matters | Recommended next step

# Game-Feel Assessment

Area | Status | Evidence | Gap | Safe recommendation

# Originality/IP Safety

Risk | Evidence | Classification | Recommendation

# Tests And Validation

Check | Result | Evidence | Notes

# Manual Verification Needed

Manual check | Why | Steps

# Recommended Next Work

Rank | Feature/Fix | Why | Complexity | Risk | Files likely touched | Acceptance criteria | Suggested tests

# Next Codex Prompt

A scoped implementation prompt ready to paste. It must ask for one small, testable improvement and repeat: do not copy protected content, preserve user work, and do not commit.
