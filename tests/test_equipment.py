from __future__ import annotations

from game.systems.equipment import Equipment
from game.systems.inventory import Inventory
from game.systems.skills import Skills, skill_xp_thresholds


def test_equipment_requires_combat_level() -> None:
    inventory = Inventory({"iron_sword": 1})
    skills = Skills(_skills())
    equipment = Equipment(_items(), inventory, skills)

    blocked = equipment.equip("iron_sword")

    assert not blocked.success
    assert blocked.feedback == "You need attack level 15 to wield Iron sword"
    assert inventory.to_dict() == {"iron_sword": 1}
    assert equipment.to_dict() == {}

    skills.add_xp("attack", skill_xp_thresholds()["15"])
    equipped = equipment.equip("iron_sword")

    assert equipped.success
    assert inventory.to_dict() == {}
    assert equipment.to_dict() == {"weapon": "iron_sword"}


def test_equipping_replaces_and_unequips_items() -> None:
    inventory = Inventory({"bronze_sword": 1, "iron_sword": 1})
    skills = Skills(_skills())
    skills.add_xp("attack", skill_xp_thresholds()["15"])
    equipment = Equipment(_items(), inventory, skills)

    assert equipment.equip("bronze_sword").success
    assert equipment.equip("iron_sword").success

    assert equipment.to_dict() == {"weapon": "iron_sword"}
    assert inventory.to_dict() == {"bronze_sword": 1}

    assert equipment.unequip("weapon").success
    assert equipment.to_dict() == {}
    assert inventory.to_dict() == {"bronze_sword": 1, "iron_sword": 1}


def test_equipment_requires_ranged_and_magic_levels() -> None:
    inventory = Inventory({"training_bow": 1, "training_staff": 1})
    skills = Skills(_skills())
    equipment = Equipment(_items(), inventory, skills)

    blocked_bow = equipment.equip("training_bow")
    blocked_staff = equipment.equip("training_staff")

    assert blocked_bow.feedback == "You need ranged level 5 to wield Training bow"
    assert blocked_staff.feedback == "You need magic level 5 to wield Training staff"

    skills.add_xp("ranged", skill_xp_thresholds()["5"])
    skills.add_xp("magic", skill_xp_thresholds()["5"])

    assert equipment.equip("training_bow").success
    assert equipment.equip("training_staff").success
    assert equipment.to_dict() == {"weapon": "training_staff"}
    assert inventory.to_dict() == {"training_bow": 1}


def test_unequip_requires_open_inventory_slot_for_non_stackable_item() -> None:
    inventory = Inventory({"iron_sword": 28})
    skills = Skills(_skills())
    equipment = Equipment(_items(), inventory, skills, {"weapon": "bronze_sword"})

    result = equipment.unequip("weapon")

    assert not result.success
    assert result.feedback == "Inventory is full"
    assert equipment.to_dict() == {"weapon": "bronze_sword"}
    assert inventory.to_dict() == {"iron_sword": 28}


def _skills() -> dict[str, dict[str, object]]:
    thresholds = skill_xp_thresholds()
    return {
        "attack": {
            "display_name": "attack",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "defence": {
            "display_name": "defence",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "ranged": {
            "display_name": "ranged",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "magic": {
            "display_name": "magic",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
    }


def _items() -> dict[str, dict[str, object]]:
    return {
        "bronze_sword": {
            "name": "Bronze sword",
            "category": "weapon",
            "sell_price": 12,
            "stackable": False,
            "equip_slot": "weapon",
            "required_skills": {"attack": 1},
        },
        "iron_sword": {
            "name": "Iron sword",
            "category": "weapon",
            "sell_price": 35,
            "stackable": False,
            "equip_slot": "weapon",
            "required_skills": {"attack": 15},
        },
        "training_bow": {
            "name": "Training bow",
            "category": "weapon",
            "sell_price": 10,
            "stackable": False,
            "equip_slot": "weapon",
            "required_skills": {"ranged": 5},
        },
        "training_staff": {
            "name": "Training staff",
            "category": "weapon",
            "sell_price": 10,
            "stackable": False,
            "equip_slot": "weapon",
            "required_skills": {"magic": 5},
        },
    }
