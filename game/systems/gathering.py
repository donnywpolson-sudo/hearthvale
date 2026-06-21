from __future__ import annotations

from dataclasses import dataclass
import random
import time
from typing import Any, Callable, Iterable

from game.systems.inventory import INVENTORY_SLOT_LIMIT, inventory_can_add
from game.world.grid import Tile, TileGrid
from game.world.pathfinding import find_path


TimeProvider = Callable[[], float]
REQUIRED_TOOLS = {
    "woodcutting": ("bronze_axe", "woodcutting axe"),
    "mining": ("bronze_pickaxe", "pickaxe"),
    "fishing": ("fishing_rod", "fishing rod"),
}


@dataclass(frozen=True)
class ResourceNode:
    node_id: str
    node_type: str
    skill_id: str
    required_level: int
    xp_reward: int
    item_reward: str
    quantity_reward: int
    depleted_state: str
    respawn_seconds: float
    blocks_movement: bool
    position: Tile
    display_name: str = ""
    base_gather_seconds: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceNode":
        position = data["position"]
        node_type = str(data["node_type"])
        return cls(
            node_id=str(data["node_id"]),
            node_type=node_type,
            display_name=str(data.get("display_name") or node_type.replace("_", " ").title()),
            skill_id=str(data["skill_id"]),
            required_level=int(data["required_level"]),
            xp_reward=int(data["xp_reward"]),
            item_reward=str(data["item_reward"]),
            quantity_reward=int(data["quantity_reward"]),
            depleted_state=str(data["depleted_state"]),
            respawn_seconds=float(data["respawn_seconds"]),
            base_gather_seconds=float(data.get("base_gather_seconds", 0.0)),
            blocks_movement=bool(data["blocks_movement"]),
            position=(int(position[0]), int(position[1])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "display_name": self.display_name,
            "skill_id": self.skill_id,
            "required_level": self.required_level,
            "xp_reward": self.xp_reward,
            "item_reward": self.item_reward,
            "quantity_reward": self.quantity_reward,
            "depleted_state": self.depleted_state,
            "respawn_seconds": self.respawn_seconds,
            "base_gather_seconds": self.base_gather_seconds,
            "blocks_movement": self.blocks_movement,
            "position": list(self.position),
        }


@dataclass
class ResourceNodeState:
    depleted: bool = False
    respawn_at: float | None = None
    uses_remaining: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceNodeState":
        respawn_at = data.get("respawn_at")
        uses_remaining = data.get("uses_remaining")
        return cls(
            depleted=bool(data.get("depleted", False)),
            respawn_at=float(respawn_at) if respawn_at is not None else None,
            uses_remaining=int(uses_remaining) if uses_remaining is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"depleted": self.depleted, "respawn_at": self.respawn_at}
        if self.uses_remaining is not None:
            data["uses_remaining"] = self.uses_remaining
        return data


@dataclass(frozen=True)
class GatheringResult:
    success: bool
    feedback: str
    node_id: str | None = None
    skill_id: str | None = None
    item_id: str | None = None
    quantity: int = 0
    xp: int = 0
    new_player_tile: Tile | None = None
    pending: bool = False
    duration: float = 0.0


@dataclass(frozen=True)
class PendingGather:
    node_id: str
    complete_at: float
    duration: float


class GatheringSystem:
    def __init__(
        self,
        nodes: Iterable[ResourceNode] | dict[str, ResourceNode],
        inventory: Any,
        skills: Any,
        *,
        time_provider: TimeProvider = time.time,
        states: dict[str, ResourceNodeState] | None = None,
        item_definitions: dict[str, dict[str, object]] | None = None,
        slot_limit: int = INVENTORY_SLOT_LIMIT,
        rng: random.Random | None = None,
    ) -> None:
        self.nodes = dict(nodes) if isinstance(nodes, dict) else {node.node_id: node for node in nodes}
        self.inventory = inventory
        self.skills = skills
        self.time_provider = time_provider
        self.states: dict[str, ResourceNodeState] = states or {}
        self.pending: PendingGather | None = None
        self.item_definitions = item_definitions or {}
        self.slot_limit = slot_limit
        self.rng = rng or random.Random()

    def gather(
        self,
        node_id: str,
        player_tile: Tile,
        grid: TileGrid,
        blocked_tiles: Iterable[Tile],
        *,
        allow_movement: bool = True,
    ) -> GatheringResult:
        return self.start_gather(
            node_id,
            player_tile,
            grid,
            blocked_tiles,
            allow_movement=allow_movement,
        )

    def start_gather(
        self,
        node_id: str,
        player_tile: Tile,
        grid: TileGrid,
        blocked_tiles: Iterable[Tile],
        *,
        allow_movement: bool = True,
    ) -> GatheringResult:
        node = self.nodes.get(node_id)
        if node is None:
            return GatheringResult(False, "No object selected")

        if self.pending is not None:
            if self.pending.node_id == node_id:
                return GatheringResult(
                    True,
                    _pending_feedback(node, self.remaining_seconds()),
                    node_id=node.node_id,
                    skill_id=node.skill_id,
                    item_id=node.item_reward,
                    pending=True,
                    duration=self.pending.duration,
                )
            self.cancel_pending()

        if self.is_depleted(node.node_id):
            return GatheringResult(False, f"{_node_label(node)} is depleted", node_id=node.node_id)

        blocked = set(blocked_tiles)
        destination = self._find_interaction_tile(
            node,
            player_tile,
            grid,
            blocked,
            allow_movement=allow_movement,
        )
        if destination is None:
            return GatheringResult(False, "No path" if allow_movement else "Too far away", node_id=node.node_id)

        if destination != player_tile:
            return GatheringResult(
                True,
                f"Walking to {_node_label(node)}",
                node_id=node.node_id,
                skill_id=node.skill_id,
                item_id=node.item_reward,
                new_player_tile=destination,
            )

        current_level = _skill_level(self.skills, node.skill_id)
        tool_id, tool_name = REQUIRED_TOOLS.get(node.skill_id, ("", ""))
        if tool_id and self.inventory.count(tool_id) <= 0:
            article = "an" if tool_name[:1].lower() in {"a", "e", "i", "o", "u"} else "a"
            return GatheringResult(
                False,
                f"You need {article} {tool_name}",
                node_id=node.node_id,
                new_player_tile=destination if destination != player_tile else None,
            )

        if current_level < node.required_level:
            return GatheringResult(
                False,
                f"You need {_skill_name(self.skills, node.skill_id)} level {node.required_level}",
                node_id=node.node_id,
                new_player_tile=destination if destination != player_tile else None,
            )

        if not self._inventory_can_accept(node):
            return GatheringResult(False, "Inventory is full", node_id=node.node_id, skill_id=node.skill_id)

        duration = self._schedule_next_attempt(node)

        return GatheringResult(
            True,
            _start_feedback(node, duration),
            node_id=node.node_id,
            skill_id=node.skill_id,
            item_id=node.item_reward,
            pending=True,
            duration=duration,
        )

    def update(self) -> GatheringResult | None:
        if self.pending is None or self.time_provider() < self.pending.complete_at:
            return None

        pending = self.pending
        self.pending = None
        node = self.nodes.get(pending.node_id)
        if node is None:
            return GatheringResult(False, "No object selected")
        if self.is_depleted(node.node_id):
            return GatheringResult(False, f"{_node_label(node)} is depleted", node_id=node.node_id)
        requirement = self._requirement_failure(node)
        if requirement is not None:
            return requirement
        if not self._inventory_can_accept(node):
            return GatheringResult(False, "Inventory is full", node_id=node.node_id, skill_id=node.skill_id)

        if self.rng.random() > self.success_chance(node):
            duration = self._schedule_next_attempt(node)
            return GatheringResult(
                True,
                _failure_feedback(node, duration),
                node_id=node.node_id,
                skill_id=node.skill_id,
                item_id=node.item_reward,
                pending=True,
                duration=duration,
            )

        self.inventory.add(node.item_reward, node.quantity_reward)
        self.skills.add_xp(node.skill_id, node.xp_reward)
        uses_remaining = self._consume_node_use(node)
        should_continue = False
        duration = 0.0
        if uses_remaining <= 0:
            self._deplete(node)
        elif self._inventory_can_accept(node):
            should_continue = True
            duration = self._schedule_next_attempt(node)
        else:
            duration = 0.0

        return GatheringResult(
            True,
            _success_feedback(node, self.skills),
            node_id=node.node_id,
            skill_id=node.skill_id,
            item_id=node.item_reward,
            quantity=node.quantity_reward,
            xp=node.xp_reward,
            pending=should_continue,
            duration=duration if should_continue else 0.0,
        )

    def cancel_pending(self) -> bool:
        if self.pending is None:
            return False
        self.pending = None
        return True

    def remaining_seconds(self) -> float:
        if self.pending is None:
            return 0.0
        return max(0.0, self.pending.complete_at - self.time_provider())

    def gather_duration(self, node: ResourceNode) -> float:
        current_level = _skill_level(self.skills, node.skill_id)
        level_advantage = max(0, current_level - node.required_level)
        speed_bonus = min(0.40, 0.012 * level_advantage)
        return max(0.75, node.base_gather_seconds * (1.0 - speed_bonus))

    def success_chance(self, node: ResourceNode) -> float:
        current_level = _skill_level(self.skills, node.skill_id)
        level_advantage = max(0, current_level - node.required_level)
        chance = 0.45 + level_advantage * 0.015 - (resource_tier(node) - 1) * 0.04
        return _clamp(chance, 0.20, 0.92)

    def node_capacity(self, node: ResourceNode) -> int:
        current_level = _skill_level(self.skills, node.skill_id)
        level_advantage = max(0, current_level - node.required_level)
        tier = resource_tier(node)
        max_bonus = max(0, 3 - tier)
        rng_bonus = self.rng.randint(0, max_bonus) if max_bonus > 0 else 0
        capacity = max(1, 5 - tier) + min(2, level_advantage // 25) + rng_bonus
        return int(_clamp(float(capacity), 1.0, 6.0))

    def respawn_seconds(self, node: ResourceNode) -> float:
        return node.respawn_seconds * (1.0 + 0.08 * (resource_tier(node) - 1))

    def is_depleted(self, node_id: str) -> bool:
        self._refresh_node(node_id)
        return self.states.get(node_id, ResourceNodeState()).depleted

    def refresh_all(self) -> None:
        for node_id in list(self.nodes):
            self._refresh_node(node_id)

    def blocking_tiles(self) -> set[Tile]:
        return {
            node.position
            for node in self.nodes.values()
            if node.blocks_movement and not self.is_depleted(node.node_id)
        }

    def to_dict(self) -> dict[str, dict[str, Any]]:
        self.refresh_all()
        return {
            node_id: state.to_dict()
            for node_id, state in sorted(self.states.items())
            if node_id in self.nodes
            and (state.depleted or state.respawn_at is not None or state.uses_remaining is not None)
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        self.cancel_pending()
        self.states.clear()
        for node_id, raw_state in data.items():
            if node_id not in self.nodes or not isinstance(raw_state, dict):
                continue
            self.states[node_id] = ResourceNodeState.from_dict(raw_state)
        self.refresh_all()

    def reset_node(self, node_id: str) -> None:
        if self.pending is not None and self.pending.node_id == node_id:
            self.cancel_pending()
        self.states.pop(node_id, None)

    def _deplete(self, node: ResourceNode) -> None:
        respawn_at = None
        if node.respawn_seconds > 0:
            respawn_at = self.time_provider() + self.respawn_seconds(node)
        self.states[node.node_id] = ResourceNodeState(depleted=True, respawn_at=respawn_at, uses_remaining=0)

    def _refresh_node(self, node_id: str) -> None:
        state = self.states.get(node_id)
        if state is None or not state.depleted or state.respawn_at is None:
            return
        if self.time_provider() >= state.respawn_at:
            self.states.pop(node_id, None)

    def _schedule_next_attempt(self, node: ResourceNode) -> float:
        duration = self.gather_duration(node)
        self.pending = PendingGather(
            node_id=node.node_id,
            complete_at=self.time_provider() + duration,
            duration=duration,
        )
        return duration

    def _requirement_failure(self, node: ResourceNode) -> GatheringResult | None:
        tool_id, tool_name = REQUIRED_TOOLS.get(node.skill_id, ("", ""))
        if tool_id and self.inventory.count(tool_id) <= 0:
            article = "an" if tool_name[:1].lower() in {"a", "e", "i", "o", "u"} else "a"
            return GatheringResult(False, f"You need {article} {tool_name}", node_id=node.node_id)
        current_level = _skill_level(self.skills, node.skill_id)
        if current_level < node.required_level:
            return GatheringResult(
                False,
                f"You need {_skill_name(self.skills, node.skill_id)} level {node.required_level}",
                node_id=node.node_id,
            )
        return None

    def _inventory_can_accept(self, node: ResourceNode) -> bool:
        return inventory_can_add(
            self.inventory.to_dict(),
            self.item_definitions,
            node.item_reward,
            node.quantity_reward,
            slot_limit=self.slot_limit,
        )

    def _consume_node_use(self, node: ResourceNode) -> int:
        state = self.states.get(node.node_id)
        if state is None or state.depleted:
            state = ResourceNodeState()
        if state.uses_remaining is None:
            state.uses_remaining = self.node_capacity(node)
        state.uses_remaining = max(0, state.uses_remaining - 1)
        self.states[node.node_id] = state
        return state.uses_remaining

    def _find_interaction_tile(
        self,
        node: ResourceNode,
        player_tile: Tile,
        grid: TileGrid,
        blocked_tiles: set[Tile],
        *,
        allow_movement: bool,
    ) -> Tile | None:
        interaction_tiles = self._interaction_tiles(node, grid, blocked_tiles)
        if player_tile in interaction_tiles:
            return player_tile

        if not allow_movement:
            return None

        reachable: list[tuple[int, Tile]] = []
        for tile in interaction_tiles:
            path = find_path(grid, player_tile, tile, blocked_tiles)
            if path:
                reachable.append((len(path), tile))

        if not reachable:
            return None
        reachable.sort()
        return reachable[0][1]

    def _interaction_tiles(
        self,
        node: ResourceNode,
        grid: TileGrid,
        blocked_tiles: set[Tile],
    ) -> list[Tile]:
        tiles: list[Tile] = []
        if not node.blocks_movement and grid.in_bounds(node.position) and node.position not in blocked_tiles:
            tiles.append(node.position)

        for tile in grid.neighbors(node.position, diagonals=False):
            if tile not in blocked_tiles:
                tiles.append(tile)
        return tiles


def resource_nodes_from_data(data: Iterable[dict[str, Any]]) -> dict[str, ResourceNode]:
    nodes = [ResourceNode.from_dict(raw_node) for raw_node in data]
    return {node.node_id: node for node in nodes}


def resource_tier(node: ResourceNode) -> int:
    return 1 + max(0, node.required_level // 15)


def _skill_level(skills: Any, skill_id: str) -> int:
    if hasattr(skills, "level"):
        return int(skills.level(skill_id))
    return int(skills.get(skill_id).level)


def _skill_name(skills: Any, skill_id: str) -> str:
    if hasattr(skills, "display_name"):
        return str(skills.display_name(skill_id))
    definition = getattr(skills, "definitions", {}).get(skill_id, {})
    return str(definition.get("display_name") or definition.get("name") or skill_id.replace("_", " ").title())


def _item_name(item_id: str) -> str:
    return item_id.replace("_", " ")


def _node_label(node: ResourceNode) -> str:
    if node.display_name:
        return node.display_name
    labels = {
        "tree": "Tree",
        "copper_rock": "Copper rock",
        "fishing_spot": "Fishing spot",
    }
    return labels.get(node.node_type, node.node_type.replace("_", " ").title())


def _start_feedback(node: ResourceNode, duration: float) -> str:
    verb = {
        "woodcutting": "Chopping",
        "fishing": "Fishing",
        "mining": "Mining",
    }.get(node.skill_id, "Gathering")
    return f"{verb} {_node_label(node)}... {duration:.1f}s"


def _pending_feedback(node: ResourceNode, remaining_seconds: float) -> str:
    verb = {
        "woodcutting": "Chopping",
        "fishing": "Fishing",
        "mining": "Mining",
    }.get(node.skill_id, "Gathering")
    return f"{verb} {_node_label(node)}... {remaining_seconds:.1f}s"


def _failure_feedback(node: ResourceNode, duration: float) -> str:
    verb = {
        "woodcutting": "You keep chopping",
        "fishing": "No bite yet",
        "mining": "The rock resists",
    }.get(node.skill_id, "You keep gathering")
    return f"{verb}; trying again... {duration:.1f}s"


def _success_feedback(node: ResourceNode, skills: Any) -> str:
    prefix = {
        "woodcutting": f"Chopped {_node_label(node)}",
        "mining": f"Mined {_node_label(node)}",
        "fishing": f"Caught {_item_name(node.item_reward)}",
    }.get(node.skill_id, f"Gathered {_node_label(node).lower()}")
    return (
        f"{prefix}: +{node.quantity_reward} {_item_name(node.item_reward)}, "
        f"+{node.xp_reward} {_skill_name(skills, node.skill_id)} XP"
    )


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
