from __future__ import annotations

from dataclasses import dataclass

MINUTES_PER_DAY = 24 * 60
FIXED_DAY = 1
FIXED_MINUTE = 12 * 60


@dataclass
class GameTime:
    day: int = FIXED_DAY
    minute: float = float(FIXED_MINUTE)

    def update(self, _dt: float) -> None:
        self.day = FIXED_DAY
        self.minute = float(FIXED_MINUTE)

    def display(self) -> str:
        total = int(self.minute) % MINUTES_PER_DAY
        hour = total // 60
        minute = total % 60
        return f"Day {self.day} {hour:02d}:{minute:02d}"

    def to_dict(self) -> dict[str, int | float]:
        return {"day": FIXED_DAY, "minute": float(FIXED_MINUTE)}

    def load_dict(self, _data: dict[str, int | float]) -> None:
        self.day = FIXED_DAY
        self.minute = float(FIXED_MINUTE)
