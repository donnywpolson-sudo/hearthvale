from __future__ import annotations

from game.systems.combat_training import CombatTraining
from game.systems.skills import Skills, skill_xp_thresholds


def test_removed_combat_practice_does_not_award_xp() -> None:
    skills = Skills(_skills())
    training = CombatTraining(skills)

    result = training.train()

    assert result.success is False
    assert result.feedback == "Combat practice is unavailable"
    assert result.xp_awarded == 0
    assert skills.xp("attack") == 0
    assert skills.xp("strength") == 0
    assert skills.xp("defence") == 0


def test_training_style_selection_does_not_award_xp() -> None:
    skills = Skills(_skills())
    training = CombatTraining(skills)

    training.set_style("strength")
    result = training.train()

    assert result.skill_id == "strength"
    assert result.feedback == "Combat practice is unavailable"
    assert skills.xp("attack") == 0
    assert skills.xp("strength") == 0
    assert skills.xp("defence") == 0


def test_training_style_accepts_defense_alias() -> None:
    skills = Skills(_skills())
    training = CombatTraining(skills)

    training.set_style("defense")

    assert training.style == "defence"


def test_training_style_accepts_ranged_and_magic() -> None:
    skills = Skills(_skills())
    training = CombatTraining(skills)

    training.set_style("ranged")
    assert training.style == "ranged"

    training.set_style("magic")
    assert training.style == "magic"


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


def _skills() -> dict[str, dict[str, object]]:
    thresholds = skill_xp_thresholds()
    return {
        "attack": {"display_name": "Attack", "starting_level": 1, "xp_thresholds": thresholds},
        "strength": {"display_name": "Strength", "starting_level": 1, "xp_thresholds": thresholds},
        "defence": {"display_name": "Defence", "starting_level": 1, "xp_thresholds": thresholds},
        "ranged": {"display_name": "Ranged", "starting_level": 1, "xp_thresholds": thresholds},
        "magic": {"display_name": "Magic", "starting_level": 1, "xp_thresholds": thresholds},
    }
