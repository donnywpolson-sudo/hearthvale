from __future__ import annotations

import unittest

from game.systems.inventory import Inventory


class InventoryTests(unittest.TestCase):
    def test_add_remove_count(self) -> None:
        inventory = Inventory()
        inventory.add("logs", 3)
        inventory.add("logs", 2)

        self.assertEqual(inventory.count("logs"), 5)
        self.assertEqual(inventory.remove("logs", 2), 2)
        self.assertEqual(inventory.count("logs"), 3)
        self.assertEqual(inventory.remove("logs", 10), 3)
        self.assertEqual(inventory.count("logs"), 0)

    def test_slot_count_expands_non_stackable_gear_but_stacks_resources(self) -> None:
        items = {
            "logs": {"category": "wood"},
            "bronze_sword": {"category": "weapon", "equip_slot": "weapon"},
            "bronze_axe": {"category": "tool", "tool_for": "woodcutting"},
        }
        inventory = Inventory({"logs": 25, "bronze_sword": 2, "bronze_axe": 1})

        self.assertEqual(inventory.slot_count(items), 4)
        self.assertTrue(inventory.can_add("logs", 100, item_definitions=items, slot_limit=4))
        self.assertFalse(inventory.can_add("bronze_sword", 1, item_definitions=items, slot_limit=4))


if __name__ == "__main__":
    unittest.main()
