# META_AUDIT.md

You are auditing the local Hearthvale project.

Project root:

`C:\Users\donny\Desktop\hearthvale`

Goal: perform a **read-only meta-audit** of the audit prompt below against the actual local Hearthvale game project.

This is a report-only audit unless the user explicitly asks you to create a timestamped report file.

The audit should improve future `AUDIT.md` / Codex audit prompts so they better evaluate whether Hearthvale is becoming a strong original classic grindable RPG with:

* long-term account-building progression
* meaningful skilling
* satisfying resource/economy loops
* memorable quests and activities
* better graphics, animation, UI, audio, and settings
* stronger persistence and save compatibility
* better player goals and achievement weight
* original nostalgic texture without copying protected IP

Do **not** implement fixes.

Do **not** modify project files unless the user explicitly asks for one timestamped report file.

---

## Hard Rules

* Do not modify source, data, tests, saves, lockfiles, generated output, build output, caches, or user work.
* Do not delete, clean, normalize, migrate, regenerate, reset, checkout, stash, commit, or revert anything.
* Treat every modified or untracked file as pre-existing user work unless you created it in this turn.
* Record `git status --short` before checks and after checks.
* If asked to create a report file, create exactly one timestamped audit report file and no other files.
* If not asked to create a report file, do not create files.
* Do not run formatters.
* Do not install dependencies.
* Do not run commands likely to generate, overwrite, migrate, cache, normalize, or rewrite project files.
* Do not paste large source files.
* Do not implement fixes.
* Do not recommend broad rewrites.
* Do not recommend protected clone content.
* Translate the desired classic grindable RPG feel into original Hearthvale-safe mechanics, names, lore, UI, items, quests, progression, visuals, and audio.
* Evidence must be concise: path + line/function/class/config key when useful.
* Code/docs mentioning a system is not proof that the system is playable.
* A system only counts as playable if the audit can show how a player reaches and uses it.

---

## Original Audit Prompt To Evaluate

```text
[PASTE ORIGINAL AUDIT PROMPT HERE]
```

---

## Target Game Feel

Target feel: **classic grindable account-building RPG progression** translated into original Hearthvale-safe content.

Do not copy protected IP.

Audit whether the original prompt properly evaluates this project for:

* long-term account-building progression
* meaningful skilling as a main playstyle
* resource gathering, refining, crafting, banking, selling, using, and upgrading
* single-player economy loops, shops, banking, and resource dependency
* sandbox freedom and multiple valid goals
* daily routines and persistence
* satisfying grind vs empty grind
* social/community feel only when supported by implemented code or explicitly labeled missing/manual verification needed
* memorable quest/activity design
* rarity, scarcity, risk, and achievement weight
* simple but sticky combat
* accessibility / low mechanical friction
* nostalgic old-school texture through original Hearthvale-safe content
* originality and copyright/IP safety
* graphics, sprites, animation, tilesets, UI, audio, music, and settings polish
* save/load compatibility and persistence
* backend/UI consistency
* implemented systems being reachable in gameplay

---

## System Classification Requirement

Classify each audited system as one of:

* fully implemented
* partially implemented
* partially wired
* present but unused
* stub/TODO
* missing
* manually unverified

Use this distinction strictly:

* **Fully implemented**: code, data, UI/reachability, and tests/manual evidence show the player can use it.
* **Partially implemented**: core logic exists but some behavior, UI, data, tests, or player flow is incomplete.
* **Partially wired**: pieces exist but are not fully connected to gameplay.
* **Present but unused**: file/class/data exists but no evidence it is called or reachable.
* **Stub/TODO**: placeholder, pass, TODO, FIXME, NotImplemented, or intentionally incomplete.
* **Missing**: no meaningful evidence found.
* **Manually unverified**: cannot be proven safely from code/tests/docs alone.

For every major system, prefer this table:

System | Status | Evidence | Reachable in gameplay? | Player value | Main gap | Best next improvement

---

## Required Local Verification

### 1. Enter repo

```powershell
cd C:\Users\donny\Desktop\hearthvale
```

### 2. Verify exact location, repo root, and dirty worktree state

```powershell
pwd
git rev-parse --show-toplevel
git status --short
```

If the path or repo root is wrong, stop and report.

If the worktree is dirty, continue read-only only. Treat all modified/untracked files as user work.

### 3. List top-level files/folders read-only

```powershell
Get-ChildItem -Force | Select-Object Mode,Length,LastWriteTime,Name
```

### 4. Read only if present and relevant

Use targeted reads. Do not dump large files.

Read these if present:

* `AGENTS.md`
* `README.md`
* `.gitignore`
* `requirements.txt`
* docs/TODO/planning files
* launcher/build/package files
* config/settings files
* schema/validation files
* save/account/auth-related files
* asset/style/sprite/animation/audio/settings-related files
* targeted files under `game/`
* targeted files under `game/data/`
* targeted files under `tests/`

Prioritize files that prove actual gameplay behavior, not just planned systems.

### 5. Search with concise evidence

Run a broad but targeted search:

```powershell
rg -n "TODO|FIXME|pass|NotImplemented|stub|animation|sprite|spritesheet|tileset|tilemap|texture|palette|shader|lighting|shadow|particle|audio|music|sound|sfx|volume|settings|accessibility|quest|dialogue|npc|shop|bank|inventory|equipment|craft|recipe|resource|gather|forage|mine|fish|farm|wood|ore|bar|herb|combat|enemy|loot|drop|rare|collection|achievement|milestone|skill|XP|level|unlock|progression|save|load|schema|migration|account|auth|launcher|build|package|economy|trade|market|daily|routine|calendar|weather" AGENTS.md README.md .gitignore requirements.txt launcher game tests -g "!*.pyc" -g "!__pycache__/**"
```

Also search for protected-content drift terms from `AGENTS.md` and report any hits as concise evidence.

If `rg` is unavailable, use a read-only PowerShell equivalent and report that fallback.

### 6. Inspect validation before running

Before running validation, inspect the tool first:

```powershell
Get-Content .\game\tools\validate_data.py -TotalCount 220
```

Only run validation if clearly read-only:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m game.tools.validate_data
```

Skip validation if it may write files, migrate data, normalize saves, rewrite generated assets, or modify caches.

### 7. Inspect tests before running

Run tests only if they appear safe/read-only:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m pytest -p no:cacheprovider
```

If tests might write files, modify saves, generate snapshots, regenerate assets, alter caches, or mutate user data, skip and explain why.

### 8. After checks, verify worktree again

```powershell
git status --short
```

If worktree status changed, report it immediately. Do not clean it up.

---

# Meta-Audit Tasks

## 1. Prompt Coverage Audit

Evaluate whether the original audit prompt adequately covers:

* local path verification
* local vs remote repo confusion
* repo hygiene
* dirty worktree protection
* no-modification requirement
* generated-file protection
* exact command reporting
* evidence standards
* concise path/line/function evidence
* asset/copyright/originality constraints
* target game feel
* implemented vs partial vs unused vs stubbed vs missing systems
* playable behavior vs code presence
* visuals, animation, sprite, tileset, style, audio, music, and settings
* save/load compatibility
* account/auth/save-data risks
* data/schema/validation compatibility
* tests and validation
* launcher/build docs
* README/docs drift
* highest-yield prioritization
* Codex prompt output quality
* risk of broad rewrites
* risk of over-inspection
* risk of hallucinated implemented features
* risk of recommending protected clone-like content
* risk of missing the intended grindy, systems-driven feel
* risk of treating “long grind” as “good grind”
* risk of ignoring graphics/audio/UI feedback
* risk of systems existing in code but being unreachable in gameplay
* risk of recommending social/community systems not supported by implemented multiplayer or market mechanics

---

## 2. Repo-Reality Check

Compare the original audit prompt against the actual local project.

Answer:

* Does it ask for every file/folder that matters?
* Does it miss generated/build/launcher paths?
* Does it miss assets, visuals, animations, audio, style, or settings files?
* Does it miss save/account/auth files?
* Does it miss validation/schema files?
* Does it miss tests that reveal actual behavior?
* Does it ask for too much irrelevant inspection?
* Does it force enough evidence to prevent hallucinated features?
* Does it distinguish fully implemented, partially implemented, partially wired, present-but-unused, stubbed, missing, and manually unverified systems?
* Does it distinguish code existence from playable behavior?
* Does it evaluate whether current systems support the target feel through original Hearthvale-safe content?
* Does it check whether gameplay systems are reachable from UI/player flow?
* Does it check whether graphics/audio feedback supports repeated actions?
* Does it check whether skilling can be a main playstyle?
* Does it check whether economy loops have inputs, outputs, sinks, and progression value?

---

## 3. Current-State Risk Check

Identify risks that the original audit prompt should force future Codex runs to catch:

* failing tests
* skipped tests
* validation failures
* dirty worktree
* broken launcher/build docs
* README/docs mismatch
* save migration risks
* data schema drift
* hardcoded protected naming drift
* protected-like names, quests, maps, icons, music, dialogue, formulas, or terminology
* recommendations that copy protected content instead of translating the desired feel into original design
* grind that is long but not meaningful
* combat crowding out skilling, economy, quests, collection, or exploration goals
* economy/trading/social goals not supported by implemented multiplayer or market mechanics
* lack of rarity, scarcity, risk, or visible milestones
* visual/animation gaps
* audio/settings gaps
* backend/UI mismatch
* systems present in code but unreachable in gameplay
* untested new systems
* present-but-unused modules
* manual checks required but undocumented
* missing level-up, rare-drop, gathering, crafting, shop, bank, or combat feedback
* missing tooltips, unlock previews, collection logs, or next-goal guidance
* missing resource sinks that make gathering/crafting/economy meaningful
* stale save files or schema changes that could break player progress

---

## 4. Game-Feel Audit

Audit whether the current project supports the intended classic grindable RPG feel through original Hearthvale-safe design.

For each major gameplay pillar, report:

Pillar | Current status | Evidence | Reachable in gameplay? | What works | What feels weak | Best small next step

Pillars:

* movement and interaction
* inventory
* banking/storage
* shops
* economy/resource value
* gathering
* refining
* crafting
* combat
* equipment
* food/consumables
* quests
* NPC dialogue
* exploration
* area unlocks
* skill XP/levels
* unlock tables
* collection/achievement tracking
* rare drops/rare finds
* save/load persistence
* settings/accessibility
* graphics/sprites/tilesets
* animation/feedback
* audio/music/SFX
* launcher/build/run flow

Do not invent features. If evidence is missing, say so.

---

## 5. Grind Quality Audit

For each skill or repeatable activity, answer:

* What does the player do moment-to-moment?
* What short-term reward happens within 1–5 minutes?
* What medium-term unlock happens within 30–60 minutes?
* What long-term goal exists after several sessions?
* What new options unlock from leveling?
* Does the output feed another system?
* Does the activity require choices, routes, upgrades, risk, scarcity, or planning?
* Does the activity have clear visual/audio/UI feedback?
* Is the grind meaningful, or only time-consuming?
* What would make it more satisfying without a broad rewrite?

Use this table:

Activity | Evidence | Output | Sink/use | Unlocks | Feedback | Grind quality | Smallest useful improvement

---

## 6. Economy Loop Audit

Map actual implemented loops.

Use this table:

Input resource | Source | Processing step | Output item | Use case | Sink | Shop/bank support | Evidence | Gap

Look for loops such as:

* gather → refine → craft → use/sell/upgrade
* monster drop → crafting/economy/quest use
* farming/gathering → consumable → combat/skilling support
* quest reward → unlock → new area/resource/activity
* shop purchase → tool upgrade → faster or broader progression
* rare resource → special item/cosmetic/quest/upgrade

Flag loops that are:

* complete and playable
* partially wired
* missing a sink
* missing a reward
* missing UI support
* missing save persistence
* present in data but unreachable
* manually unverified

---

## 7. Graphics / Animation / UI / Audio Audit

Audit current evidence for:

### Graphics

* sprite consistency
* tileset cohesion
* readable silhouettes
* palette consistency
* original visual identity
* item icons
* NPC/enemy identity
* environment variety
* lighting/shadow/particle support if present

### Animation

* idle animations
* walk animations
* gathering animations
* crafting feedback
* shop/bank interaction feedback
* combat attack/hit feedback
* damage/death feedback
* level-up feedback
* rare-drop/rare-find feedback

### UI

* inventory readability
* bank usability
* shop usability
* equipment screen clarity
* skill screen clarity
* quest journal clarity
* tooltip/examine text
* unlock preview
* collection/achievement visibility
* settings menu
* control remapping if present
* text scale/readability

### Audio

* music
* ambience
* UI sounds
* gathering sounds
* crafting sounds
* combat sounds
* shop/bank sounds
* level-up sound
* rare-drop sound
* volume controls
* mute settings

Use this table:

Area | Evidence | Current status | Player impact | Gap | Smallest useful improvement

Label anything not safely proven as `manual verification needed`.

---

## 8. Originality / IP Safety Audit

Do not recommend clone content.

Translate classic grindable RPG feel into original Hearthvale-safe systems.

Check for protected-content drift in:

* names
* skill terminology
* item names
* quest names
* map/area names
* icons
* UI layout
* formulas
* dialogue
* music/audio references
* NPC names
* enemy names
* progression tables
* economy structures
* tutorial phrasing
* jokes/references
* placeholder names

If any protected-like content appears, report concise evidence and recommend original Hearthvale replacements.

Do not suggest copying:

* protected names
* protected quest structures
* protected map layouts
* protected icon shapes
* protected UI arrangements
* protected music style too closely
* protected formulas/tables
* protected dialogue or terminology

Safe translation examples:

* “classic account-building progression” instead of naming a protected game as the design target
* “resource dependency loops” instead of copying exact skill/item systems
* “original Hearthvale professions” instead of protected skill names
* “town request board” instead of copied quest/activity structures
* “Hearth Ledger” or another original tracking system instead of copied collection interfaces

---

## 9. Manual Playtest Checks

Do not claim these passed unless actually verified.

If running the game is feasible and safe, recommend manual checks. If not feasible, list them under `manual verification needed`.

Recommended checks:

### 10-minute new-player test

Expected result:

* player understands movement
* first interaction is clear
* first goal is clear
* inventory is understandable
* first reward happens quickly
* next step is obvious

### 60-minute progression test

Expected result:

* player experiences at least one meaningful unlock
* player completes or advances one economy loop
* player sees at least one milestone
* player understands at least two possible goals

### Skilling-main test

Expected result:

* player can spend a session progressing without combat being mandatory
* skilling outputs matter
* tools/resources/upgrades are visible
* bank/shop/crafting support the loop

### Sandbox-goal test

Expected result:

* player can choose between skilling, questing, combat, collecting, crafting, shopping, or exploration
* at least three goals are visible or discoverable
* progress is persistent

### Feedback test

Expected result:

* common actions have clear visual/audio/UI feedback
* leveling/unlocks feel noticeable
* rare events are visible
* failure/blocked actions explain why

---

## 10. Improvement-Ideas Policy

Improvement ideas are allowed only as report recommendations.

Separate them into:

1. **Audit-prompt improvements**

   Changes that make future audit/planning Codex runs safer, more evidence-based, or more useful.

2. **Project improvement candidates**

   Possible future game improvements discovered from repo evidence.

Rules:

* Do not implement anything.
* Do not modify files unless explicitly asked to create the timestamped report.
* Do not invent features.
* Do not recommend broad rewrites.
* Do not recommend protected clone content.
* Translate classic grindable RPG feel into original systems, names, lore, items, quests, UI, progression, visuals, and audio.
* Every idea must cite repo evidence or be labeled `manual verification needed`.
* Prefer small, testable, incremental work.
* Prefer fixes for failing tests/validation before new gameplay unless clearly unrelated.
* Prefer improvements to existing reachable systems before brand-new systems.
* Prefer improving player feedback for existing actions before adding content.
* Prefer making economy loops complete before adding more resources.
* Prefer save/schema safety before persistence-affecting changes.

Recommendation format:

Priority | Area | Evidence | Problem | Smallest useful improvement | Expected player impact | Risk | Test/verification

Priority order:

1. broken tests, validation, save/load, schema, or launcher issues
2. unreachable systems
3. missing feedback for existing actions
4. weak economy/skilling loops
5. progression and milestone clarity
6. visual/audio/UI polish
7. new content only after core loops work

---

# Required Output Format

Output exactly these sections:

# Meta-Audit Snapshot

* Local path:
* Repo root:
* Git status:
* Checks run:
* Checks result:
* Worktree changed after checks:
* Prompt verdict:

# Audit Prompt Strengths

Issue | Why it helps | Evidence from prompt/repo

# Audit Prompt Weaknesses

Issue | Risk | Concrete improvement

# Repo-Reality Gaps The Prompt Should Catch

Gap | Evidence | Why it matters

# Current-State Risks Future Audits Should Force

Risk | Evidence | How the improved prompt should catch it

# Game-Feel Gaps Future Audits Should Force

Gap | Evidence | Why it matters | How the improved prompt should catch it

# Graphics / Animation / UI / Audio Gaps

Area | Evidence | Player impact | Recommended audit coverage

# Economy / Skilling / Progression Gaps

Loop or system | Evidence | Current status | Missing link | Recommended audit coverage

# Originality / IP Safety Risks

Risk | Evidence | Safer Hearthvale-safe direction

# Improvement Ideas Allowed?

* Prompt improvement ideas:
* Project improvement ideas:
* Boundaries:

# Improved Audit Prompt

A ready-to-paste replacement prompt.

The improved prompt must:

* be read-only unless the user explicitly asks for a report file
* be concise
* preserve the same report-only purpose
* verify the local path strongly
* protect dirty worktree/user changes strongly
* require exact command reporting
* handle tests and validation safely
* check recent visual/animation/audio/settings work
* check originality drift and protected-content risk
* audit for target game feel without recommending direct clone content
* check save/data/schema compatibility
* distinguish:

  * fully implemented
  * partially implemented
  * partially wired
  * present but unused
  * stub/TODO
  * missing
  * manually unverified
* avoid over-inspection
* avoid pasted source dumps
* include "do not fix" language
* include manual-check recommendations
* not require running the game unless feasible and safe
* include a playable-proof standard
* include grind-quality checks
* include economy-loop checks
* include graphics/audio/UI feedback checks
* include original Hearthvale-safe improvement ideas only when evidence-backed or labeled manual verification needed

# Recommended Use

* When to use original prompt:
* When to use improved prompt:
* When to split into smaller prompts:
* Highest-risk thing to verify before any implementation:

---

# Good Project Improvement Candidates To Look For

These are not automatic recommendations. Future audits may recommend them only if repo evidence supports them or if labeled `manual verification needed`.

## Account Progression

Potential ideas:

* original account ledger showing skills, quests, collections, rare finds, zones, lifetime stats, and milestones
* visible unlock tables
* milestone popups
* long-term cosmetic goals
* house/base/town upgrades
* persistent player history

Audit question:

Does the current project give the player a reason to care about long-term progress?

## Skilling

Potential ideas:

* each skill has tools, resources, XP, unlocks, outputs, and sinks
* each skill can support another system
* gathering has rare finds
* refining improves resource value
* crafting creates useful items, not only filler
* skill screens show next unlocks

Audit question:

Can skilling be a main playstyle, or is it secondary filler?

## Economy

Potential ideas:

* shops with limited identity and selective stock
* resources with real use cases
* crafted items with sinks
* bank support for skilling/crafting
* town request board
* price/value differences by item category
* NPC service unlocks
* repair, upgrade, or consumable sinks

Audit question:

Do resources move through meaningful loops, or do they just accumulate?

## Banking / Inventory

Potential ideas:

* quick deposit
* item stacking clarity
* bank tabs
* search/filter
* sort
* favorites
* crafting-from-bank if appropriate
* equipment/loadout support
* tooltips and examine text

Audit question:

Does storage reduce friction without removing meaningful planning?

## Quests / Activities

Potential ideas:

* short original town stories
* profession-specific tasks
* multi-step resource requests
* NPC service unlocks
* area unlocks
* recurring but non-FOMO town requests
* memorable rewards
* original Hearthvale lore hooks

Audit question:

Do quests teach systems and unlock options, or are they isolated errands?

## Rarity / Scarcity / Achievement Weight

Potential ideas:

* rare gathering finds
* rare drops
* collection log
* unique cosmetics
* visible drop celebration
* milestone announcements
* scarce resources in specific areas
* risk/reward zones
* original achievement titles

Audit question:

Does the player feel moments of luck, pride, and long-term achievement?

## Combat

Potential ideas:

* simple readable combat
* clear enemy identity
* gear choice
* food/potion support
* risk/reward drops
* attack/hit feedback
* enemy-specific loot
* combat not crowding out skilling

Audit question:

Is combat sticky without becoming the only meaningful activity?

## Graphics

Potential ideas:

* consistent tilesets
* readable sprites
* stronger silhouettes
* coherent palette
* improved environment identity
* item icon pass
* UI skin pass
* animation polish for common actions
* particles for hits, gathering, crafting, level-ups, and rare drops

Audit question:

Do visuals make repeated actions satisfying and readable?

## Audio

Potential ideas:

* area ambience
* gathering sounds
* crafting sounds
* combat sounds
* shop/bank UI sounds
* level-up cue
* rare-drop cue
* music loops
* volume/mute controls

Audit question:

Does audio reinforce the grind and make actions feel rewarding?

## Accessibility / Low Friction

Potential ideas:

* text scale
* clear keybinds
* remappable controls if feasible
* readable contrast
* input buffering
* clear blocked-action messages
* tooltips
* consistent interaction prompts

Audit question:

Can the player play for long sessions comfortably?

---

# Final Reminder For Future Codex Runs

Do not fix anything during this meta-audit.

The deliverable is a report that improves the audit prompt and identifies safer, evidence-backed ways to make Hearthvale a better original classic grindable RPG.

Every claim about the repo must be supported by concise evidence or labeled `manual verification needed`.

Every project improvement idea must be small, testable, incremental, and Hearthvale-original.
