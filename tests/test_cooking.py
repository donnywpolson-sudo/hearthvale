from __future__ import annotations

from game.systems.cooking import CookingSystem
from game.systems.inventory import Inventory
from game.systems.skills import Skills, osrs_xp_thresholds


class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def test_cooking_completes_after_timer_and_grants_rewards() -> None:
    clock = FakeClock()
    inventory = Inventory({"raw_shrimp": 1})
    skills = Skills(_skills())
    cooking = CookingSystem(_items(), inventory, skills, time_provider=clock)

    started = cooking.start_cooking("raw_shrimp")

    assert started.success
    assert started.pending
    assert started.feedback == "Cooking Raw shrimp... 1.8s"
    assert inventory.count("raw_shrimp") == 1
    assert inventory.count("cooked_shrimp") == 0
    assert cooking.update() is None

    clock.now += 1.8
    completed = cooking.update()

    assert completed is not None
    assert completed.success
    assert inventory.count("raw_shrimp") == 0
    assert inventory.count("cooked_shrimp") == 1
    assert skills.xp("cooking") == 30
    assert completed.feedback == "Cooked Raw shrimp: +1 Cooked shrimp, +30 Cooking XP"


def test_too_low_cooking_level_blocks_recipe() -> None:
    inventory = Inventory({"raw_trout": 1})
    skills = Skills(_skills())
    cooking = CookingSystem(_items(), inventory, skills)

    result = cooking.start_cooking("raw_trout")

    assert not result.success
    assert result.feedback == "You need Cooking level 15"
    assert inventory.to_dict() == {"raw_trout": 1}
    assert skills.xp("cooking") == 0


def test_higher_cooking_level_reduces_duration() -> None:
    inventory = Inventory({"raw_shrimp": 1})
    skills = Skills(_skills())
    cooking = CookingSystem(_items(), inventory, skills)
    recipe = cooking.recipes["raw_shrimp"]

    level_one_duration = cooking.cook_duration(recipe)
    skills.add_xp("cooking", int(osrs_xp_thresholds()["6"]))
    level_six_duration = cooking.cook_duration(recipe)

    assert level_one_duration == 1.8
    assert level_six_duration == 0.9


def test_cooking_completion_requires_raw_item_still_available() -> None:
    clock = FakeClock()
    inventory = Inventory({"raw_shrimp": 1})
    skills = Skills(_skills())
    cooking = CookingSystem(_items(), inventory, skills, time_provider=clock)

    started = cooking.start_cooking("raw_shrimp")
    inventory.remove("raw_shrimp", 1)
    clock.now += started.duration
    completed = cooking.update()

    assert completed is not None
    assert not completed.success
    assert completed.feedback == "No Raw shrimp to cook"
    assert inventory.count("cooked_shrimp") == 0
    assert skills.xp("cooking") == 0


def test_pending_cooking_can_be_cancelled() -> None:
    clock = FakeClock()
    inventory = Inventory({"raw_shrimp": 1})
    skills = Skills(_skills())
    cooking = CookingSystem(_items(), inventory, skills, time_provider=clock)

    cooking.start_cooking("raw_shrimp")
    assert cooking.cancel_pending()
    clock.now += 1.8

    assert cooking.update() is None
    assert inventory.to_dict() == {"raw_shrimp": 1}
    assert skills.xp("cooking") == 0


def _items() -> dict[str, dict[str, object]]:
    return {
        "raw_shrimp": {
            "name": "Raw shrimp",
            "category": "fish",
            "sell_price": 4,
            "cook_result": "cooked_shrimp",
            "cooking_required_level": 1,
            "cooking_xp": 30,
            "base_cook_seconds": 1.8,
        },
        "cooked_shrimp": {"name": "Cooked shrimp", "category": "fish", "sell_price": 7},
        "raw_trout": {
            "name": "Raw trout",
            "category": "fish",
            "sell_price": 7,
            "cook_result": "cooked_trout",
            "cooking_required_level": 15,
            "cooking_xp": 70,
            "base_cook_seconds": 2.0,
        },
        "cooked_trout": {"name": "Cooked trout", "category": "fish", "sell_price": 12},
    }


def _skills() -> dict[str, dict[str, object]]:
    return {
        "cooking": {
            "display_name": "Cooking",
            "starting_level": 1,
            "xp_thresholds": osrs_xp_thresholds(),
        }
    }
