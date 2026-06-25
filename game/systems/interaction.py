from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from game import settings
from game.assets.runtime import apply_surface_texture, load_animation_clip_data
from game.entities.player import Player, heading_for_delta
from game.systems.combat import CombatSystem
from game.systems.cooking import CookingSystem
from game.systems.gathering import GatheringSystem, REQUIRED_TOOLS
from game.systems.inventory import Inventory
from game.systems.shop import Shop
from game.systems.smithing import SmithingRecipe, SmithingSystem
from game.systems.skills import Skills
from game.world.grid import Tile
from game.world.map import WorldMap
from game.world.objects import WorldObject, make_box
from game.world.pathfinding import find_path


@dataclass(frozen=True)
class InteractionAction:
    action_id: str
    label: str


class InteractionManager:
    def __init__(
        self,
        world_map: WorldMap,
        player: Player,
        inventory: Inventory,
        skills: Skills,
        shop: Shop,
        add_coins: Callable[[int], None],
        feedback: Callable[[str], None],
        gathering: GatheringSystem | None = None,
        cooking: CookingSystem | None = None,
        combat: CombatSystem | None = None,
        smithing: SmithingSystem | None = None,
        open_bank: Callable[[], None] | None = None,
        open_shop: Callable[[], None] | None = None,
        talk_to_npc: Callable[[WorldObject], None] | None = None,
        on_cooking_result: Callable[[object], None] | None = None,
        on_smithing_result: Callable[[object], None] | None = None,
        on_smithing_choice: Callable[[str, list[SmithingRecipe]], None] | None = None,
        on_quantity_choice: Callable[[str, str, int, Callable[[int], None]], None] | None = None,
        on_combat_result: Callable[[object], None] | None = None,
        animator: object | None = None,
    ) -> None:
        self.world_map = world_map
        self.player = player
        self.inventory = inventory
        self.skills = skills
        self.shop = shop
        self.add_coins = add_coins
        self.feedback = feedback
        self.gathering = gathering
        self.cooking = cooking
        self.combat = combat
        self.smithing = smithing
        self.open_bank = open_bank
        self.open_shop = open_shop
        self.talk_to_npc = talk_to_npc
        self.on_cooking_result = on_cooking_result
        self.on_smithing_result = on_smithing_result
        self.on_smithing_choice = on_smithing_choice
        self.on_quantity_choice = on_quantity_choice
        self.on_combat_result = on_combat_result
        self.animator = animator
        self._mob_response_clip = load_animation_clip_data("npc_mob_combat_response")
        self.pending_object_id: str | None = None
        self.pending_action_id: str | None = None
        self.selected_item_id: str | None = None
        self.selected_item_slot: tuple[str, int] | None = None
        self.pending_station_object_id: str | None = None

    def move_to_tile(self, tile: Tile) -> None:
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        self._cancel_smithing()
        self._stop_action_animation()
        path = find_path(self.world_map.grid, self.player.tile, tile, self.world_map.blocked_tiles())
        if path is None:
            self.feedback("No path")
            return
        self.pending_object_id = None
        self.pending_action_id = None
        self.player.set_path(path)

    def walk_to_target(self, obj: WorldObject) -> None:
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        self._cancel_smithing()
        self._stop_action_animation()
        path = self._path_for_walk_action(obj)
        if path is None:
            self.feedback("No path")
            return
        self.pending_object_id = None
        self.pending_action_id = None
        self.player.set_path(path)
        self.feedback("Walking here")

    def interact_with(self, obj: WorldObject | None) -> None:
        actions = self.get_actions(obj)
        if obj is not None and actions:
            self.perform_action(actions[0].action_id, obj)
            return
        self._interact_default(obj)

    def get_actions(self, obj: WorldObject | None) -> list[InteractionAction]:
        if obj is None:
            return []
        actions: list[InteractionAction] = []
        if obj.scenery:
            actions.append(InteractionAction("walk", "Walk here"))
        elif self._is_gatherable(obj):
            node = self.world_map.resource_node_for_object(obj)
            skill_id = node.skill_id if node is not None else obj.skill_id
            label = {"woodcutting": "Chop down", "mining": "Mine", "fishing": "Fish"}.get(skill_id, "Gather")
            actions.append(InteractionAction("gather", f"{label} {obj.display_name or obj.kind}"))
        elif obj.kind == "cooking_range":
            actions.append(InteractionAction("cook", "Cook"))
        elif obj.kind == "furnace":
            actions.append(InteractionAction("smelt", "Smelt"))
        elif obj.kind == "anvil":
            actions.append(InteractionAction("smith", "Smith"))
        elif obj.kind == "bank":
            actions.append(InteractionAction("bank", "Bank"))
        elif obj.kind == "shop":
            actions.append(InteractionAction("trade", "Trade"))
        elif obj.kind == "npc":
            actions.append(InteractionAction("talk", f"Talk-to {obj.display_name or 'NPC'}"))
        elif self._is_combatable(obj):
            actions.append(InteractionAction("attack", f"Attack {obj.display_name or obj.kind}"))
        elif obj.kind == "ground_item":
            actions.append(InteractionAction("take", f"Take {self._item_name(obj.item_id)}"))
        actions.append(InteractionAction("examine", f"Examine {obj.display_name or obj.kind}"))
        actions.append(InteractionAction("cancel", "Cancel"))
        return actions

    def perform_action(self, action_id: str, obj: WorldObject | None) -> None:
        if obj is None:
            return
        if action_id == "cancel":
            self._cancel_gathering()
            self._cancel_cooking()
            self._cancel_combat()
            self._cancel_smithing()
            self._stop_action_animation()
            return
        if action_id == "examine":
            self.feedback(self._examine_text(obj))
            return
        if action_id == "walk":
            self.walk_to_target(obj)
            return
        self._interact_default(obj, action_id)

    def start_smithing_recipe(self, action_type: str, recipe_id: str) -> None:
        if self.smithing is None:
            self.feedback("Select ore to smelt" if action_type == "smelting" else "Select bars to smith")
            return
        recipe = self.smithing.recipe_by_id(action_type, recipe_id)
        if recipe is None:
            self.feedback("Recipe unavailable")
            return
        self._show_or_start_smithing_recipe(action_type, recipe)

    def _interact_default(self, obj: WorldObject | None, action_id: str | None = None) -> None:
        if obj is None:
            self._cancel_gathering()
            self._cancel_cooking()
            self._cancel_combat()
            self._cancel_smithing()
            self.feedback("Nothing to interact with")
            return
        if obj.scenery:
            self.walk_to_target(obj)
            return
        if self._is_gatherable(obj):
            if self._in_range(obj.tile):
                self._perform(obj, action_id)
                return
            self._cancel_gathering()
            self._cancel_cooking()
            self._cancel_combat()
            self._cancel_smithing()
            path = self._path_to_adjacent(obj.tile)
            if path is None:
                self.feedback("No path")
                return
            self.pending_object_id = obj.object_id
            self.pending_action_id = action_id
            self.player.set_path(path)
            self.feedback(f"Walking to {_object_label(obj)}")
            return
        if self._is_combatable(obj) or obj.kind == "ground_item":
            if self._in_range_for(obj):
                self._perform(obj, action_id)
                return
            self._cancel_gathering()
            self._cancel_cooking()
            self._cancel_combat()
            self._cancel_smithing()
            path = self._path_to_object(obj)
            if path is None:
                self.feedback("No path")
                return
            self.pending_object_id = obj.object_id
            self.pending_action_id = action_id
            self.player.set_path(path)
            self.feedback(f"Walking to {_object_label(obj)}")
            return
        self._cancel_gathering()
        self._cancel_combat()
        if obj.kind != "cooking_range":
            self._cancel_cooking()
        if obj.kind not in {"furnace", "anvil"}:
            self._cancel_smithing()
        if self._in_range_for(obj):
            self._perform(obj, action_id)
            return

        path = self._path_to_adjacent(obj.tile)
        if path is None:
            self.feedback("No path")
            return
        self.pending_object_id = obj.object_id
        self.pending_action_id = action_id
        self.player.set_path(path)
        self.feedback(f"Walking to {_object_label(obj)}")

    def select_inventory_item(self, item_id: str, occurrence_index: int = 0) -> None:
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        self._cancel_smithing()
        if self.inventory.count(item_id) <= 0:
            self.selected_item_id = None
            self.selected_item_slot = None
            self.feedback(f"No {self._item_name(item_id)}")
            return
        self.selected_item_id = item_id
        self.selected_item_slot = (item_id, max(0, occurrence_index))
        self.feedback(f"Selected item: {self._item_name(item_id)}")

    def update(self) -> None:
        if self.gathering is not None:
            if self._gathering_target_invalid():
                self._cancel_gathering()
                self.feedback("Gathering stopped")
            else:
                result = self.gathering.update()
                if result is not None:
                    self.world_map.apply_resource_states(self.gathering.states)
                    target = self.world_map.get_object(result.node_id) if result.node_id is not None else None
                    if result.pending:
                        self._start_action_animation("gathering", target, result.skill_id)
                    else:
                        self._stop_action_animation()
                    self.feedback(result.feedback)

        if self.cooking is not None:
            result = self.cooking.update()
            if result is not None:
                station = self.world_map.get_object(self.pending_station_object_id) if self.pending_station_object_id else None
                if result.pending:
                    self._start_action_animation("cooking", station)
                else:
                    self._stop_action_animation()
                if (
                    result.raw_item_id is not None
                    and result.raw_item_id == self.selected_item_id
                    and self.inventory.count(result.raw_item_id) <= 0
                ):
                    self.selected_item_id = None
                    self.selected_item_slot = None
                self.feedback(result.feedback)
                if self.on_cooking_result is not None:
                    self.on_cooking_result(result)

        if self.smithing is not None:
            result = self.smithing.update()
            if result is not None:
                station = self.world_map.get_object(self.pending_station_object_id) if self.pending_station_object_id else None
                if result.pending:
                    action_type = "smithing"
                    pending = self.smithing.pending
                    if pending is not None:
                        action_type = pending.action_type
                    self._start_action_animation(action_type, station)
                else:
                    self._stop_action_animation()
                if (
                    result.item_id is not None
                    and self.selected_item_id is not None
                    and self.inventory.count(self.selected_item_id) <= 0
                ):
                    self.selected_item_id = None
                    self.selected_item_slot = None
                self.feedback(result.feedback)
                if self.on_smithing_result is not None:
                    self.on_smithing_result(result)

        if self.combat is not None:
            result = self.combat.update()
            if result is not None:
                target = self.world_map.get_object(result.mob_id) if result.mob_id is not None else None
                if result.killed and target is not None:
                    self._animate_defeat(target)
                self.world_map.apply_mob_states(self.combat.states)
                feedback = result.feedback
                if result.killed and result.mob_id is not None:
                    mob = self.combat.mobs.get(result.mob_id)
                    if mob is not None:
                        created = self.world_map.spawn_ground_drops(mob.position, result.drops)
                        if created:
                            feedback = f"{feedback}; drops appeared"
                        self._animate_ground_drops(created)
                if result.player_damage > 0 and result.mob_id is not None:
                    self._animate_hit(self.world_map.get_object(result.mob_id), result.player_damage)
                if result.enemy_damage > 0:
                    self._animate_player_hit(result.enemy_damage)
                if result.pending and not result.player_dead and not result.killed and result.mob_id is not None:
                    self._start_action_animation(_combat_animation_id(result.combat_style), self.world_map.get_object(result.mob_id))
                else:
                    self._stop_action_animation()
                self.feedback(feedback)
                if self.on_combat_result is not None:
                    self.on_combat_result(result)

        if self.player.is_moving:
            self._stop_action_animation()
        if self.pending_object_id is None or self.player.is_moving:
            return
        obj = self._get_target(self.pending_object_id)
        self.pending_object_id = None
        if obj is None:
            return
        if self._in_range_for(obj):
            action_id = self.pending_action_id
            self.pending_action_id = None
            self._perform(obj, action_id)
        else:
            self.feedback("Too far away")

    def _perform(self, obj: WorldObject, action_id: str | None = None) -> None:
        if self._is_gatherable(obj):
            self._perform_gathering(obj)
        elif obj.kind == "cooking_range":
            self._perform_cooking(obj)
        elif obj.kind == "furnace":
            self._perform_smelting(obj)
        elif obj.kind == "anvil":
            self._perform_smithing(obj)
        elif obj.kind == "bank":
            if self.open_bank is None:
                self.feedback("Bank unavailable")
                return
            self.open_bank()
        elif obj.kind == "shop":
            if self.open_shop is None:
                self.feedback("Shop unavailable")
                return
            self.open_shop()
        elif self._is_combatable(obj):
            self._perform_combat(obj)
        elif obj.kind == "ground_item":
            self._perform_ground_item(obj)
        elif obj.kind == "npc":
            if self.talk_to_npc is None:
                self.feedback("Nothing happens")
                return
            self.talk_to_npc(obj)
        else:
            self.feedback("Nothing happens")

    def _perform_gathering(self, obj: WorldObject) -> None:
        if self.gathering is None:
            self.feedback("Nothing happens")
            return
        self._cancel_cooking()
        self._cancel_combat()
        self._cancel_smithing()
        result = self.gathering.start_gather(
            obj.object_id,
            self.player.tile,
            self.world_map.grid,
            self.world_map.blocked_tiles(),
            allow_movement=False,
        )
        self.world_map.apply_resource_states(self.gathering.states)
        if result.pending:
            self._start_action_animation("gathering", obj, result.skill_id)
        else:
            self._stop_action_animation()
        feedback = result.feedback
        if result.pending:
            node = self.world_map.resource_node_for_object(obj)
            if node is not None and node.skill_id == "fishing":
                feedback = f"{feedback}; {self._resource_detail_text(node, catch_label='catches')}"
        self.feedback(feedback)

    def _perform_cooking(self, obj: WorldObject) -> None:
        if self.cooking is None:
            self.feedback("Select a raw fish first")
            return
        self._cancel_gathering()
        self._cancel_combat()
        self._cancel_smithing()
        self.pending_station_object_id = obj.object_id
        if self._show_cooking_quantity_choice():
            return
        result = self.cooking.start_cooking(self.selected_item_id)
        if result.pending:
            self._start_action_animation("cooking", obj)
        else:
            self._stop_action_animation()
        self.feedback(result.feedback)

    def _perform_smelting(self, obj: WorldObject) -> None:
        if self.smithing is None:
            self.feedback("Select ore to smelt")
            return
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        self.pending_station_object_id = obj.object_id
        if self._show_smithing_choice("smelting"):
            return
        recipe = self.smithing.recipe_for_item("smelting", self.selected_item_id)
        if recipe is None:
            result = self.smithing.start_smelting(self.selected_item_id)
            self._stop_action_animation()
            self.feedback(result.feedback)
            return
        self._show_or_start_smithing_recipe("smelting", recipe)

    def _perform_smithing(self, obj: WorldObject) -> None:
        if self.smithing is None:
            self.feedback("Select bars to smith")
            return
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        self.pending_station_object_id = obj.object_id
        if self._show_smithing_choice("smithing"):
            return
        recipe = self.smithing.recipe_for_item("smithing", self.selected_item_id)
        if recipe is None:
            result = self.smithing.start_smithing(self.selected_item_id)
            self._stop_action_animation()
            self.feedback(result.feedback)
            return
        self._show_or_start_smithing_recipe("smithing", recipe)

    def _show_smithing_choice(self, action_type: str) -> bool:
        if self.smithing is None or self.on_smithing_choice is None:
            return False
        recipes = self.smithing.matching_recipes(action_type, self.selected_item_id)
        if len(recipes) <= 1:
            return False
        self.feedback("Choose a recipe to smelt" if action_type == "smelting" else "Choose a recipe to smith")
        self.on_smithing_choice(action_type, recipes)
        return True

    def _show_cooking_quantity_choice(self) -> bool:
        if self.cooking is None or self.on_quantity_choice is None:
            return False
        raw_item_id = self.selected_item_id
        recipe = self.cooking.recipes.get(raw_item_id or "")
        if raw_item_id is None or recipe is None or self.inventory.count(raw_item_id) <= 0:
            return False
        current_level = self.skills.level("cooking") if hasattr(self.skills, "level") else self.skills.get("cooking").level
        if current_level < recipe.required_level:
            return False
        max_quantity = self.inventory.count(raw_item_id)
        self.on_quantity_choice("cook", self._item_name(raw_item_id), max_quantity, self.start_cooking_quantity)
        return True

    def start_cooking_quantity(self, quantity: int) -> None:
        if self.cooking is None:
            self.feedback("Select a raw fish first")
            return
        self._cancel_gathering()
        self._cancel_combat()
        self._cancel_smithing()
        result = self.cooking.start_cooking(self.selected_item_id, quantity)
        station = self.world_map.get_object(self.pending_station_object_id) if self.pending_station_object_id else None
        if result.pending:
            self._start_action_animation("cooking", station)
        else:
            self._stop_action_animation()
        self.feedback(result.feedback)

    def _show_or_start_smithing_recipe(self, action_type: str, recipe: SmithingRecipe) -> None:
        if self.smithing is None:
            self.feedback("Select ore to smelt" if action_type == "smelting" else "Select bars to smith")
            return
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        max_quantity = self.smithing.max_quantity(recipe)
        if self.on_quantity_choice is not None and max_quantity > 0:
            self.on_quantity_choice(
                "smelt" if action_type == "smelting" else "smith",
                recipe.display_name,
                max_quantity,
                lambda quantity, action_type=action_type, recipe_id=recipe.recipe_id: self.start_smithing_recipe_quantity(
                    action_type,
                    recipe_id,
                    quantity,
                ),
            )
            return
        self.start_smithing_recipe_quantity(action_type, recipe.recipe_id, 1)

    def start_smithing_recipe_quantity(self, action_type: str, recipe_id: str, quantity: int) -> None:
        if self.smithing is None:
            self.feedback("Select ore to smelt" if action_type == "smelting" else "Select bars to smith")
            return
        result = self.smithing.start_recipe_by_id(action_type, recipe_id, quantity)
        station = self.world_map.get_object(self.pending_station_object_id) if self.pending_station_object_id else None
        if result.pending:
            self._start_action_animation(action_type, station)
        else:
            self._stop_action_animation()
        self.feedback(result.feedback)

    def _perform_combat(self, obj: WorldObject) -> None:
        if self.combat is None:
            self.feedback("Nothing happens")
            return
        self._cancel_gathering()
        self._cancel_cooking()
        result = self.combat.start_attack(
            obj.object_id,
            self.player.tile,
            self.world_map.grid,
            self.world_map.blocked_tiles(),
        )
        self.world_map.apply_mob_states(self.combat.states)
        if result.pending:
            self._start_action_animation(_combat_animation_id(result.combat_style), obj)
        else:
            self._stop_action_animation()
        self.feedback(result.feedback)

    def _perform_ground_item(self, obj: WorldObject) -> None:
        if not self.inventory.can_add(obj.item_id, obj.quantity, item_definitions=self.shop.item_definitions):
            self.feedback("Inventory is full")
            return
        picked_up = self.world_map.pickup_ground_item(obj.object_id)
        if picked_up is None:
            self.feedback("Nothing to pick up")
            return
        item_id, quantity = picked_up
        self.inventory.add(item_id, quantity)
        self.feedback(f"Picked up {quantity} {self._item_name(item_id)}")

    def _path_to_object(self, obj: WorldObject) -> list[Tile] | None:
        if self._is_combatable(obj):
            return self._path_to_combat_range(obj)
        if obj.kind == "ground_item" or (not obj.blocking and obj.scenery):
            blocked = self.world_map.blocked_tiles()
            if obj.scenery:
                blocked.discard(obj.tile)
            if obj.tile not in blocked:
                path = find_path(self.world_map.grid, self.player.tile, obj.tile, blocked)
                if path is not None:
                    return path
        return self._path_to_adjacent(obj.tile)

    def _path_to_combat_range(self, obj: WorldObject) -> list[Tile] | None:
        if self.combat is None or obj.object_id not in self.combat.mobs:
            return self._path_to_adjacent(obj.tile)
        attack_range = self.combat.attack_range_for_style()
        blocked = self.world_map.blocked_tiles()
        best_path: list[Tile] | None = None
        for dx in range(-attack_range, attack_range + 1):
            for dy in range(-attack_range, attack_range + 1):
                distance = abs(dx) + abs(dy)
                if distance <= 0 or distance > attack_range:
                    continue
                candidate = (obj.tile[0] + dx, obj.tile[1] + dy)
                if candidate in blocked or not self.world_map.grid.in_bounds(candidate):
                    continue
                path = find_path(self.world_map.grid, self.player.tile, candidate, blocked)
                if path is not None and (best_path is None or len(path) < len(best_path)):
                    best_path = path
        return best_path

    def _path_for_walk_action(self, obj: WorldObject) -> list[Tile] | None:
        if obj.blocking:
            return self._path_to_adjacent(obj.tile)
        blocked = self.world_map.blocked_tiles()
        blocked.discard(obj.tile)
        return find_path(self.world_map.grid, self.player.tile, obj.tile, blocked)

    def _path_to_adjacent(self, target: Tile) -> list[Tile] | None:
        blocked_tiles = getattr(self.world_map, "blocked_tiles", None)
        grid = getattr(self.world_map, "grid", None)
        if not callable(blocked_tiles) or grid is None or not hasattr(grid, "neighbors"):
            return None
        blocked = blocked_tiles()
        best_path: list[Tile] | None = None
        for candidate in grid.neighbors(target, diagonals=False):
            if candidate in blocked:
                continue
            path = find_path(grid, self.player.tile, candidate, blocked)
            if path is not None and (best_path is None or len(path) < len(best_path)):
                best_path = path
        return best_path

    def _in_range(self, tile: Tile) -> bool:
        dx = abs(self.player.tile[0] - tile[0])
        dy = abs(self.player.tile[1] - tile[1])
        return 0 < dx + dy <= settings.INTERACTION_RANGE

    def _in_range_for(self, obj: WorldObject) -> bool:
        if self._is_combatable(obj) and self.combat is not None:
            mob = self.combat.mobs.get(obj.object_id)
            return mob is not None and self.combat.can_attack_from(self.player.tile, mob)
        dx = abs(self.player.tile[0] - obj.tile[0])
        dy = abs(self.player.tile[1] - obj.tile[1])
        distance = dx + dy
        if obj.kind == "ground_item":
            return distance <= settings.INTERACTION_RANGE
        return 0 < distance <= settings.INTERACTION_RANGE

    def _is_gatherable(self, obj: WorldObject) -> bool:
        return self.gathering is not None and obj.object_id in self.gathering.nodes

    def _is_combatable(self, obj: WorldObject) -> bool:
        return self.combat is not None and obj.active and obj.object_id in self.combat.mobs

    def _get_target(self, object_id: str) -> WorldObject | None:
        get_target = getattr(self.world_map, "get_target", None)
        if callable(get_target):
            return get_target(object_id)
        return self.world_map.get_object(object_id)

    def _start_action_animation(
        self,
        action_id: str,
        obj: WorldObject | None,
        skill_id: str | None = None,
    ) -> None:
        self._stop_action_animation()
        self._face_object(obj)
        self._start_player_action(action_id, skill_id)
        if self.animator is None:
            return

        parts = getattr(self.player, "parts", {}) or {}
        player_node = getattr(self.player, "node", None)
        right_arm = parts.get("right_arm")
        tool = parts.get("tool")
        target = obj.node if obj is not None else None
        target_direction = self._direction_from_player(obj) if obj is not None else (0.0, -1.0, 0.0)

        if action_id == "gathering" and skill_id == "woodcutting":
            self._start_anim("start_swing", "action:arm", right_arm, axis="p", amplitude=44.0, speed=8.8, steps=8)
            self._start_anim("start_swing", "action:tool", tool, axis="p", amplitude=66.0, speed=8.8, phase=0.35, steps=8)
            self._start_anim("start_shake", "action:target_shake", target, amplitude=0.020, speed=13.0)
            self._start_anim("start_tilt", "action:target", target, roll=4.5, speed=9.0)
            self._start_anim("start_pulse", "action:target_pulse", target, amplitude=0.025, speed=9.0)
            self._start_anim("start_burst", "action:target_burst", target, amplitude=0.035, duration=0.24)
        elif action_id == "gathering" and skill_id == "mining":
            self._start_anim("start_swing", "action:arm", right_arm, axis="p", amplitude=50.0, speed=9.5, steps=8)
            self._start_anim("start_swing", "action:tool", tool, axis="p", amplitude=72.0, speed=9.5, phase=0.25, steps=8)
            self._start_anim("start_shake", "action:target_shake", target, amplitude=0.030, speed=16.0)
            self._start_anim("start_tilt", "action:target", target, pitch=2.5, roll=4.0, speed=11.0)
            self._start_anim("start_flash", "action:target_flash", target, color=(1.20, 1.15, 0.90, 1.0), speed=8.0)
            self._start_anim("start_impact", "action:target_impact", target, direction=target_direction, distance=0.035, duration=0.18)
            self._start_anim("start_spark", "action:target_spark", target, lift=0.08, duration=0.18)
        elif action_id == "gathering" and skill_id == "fishing":
            self._start_anim("start_tilt", "action:player_lean", player_node, pitch=2.5, roll=2.5, speed=4.2)
            self._start_anim("start_swing", "action:tool", tool, axis="r", amplitude=24.0, speed=4.8, steps=8)
            self._start_anim("start_pulse", "action:target_pulse", target, amplitude=0.08, speed=5.2)
            self._start_anim("start_rotate", "action:target_rotate", target, degrees_per_second=28.0)
            self._start_anim("start_ripple", "action:target_ripple", target, amplitude=0.12, duration=0.42)
        elif action_id == "cooking":
            self._start_anim("start_tilt", "action:player_lean", player_node, pitch=2.0, roll=1.5, speed=4.4)
            self._start_anim("start_swing", "action:arm", right_arm, axis="p", amplitude=22.0, speed=6.0, steps=8)
            self._start_anim("start_pulse", "action:range_pulse", target, amplitude=0.035, speed=5.5)
            self._start_anim("start_flash", "action:range_glow", target, color=(1.16, 0.78, 0.42, 1.0), speed=5.5)
            self._start_anim("start_burst", "action:range_burst", target, amplitude=0.04, color=(1.22, 0.74, 0.36, 1.0), duration=0.28)
        elif action_id == "smelting":
            self._start_anim("start_tilt", "action:player_lean", player_node, pitch=1.8, roll=1.5, speed=4.0)
            self._start_anim("start_pulse", "action:furnace_pulse", target, amplitude=0.045, speed=5.8)
            self._start_anim("start_flash", "action:furnace_glow", target, color=(1.25, 0.62, 0.28, 1.0), speed=6.2)
            self._start_anim("start_burst", "action:furnace_burst", target, amplitude=0.05, color=(1.30, 0.58, 0.20, 1.0), duration=0.30)
        elif action_id == "smithing":
            self._start_anim("start_swing", "action:arm", right_arm, axis="p", amplitude=52.0, speed=10.5, steps=8)
            self._start_anim("start_swing", "action:tool", tool, axis="p", amplitude=74.0, speed=10.5, phase=0.25, steps=8)
            self._start_anim("start_pulse", "action:anvil_pulse", target, amplitude=0.035, speed=10.0)
            self._start_anim("start_flash", "action:anvil_flash", target, color=(1.28, 1.15, 0.74, 1.0), speed=10.0)
            self._start_anim("start_impact", "action:anvil_impact", target, direction=target_direction, distance=0.025, duration=0.16)
            self._start_anim("start_spark", "action:anvil_spark", target, lift=0.10, duration=0.18)
        elif action_id.startswith("combat"):
            if action_id == "combat_ranged":
                self._animate_projectile(obj, "ranged")
                self._start_anim("start_swing", "action:arm", right_arm, axis="r", amplitude=26.0, speed=6.2, steps=8)
                self._start_anim("start_swing", "action:tool", tool, axis="r", amplitude=32.0, speed=6.2, phase=0.20, steps=8)
                self._start_anim("start_impact", "action:ranged_target", target, direction=target_direction, distance=0.030, duration=0.16)
            elif action_id == "combat_magic":
                self._animate_projectile(obj, "magic")
                self._start_anim("start_tilt", "action:caster_lean", player_node, pitch=2.0, roll=2.5, speed=4.8)
                self._start_anim("start_flash", "action:magic_glow", target, color=(0.58, 0.72, 1.25, 1.0), speed=7.0)
                self._start_anim("start_burst", "action:magic_burst", target, amplitude=0.045, color=(0.54, 0.72, 1.20, 1.0), duration=0.24)
            else:
                speed = 8.8 if action_id == "combat_strength" else 7.8
                amplitude = 56.0 if action_id == "combat_strength" else 44.0
                self._start_anim("start_swing", "action:arm", right_arm, axis="p", amplitude=amplitude, speed=speed, steps=8)
                self._start_anim("start_swing", "action:tool", tool, axis="p", amplitude=amplitude + 16.0, speed=speed, phase=0.20, steps=8)
                if action_id == "combat_defence":
                    self._start_anim("start_tilt", "action:defence_brace", player_node, pitch=-1.5, roll=3.0, speed=5.8)
            self._start_anim("start_bob", "action:combat_bob", player_node, amplitude=0.018, speed=7.8)
            self._start_anim("start_pulse", "action:combat_target", target, amplitude=0.018, speed=7.8)

    def _stop_action_animation(self) -> None:
        stop_player = getattr(self.player, "stop_action_animation", None)
        if callable(stop_player):
            stop_player()
        if self.animator is not None and hasattr(self.animator, "stop_prefix"):
            self.animator.stop_prefix("action:")

    def _start_player_action(self, action_id: str, skill_id: str | None) -> None:
        start_player = getattr(self.player, "start_action_animation", None)
        if not callable(start_player):
            return
        player_action = skill_id if action_id == "gathering" else action_id
        if player_action is not None:
            start_player(player_action)

    def _animate_hit(self, obj: WorldObject | None, damage: int = 0) -> None:
        if obj is None or self.animator is None:
            return
        self._start_anim(
            "start_hit",
            f"fx:hit:{obj.object_id}",
            obj.node,
            direction=self._direction_from_player(obj),
        )
        self._start_anim(
            "start_impact",
            f"fx:impact:{obj.object_id}",
            obj.node,
            direction=self._direction_from_player(obj),
            distance=0.045,
            duration=0.18,
        )
        self._start_motion_profile(
            f"fx:response:{obj.object_id}",
            obj.node,
            self._mob_response_clip,
            phase=_motion_phase(obj.object_id),
        )
        if damage > 0:
            self._start_anim(
                "start_float_text",
                f"fx:damage:{obj.object_id}",
                obj.node,
                text=f"-{damage}",
                color=(1.0, 0.30, 0.18, 1.0),
            )

    def _animate_projectile(self, obj: WorldObject | None, kind: str) -> None:
        root = getattr(self.world_map, "root", None)
        if obj is None or self.animator is None or root is None:
            return
        start_x, start_y = self.world_map.grid.to_world(self.player.tile)
        target_x, target_y = self.world_map.grid.to_world(obj.tile)
        if kind == "magic":
            color = (0.58, 0.72, 1.25, 1.0)
            projectile = make_box(f"fx_magic_bolt_{obj.object_id}", (0.13, 0.13, 0.13), color)
            arc = 0.26
            duration = 0.34
        else:
            color = (0.80, 0.58, 0.32, 1.0)
            projectile = make_box(f"fx_arrow_{obj.object_id}", (0.055, 0.34, 0.040), color)
            arc = 0.10
            duration = 0.24
        projectile.reparentTo(root)
        apply_surface_texture(projectile, "spark" if kind == "magic" else "impact")
        projectile.setPos(start_x, start_y, 0.58)
        projectile.setH(heading_for_delta(obj.tile[0] - self.player.tile[0], obj.tile[1] - self.player.tile[1]))
        self._start_anim(
            "start_projectile",
            f"fx:projectile:{kind}:{obj.object_id}",
            projectile,
            target_pos=(target_x, target_y, 0.55),
            color=color,
            arc=arc,
            duration=duration,
        )

    def _animate_player_hit(self, damage: int) -> None:
        if self.animator is None:
            return
        player_node = getattr(self.player, "node", None)
        self._start_player_action("combat_reaction", None)
        self._start_anim(
            "start_hit",
            "fx:player_hit",
            player_node,
            direction=(0.0, -1.0, 0.0),
            distance=0.035,
            duration=0.18,
        )
        self._start_anim(
            "start_float_text",
            "fx:player_damage",
            player_node,
            text=f"-{damage}",
            color=(1.0, 0.20, 0.12, 1.0),
        )

    def _animate_defeat(self, obj: WorldObject) -> None:
        if obj.node is None or self.animator is None or not hasattr(obj.node, "copyTo"):
            return
        parent = obj.node.getParent()
        if parent is None:
            return
        copy = obj.node.copyTo(parent)
        copy.setName(f"{obj.object_id}_defeat_fx")
        self._start_anim("start_defeat", f"fx:defeat:{obj.object_id}", copy)

    def _animate_ground_drops(self, objects: list[WorldObject]) -> None:
        if self.animator is None:
            return
        for obj in objects:
            self._start_anim("start_pop_in", f"fx:drop:{obj.object_id}", obj.node)

    def _start_anim(self, method_name: str, key: str, node: object | None, **kwargs: object) -> None:
        if node is None or self.animator is None:
            return
        method = getattr(self.animator, method_name, None)
        if method is not None:
            method(key, node, **kwargs)

    def _start_motion_profile(
        self,
        key_prefix: str,
        node: object | None,
        profile: dict[str, object] | None,
        *,
        phase: float = 0.0,
    ) -> bool:
        if node is None or self.animator is None or profile is None:
            return False
        method = getattr(self.animator, "start_motion_profile", None)
        if not callable(method):
            return False
        return bool(method(key_prefix, node, profile, phase=phase))

    def _face_object(self, obj: WorldObject | None) -> None:
        if obj is None:
            return
        dx = obj.tile[0] - self.player.tile[0]
        dy = obj.tile[1] - self.player.tile[1]
        if dx == 0 and dy == 0:
            return
        if hasattr(self.player, "heading"):
            self.player.heading = heading_for_delta(dx, dy)
        sync_node = getattr(self.player, "_sync_node", None)
        if callable(sync_node):
            sync_node()

    def _direction_from_player(self, obj: WorldObject) -> tuple[float, float, float]:
        dx = float(obj.tile[0] - self.player.tile[0])
        dy = float(obj.tile[1] - self.player.tile[1])
        if dx == 0.0 and dy == 0.0:
            return (0.0, -1.0, 0.0)
        return (dx, dy, 0.0)

    def _cancel_gathering(self) -> None:
        if self.gathering is not None and self.gathering.cancel_pending():
            self._stop_action_animation()

    def _gathering_target_invalid(self) -> bool:
        if self.gathering is None or self.gathering.pending is None:
            return False
        obj = self._get_target(self.gathering.pending.node_id)
        return obj is None or not obj.active or obj.object_id not in self.gathering.nodes or not self._in_range(obj.tile)

    def _cancel_cooking(self) -> None:
        if self.cooking is not None and self.cooking.cancel_pending():
            self._stop_action_animation()

    def _cancel_combat(self) -> None:
        if self.combat is not None and self.combat.cancel_pending():
            self._stop_action_animation()

    def _cancel_smithing(self) -> None:
        if self.smithing is not None and self.smithing.cancel_pending():
            self._stop_action_animation()

    def _item_name(self, item_id: str) -> str:
        if self.cooking is not None:
            return str(self.cooking.item_definitions.get(item_id, {}).get("name") or item_id.replace("_", " "))
        definition = self.shop.item_definitions.get(item_id)
        if definition is not None:
            return str(definition.get("name") or item_id.replace("_", " "))
        return item_id.replace("_", " ")

    def _examine_text(self, obj: WorldObject) -> str:
        if obj.kind == "mob":
            return f"{obj.display_name}: level {obj.level}, {obj.hitpoints} HP"
        if obj.kind == "ground_item":
            return f"{obj.quantity} {self._item_name(obj.item_id)} on the ground"
        if self._is_gatherable(obj):
            node = self.world_map.resource_node_for_object(obj)
            if node is not None:
                return f"{obj.display_name or obj.kind.replace('_', ' ').title()}: {self._resource_detail_text(node)}"
        if obj.scenery:
            return obj.display_name or obj.kind.replace("_", " ").title()
        return obj.display_name or obj.kind.replace("_", " ").title()

    def _resource_detail_text(self, node: object, *, catch_label: str = "yields") -> str:
        skill_id = str(getattr(node, "skill_id", ""))
        skill_name = self.skills.display_name(skill_id) if hasattr(self.skills, "display_name") else skill_id.replace("_", " ").title()
        required_level = int(getattr(node, "required_level", 1))
        item_id = str(getattr(node, "item_reward", ""))
        tool_id, tool_name = REQUIRED_TOOLS.get(skill_id, ("", ""))
        requirement = f"requires {skill_name} level {required_level}"
        if tool_id:
            requirement = f"{requirement} and {tool_name}"
        return f"{requirement}; {catch_label} {self._item_name(item_id)}"


def _object_label(obj: WorldObject) -> str:
    return obj.display_name or obj.kind.replace("_", " ").title()


def _combat_animation_id(style: str) -> str:
    normalized = style if style in {"attack", "strength", "defence", "ranged", "magic"} else "attack"
    return f"combat_{normalized}"


def _motion_phase(name: str) -> float:
    if not name:
        return 0.0
    return (sum(ord(char) for char in name) % 360) * math.pi / 180.0
