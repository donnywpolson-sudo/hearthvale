# Snapshot
- Stack: Python 3.11, Panda3D, pytest
- Entry point: `python -m game.main`
- Focused tests: `python -B -m pytest -p no:cacheprovider tests/test_hud.py tests/test_app_audio.py tests/test_assets_runtime.py tests/test_time.py tests/test_save.py`
- Current status: the settings menu now includes a session-only ambient volume control that updates the loaded loop immediately.

# Changes
- Updated `game/ui/hud.py` to add an ambient volume button and label sync in the existing settings menu.
- Updated `game/engine/app.py` to cycle ambient volume levels, apply them to loaded audio, and surface the current value in the HUD.
- Expanded `tests/test_hud.py` and `tests/test_app_audio.py` to cover the new control and volume propagation.
- Updated `README.md` to mention ambient volume in the settings controls list.

# Checks
- `python -B -m game.tools.validate_data`: passed
- `python -B -m pytest -p no:cacheprovider tests/test_hud.py tests/test_app_audio.py tests/test_assets_runtime.py tests/test_time.py tests/test_save.py`: passed (`100 passed`)
- `python -c "from game.engine.app import GameApp; app = GameApp(); print('startup ok'); app.destroy()"`: passed (`startup ok`); non-fatal `SetForegroundWindow() failed!` warning from Panda3D on Windows

# Remaining Work
- None required for this batch.

# Next Prompt
Continue from `CODEX_HANDOFF.md`.

Next selected scope: add one small UI feedback toggle, such as a switch for hover text or XP toasts.

Rules:
- Do not change gameplay, saves, login, or map layout.
- Do not remove the procedural fallback, the asset hooks, or the existing audio controls.
- Keep the batch limited to HUD/app wiring and the smallest doc/test updates needed.
- Keep the control optional or session-only unless persistence is clearly needed.
- Do not copy protected content, preserve user work, and do not commit.
- Verify with `python -B -m pytest -p no:cacheprovider tests/test_hud.py tests/test_app_audio.py tests/test_assets_runtime.py tests/test_time.py tests/test_save.py` and `python -B -m game.tools.validate_data`.
- Do a short startup smoke with `python -c "from game.engine.app import GameApp; app = GameApp(); print('startup ok'); app.destroy()"` if practical.

Task:
- Add one new UI feedback control with an observable runtime effect.
- Wire it through `game/ui/hud.py` and `game/engine/app.py` using the existing settings pattern.
- Update only the smallest tests and README text needed to document the control.

Stop when:
- The control changes runtime behavior, focused tests pass, and no unrelated files changed.
