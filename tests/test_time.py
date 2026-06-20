from __future__ import annotations

from game.world.time import FIXED_DAY, FIXED_MINUTE, GameTime


def test_game_time_stays_fixed_at_noon() -> None:
    game_time = GameTime()

    game_time.update(999.0)

    assert game_time.display() == "Day 1 12:00"
    assert game_time.to_dict() == {"day": FIXED_DAY, "minute": float(FIXED_MINUTE)}


def test_loaded_night_time_resets_to_noon() -> None:
    game_time = GameTime(day=5, minute=23 * 60)

    game_time.load_dict({"day": 9, "minute": 2 * 60})

    assert game_time.display() == "Day 1 12:00"
