You are working locally in:

`C:\Users\donny\Desktop\runescape`

Goal: perform a **meta-audit** of the audit prompt below against the actual local RuneScape-style game project. Do not modify files. Produce a report only.

This is not an implementation task. This is an audit-of-the-audit:

1. Check whether the audit prompt is complete, safe, and effective.
2. Check whether it forces enough repo evidence.
3. Check whether it misses important local project realities.
4. Check whether it overreaches, duplicates work, or risks damaging user work.
5. Improve the prompt so future Codex runs produce better planning reports.

Original audit prompt to evaluate:

```text
You are working in my RuneScape-style game project.

Goal: inspect the current repo state, identify what is already implemented, find the highest-yield next work, and write the most efficient implementation plan. Do not modify files. Produce a planning report only.

First, read `AGENTS.md` and follow its project rules and output format.

Safety and repo hygiene:

* Run `git status --short` early.
* Treat all modified and untracked files as pre-existing user work.
* Do not revert, delete, format, overwrite, or clean up dirty-worktree changes.
* Do not run destructive commands.
* Do not install dependencies unless clearly necessary for inspection.
* Keep evidence concise with path references; do not paste large source files.

Targeted inspection:

* Run basic discovery: `pwd`, `git status --short`, top-level files/folders, README/docs/TODOs/config files.
* Identify stack, entry points, run commands, test commands, asset/data folders, save/data formats, and main gameplay systems.
* Inspect only the relevant source/data/test files needed to classify current systems accurately.
* Search for implemented, partial, unused, stubbed, TODO, and missing systems.
* Run safe existing checks if available, especially examples like:
  * `python -m pytest`
  * `python -m game.tools.validate_data`
* Report exact check commands and results. If checks fail, prioritize fixing those failures before new gameplay additions unless they are clearly unrelated.

Evaluate the game as an original RuneScape-inspired progression game:

* Identify systems such as movement, camera, map/world, NPCs, dialogue, quests, combat, enemies, loot, skills, gathering, crafting/processing, inventory, equipment, banking, shops, economy, XP/levels/unlocks, UI feedback, save/load, areas, audio, settings, and testing.
* Clearly separate:
  1. Fully implemented
  2. Partially implemented
  3. Present but unused
  4. Stub/TODO
  5. Missing but high-value
* Do not claim implementation without repo evidence.
* Do not recommend copying RuneScape/OSRS proprietary assets, names, dialogue, quests, maps, icons, music, or copyrighted content.

External research:

* Use web search only if available and useful for high-retention progression-loop context.
* Keep it secondary to repo evidence.
* Limit external citations to 2-3 high-quality links.
* If web search is unavailable, say so and rely on codebase analysis plus general design reasoning.

Prioritize additions by:

* Player value / fun added
* Reuse of existing code/assets
* Low implementation risk
* Progression depth
* Replayability
* Testability
* Minimal refactor required
* Fit with current architecture
* Ability to ship incrementally

Output a concise planning report using exactly this structure:

# Snapshot
- Stack:
- Entry points:
- Run command:
- Test command:
- Current status:

# Findings
System | Status | Evidence | Notes

# Recommended Next Work
Rank | Feature | Why | Complexity | Risk | Files likely touched

Rank 5-8 candidate additions. If tests or validation are failing, include a fix-first item at rank 1 unless clearly unrelated.

# Plan
Phase | Goal | Steps | Acceptance Criteria | Tests

Include phases for:

* Any safety/fix-first work needed
* First playable improvement
* Second playable improvement
* Third playable improvement, only if justified
* Polish/tests/balancing

# Next Codex Prompt
Write one scoped implementation prompt ready to paste for the highest-priority next task. It must be small, testable, avoid broad rewrites, protect dirty user work, and include exact tests/manual checks.

Constraints:

* Do not change files in this run.
* Do not invent implemented features.
* Prefer incremental additions over rewrites.
* Preserve current architecture unless there is a clear reason not to.
* Be blunt about weak spots, missing systems, failing checks, and technical debt.
* Keep the report practical, concise, and action-oriented.
```

Hard safety rules:

* Do not modify files.
* Do not run formatters.
* Do not run cleanup commands.
* Do not delete generated files.
* Do not revert or checkout anything.
* Do not commit.
* Treat every modified/untracked file as user work.
* If the repo is dirty, inspect but do not touch dirty files unless only reading them.
* Keep evidence concise with path references and line/function names where useful.

Required local discovery:

1. `cd C:\Users\donny\Desktop\runescape`
2. `pwd`
3. `git status --short`
4. List top-level files/folders.
5. Inspect:

   * `AGENTS.md`
   * `README.md`
   * `requirements.txt`
   * `.gitignore`
   * docs/TODO files if present
   * `game/`
   * `game/data/`
   * `tests/`
   * launcher/build files if present
6. Search for:

   * `TODO`
   * `pass`
   * `NotImplemented`
   * `stub`
   * `FIXME`
   * `RuneScape`
   * `OSRS`
   * `Stardew`
   * `rune`
   * `runite`
   * `animation`
   * `quest`
   * `dialogue`
   * `audio`
   * `settings`
7. Run safe checks if available:

   * `python -m pytest`
   * `python -m game.tools.validate_data`

If tests are slow or fail:

* Report the exact command, failure summary, and likely relevance.
* Do not fix anything.
* Do not continue pretending the repo is green.

Meta-audit tasks:

## 1. Prompt coverage audit

Evaluate whether the original audit prompt adequately covers:

* repo hygiene
* dirty worktree protection
* no-modification requirement
* local vs remote repo confusion
* exact command reporting
* evidence standards
* asset/copyright/originality constraints
* current gameplay system classification
* tests/validation
* save/data compatibility
* highest-yield prioritization
* Codex prompt output quality
* risk of broad/unbounded recommendations
* risk of missing visuals/animations/audio/settings
* risk of recommending protected clone-like content

## 2. Repo-reality check

Compare the prompt against the actual local project:

* Does the prompt ask for every file/folder that matters?
* Does it miss generated/build/launcher paths that matter?
* Does it miss assets, visuals, animation systems, or style files?
* Does it miss save/account/auth files?
* Does it miss validation/schema files?
* Does it miss tests that reveal actual behavior?
* Does it ask for too much irrelevant inspection?
* Does it produce enough evidence to prevent hallucinated features?

## 3. Current-state risk check

Identify any risks the audit prompt should force future Codex runs to catch:

* failing tests
* validation failures
* dirty worktree
* broken launcher/build docs
* save migration risks
* data schema drift
* copyrighted/protected naming drift
* hardcoded quest/dialogue content
* visual/animation gaps
* backend/UI mismatch, such as HUD showing slots unsupported by backend
* obsolete docs or README mismatch
* untested new systems
* present-but-unused modules

## 4. Improved audit prompt

Write an improved version of the original audit prompt.

Requirements for improved prompt:

* Still read-only.
* Still concise.
* Still outputs the same planning-report structure.
* Stronger about local path verification.
* Stronger about checking recent visual/animation work.
* Stronger about checking tests and validation.
* Stronger about originality drift.
* Stronger about distinguishing implemented vs partially wired vs manually unverified.
* Avoids over-inspection and huge pasted files.
* Includes exact commands.
* Includes “do not fix” language unless the user explicitly asks implementation.
* Includes manual-check recommendations but does not require running the game unless feasible.

Output exactly:

# Meta-Audit Snapshot

* Local path:
* Git status:
* Checks run:
* Checks result:
* Prompt verdict:

# Audit Prompt Strengths

Issue | Why it helps | Evidence from prompt/repo

# Audit Prompt Weaknesses

Issue | Risk | Concrete improvement

# Repo-Reality Gaps The Prompt Should Catch

Gap | Evidence | Why it matters

# Improved Audit Prompt

A ready-to-paste replacement prompt.

# Recommended Use

* When to use original prompt:
* When to use improved prompt:
* When to split into smaller prompts:
* Highest-risk thing to verify before any implementation:
