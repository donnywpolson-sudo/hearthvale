from __future__ import annotations

from game import settings
from game.world.time import GameTime


def test_game_time_advances_and_rolls_over_days(monkeypatch) -> None:
    monkeypatch.setattr(settings, "GAME_MINUTES_PER_REAL_SECOND", 60.0)
    game_time = GameTime(day=2, minute=23 * 60 + 30)

    game_time.update(1.0)

    assert game_time.display() == "Day 3 00:30"
    assert game_time.to_dict() == {"day": 3, "minute": 30.0}


def test_loaded_time_preserves_saved_values() -> None:
    game_time = GameTime(day=5, minute=23 * 60)

    game_time.load_dict({"day": 9, "minute": 2 * 60})

    assert game_time.display() == "Day 9 02:00"
    assert game_time.to_dict() == {"day": 9, "minute": 120.0}
