from __future__ import annotations

from dataclasses import dataclass

from game import settings

MINUTES_PER_DAY = 24 * 60
START_DAY = settings.START_DAY
START_MINUTE = settings.START_MINUTE
FIXED_DAY = START_DAY
FIXED_MINUTE = START_MINUTE
SHOP_OPEN_HOUR = 7
SHOP_CLOSE_HOUR = 20


@dataclass
class GameTime:
    day: int = START_DAY
    minute: float = float(START_MINUTE)

    def hour(self) -> int:
        return int(self.minute) % MINUTES_PER_DAY // 60

    def is_shop_open(self) -> bool:
        return SHOP_OPEN_HOUR <= self.hour() < SHOP_CLOSE_HOUR

    def update(self, dt: float) -> None:
        if dt <= 0:
            return
        minutes_per_second = float(settings.GAME_MINUTES_PER_REAL_SECOND)
        if minutes_per_second <= 0:
            return

        self.minute += dt * minutes_per_second
        while self.minute >= MINUTES_PER_DAY:
            self.minute -= MINUTES_PER_DAY
            self.day += 1

    def display(self) -> str:
        total = int(self.minute) % MINUTES_PER_DAY
        hour = total // 60
        minute = total % 60
        return f"Day {self.day} {hour:02d}:{minute:02d}"

    def to_dict(self) -> dict[str, int | float]:
        return {"day": self.day, "minute": float(self.minute)}

    def load_dict(self, data: dict[str, int | float]) -> None:
        if not isinstance(data, dict):
            self.day = START_DAY
            self.minute = float(START_MINUTE)
            return

        try:
            self.day = max(1, int(data.get("day", START_DAY)))
        except (TypeError, ValueError):
            self.day = START_DAY

        try:
            self.minute = float(data.get("minute", START_MINUTE))
        except (TypeError, ValueError):
            self.minute = float(START_MINUTE)

        if self.minute < 0:
            self.day = START_DAY
            self.minute = float(START_MINUTE)
            return

        while self.minute >= MINUTES_PER_DAY:
            self.minute -= MINUTES_PER_DAY
            self.day += 1
