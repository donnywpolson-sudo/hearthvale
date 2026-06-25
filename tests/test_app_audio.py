from __future__ import annotations

from pathlib import Path

from game.engine import app as app_module
from game.world.time import GameTime


class FakeHud:
    def __init__(self) -> None:
        self.audio_states: list[bool] = []
        self.volume_states: list[float] = []
        self.calls: list[str] = []

    def set_audio_enabled(self, enabled: bool) -> None:
        self.audio_states.append(enabled)

    def set_ambient_volume(self, volume: float) -> None:
        self.volume_states.append(volume)

    def close_bank(self) -> None:
        self.calls.append("close_bank")

    def open_shop(self) -> None:
        self.calls.append("open_shop")


class FakeSound:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.loop: bool | None = None
        self.volume: float | None = None

    def setLoop(self, enabled: bool) -> None:
        self.loop = enabled

    def setVolume(self, volume: float) -> None:
        self.volume = volume

    def play(self) -> None:
        self.calls.append("play")

    def stop(self) -> None:
        self.calls.append("stop")


class FakeLoader:
    def __init__(self, sound: FakeSound) -> None:
        self.sound = sound
        self.paths: list[str] = []

    def loadSfx(self, path: str) -> FakeSound:
        self.paths.append(path)
        return self.sound


class FakeApp:
    def __init__(
        self,
        *,
        audio_enabled: bool = True,
        game_time: GameTime | None = None,
        ambient_sound: FakeSound | None = None,
        ambient_sound_path: Path | None = None,
    ) -> None:
        self.audio_enabled = audio_enabled
        self.ambient_volume = app_module.DEFAULT_AMBIENT_VOLUME
        self.hud = FakeHud()
        self.calls: list[str] = []
        self.feedback: list[str] = []
        self.game_time = game_time or GameTime()
        self._ambient_sound = ambient_sound
        self._ambient_sound_path = ambient_sound_path
        self.loader = FakeLoader(ambient_sound or FakeSound())

    def enableAllAudio(self) -> None:
        self.calls.append("enable")

    def disableAllAudio(self) -> None:
        self.calls.append("disable")

    def _update_hud(self) -> None:
        self.calls.append("hud")

    def set_feedback(self, message: str) -> None:
        self.feedback.append(message)

    def _load_ambient_sound(self):
        return app_module.GameApp._load_ambient_sound(self)

    def _sync_audio_playback(self) -> None:
        app_module.GameApp._sync_audio_playback(self)


def test_toggle_audio_flips_runtime_state_and_syncs_hud_and_sound() -> None:
    sound = FakeSound()
    fake_app = FakeApp(ambient_sound=sound)

    app_module.GameApp.toggle_audio(fake_app)
    app_module.GameApp.toggle_audio(fake_app)

    assert fake_app.audio_enabled is True
    assert fake_app.calls == ["disable", "enable"]
    assert fake_app.hud.audio_states == [False, True]
    assert sound.calls == ["stop", "play"]


def test_audio_playback_loads_ambient_sound_on_demand() -> None:
    sound = FakeSound()
    fake_app = FakeApp(audio_enabled=True, ambient_sound=None, ambient_sound_path=Path("ambient.wav"))
    fake_app.ambient_volume = 0.70
    fake_app.loader = FakeLoader(sound)

    app_module.GameApp._sync_audio_playback(fake_app)

    assert fake_app.loader.paths == ["ambient.wav"]
    assert fake_app._ambient_sound is sound
    assert sound.loop is True
    assert sound.volume == 0.70
    assert sound.calls == ["play"]


def test_ambient_volume_cycle_updates_loaded_sound_and_hud() -> None:
    sound = FakeSound()
    fake_app = FakeApp(ambient_sound=sound)

    app_module.GameApp.cycle_ambient_volume(fake_app)

    assert fake_app.ambient_volume == app_module.AMBIENT_VOLUME_LEVELS[2]
    assert fake_app.hud.volume_states == [app_module.AMBIENT_VOLUME_LEVELS[2]]
    assert sound.volume == app_module.AMBIENT_VOLUME_LEVELS[2]
    assert fake_app.feedback == ["Ambient volume 50%"]


def test_shop_opening_is_blocked_after_dark() -> None:
    fake_app = FakeApp(game_time=GameTime(day=1, minute=22 * 60))

    app_module.GameApp.open_shop(fake_app)

    assert fake_app.hud.calls == []
    assert fake_app.calls == []
    assert fake_app.feedback == ["The shop is closed after dark."]


def test_shop_opening_still_works_during_daylight() -> None:
    fake_app = FakeApp(game_time=GameTime(day=1, minute=12 * 60))

    app_module.GameApp.open_shop(fake_app)

    assert fake_app.hud.calls == ["close_bank", "open_shop"]
    assert fake_app.calls == ["hud"]
    assert fake_app.feedback == ["Shop opened"]
