from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import time
from typing import Any


COMBAT_TRAINING_STYLES = ("attack", "strength", "defence", "ranged", "magic")
DEFAULT_COMBAT_TRAINING_STYLE = "attack"


@dataclass(frozen=True)
class CombatTrainingResult:
    success: bool
    feedback: str
    skill_id: str
    xp_awarded: int = 0
    remaining_seconds: float = 0.0


class CombatTraining:
    def __init__(
        self,
        skills: Any,
        *,
        style: str = DEFAULT_COMBAT_TRAINING_STYLE,
        xp_reward: int = 20,
        cooldown_seconds: float = 1.2,
        time_provider: Callable[[], float] | None = None,
    ) -> None:
        self.skills = skills
        self.style = normalize_combat_training_style(style)
        self.xp_reward = xp_reward
        self.cooldown_seconds = cooldown_seconds
        self.time_provider = time_provider or time.monotonic
        self.next_train_at = 0.0

    def set_style(self, style: str) -> str:
        self.style = normalize_combat_training_style(style)
        return self.style

    def train(self) -> CombatTrainingResult:
        return CombatTrainingResult(
            False,
            "Combat practice is unavailable",
            self.style,
        )


def normalize_combat_training_style(style: str) -> str:
    if style == "defense":
        return "defence"
    return style if style in COMBAT_TRAINING_STYLES else DEFAULT_COMBAT_TRAINING_STYLE


def _skill_label(skills: Any, skill_id: str) -> str:
    if hasattr(skills, "display_name"):
        return str(skills.display_name(skill_id))
    definition = getattr(skills, "definitions", {}).get(skill_id, {})
    return str(definition.get("display_name") or skill_id.replace("_", " ").title())
