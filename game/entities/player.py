from __future__ import annotations

import math

from panda3d.core import NodePath, Vec3

from game import settings
from game.world import visuals
from game.world.grid import Tile, TileGrid


class Player:
    def __init__(self, grid: TileGrid, start_tile: Tile) -> None:
        self.grid = grid
        self.tile = start_tile
        self.x, self.y = grid.to_world(start_tile)
        self.path: list[Tile] = []
        self.node: NodePath | None = None
        self.parts: dict[str, NodePath] = {}
        self.heading = 0.0
        self.walk_time = 0.0

    def render(self, parent: NodePath) -> None:
        self.node = parent.attachNewNode("player")
        self.parts = visuals.render_player_model(self.node)
        self._sync_node()

    @property
    def is_moving(self) -> bool:
        return bool(self.path)

    def set_path(self, path: list[Tile]) -> None:
        self.path = list(path)
        if self.path and self.path[0] == self.tile:
            self.path.pop(0)

    def update(self, dt: float) -> None:
        if not self.path:
            self.walk_time = 0.0
            self._sync_node()
            return

        self.walk_time += dt * 9.0
        target_tile = self.path[0]
        target_x, target_y = self.grid.to_world(target_tile)
        dx = target_x - self.x
        dy = target_y - self.y
        distance = (dx * dx + dy * dy) ** 0.5
        step = settings.PLAYER_SPEED * dt

        if distance <= step or distance < 0.001:
            self.x = target_x
            self.y = target_y
            self.tile = target_tile
            self.path.pop(0)
        else:
            self.heading = math.degrees(math.atan2(-dx, dy))
            self.x += dx / distance * step
            self.y += dy / distance * step

        self._sync_node()

    def set_position_tile(self, tile: Tile) -> None:
        self.tile = tile
        self.x, self.y = self.grid.to_world(tile)
        self.path.clear()
        self._sync_node()

    def to_dict(self) -> dict[str, object]:
        return {"tile": list(self.tile), "position": [self.x, self.y]}

    def load_dict(self, data: dict[str, object]) -> None:
        tile_data = data.get("tile", self.tile)
        tile = (int(tile_data[0]), int(tile_data[1]))  # type: ignore[index]
        if self.grid.in_bounds(tile):
            self.tile = tile
            self.x, self.y = self.grid.to_world(tile)

        position = data.get("position")
        if isinstance(position, list) and len(position) == 2:
            self.x = float(position[0])
            self.y = float(position[1])
        self.path.clear()
        self._sync_node()

    def _sync_node(self) -> None:
        if self.node is not None:
            bob = 0.0
            if self.path:
                bob = abs(math.sin(self.walk_time)) * 0.035
                sway = math.sin(self.walk_time) * 6.0
                self.parts.get("left_leg", self.node).setP(sway)
                self.parts.get("right_leg", self.node).setP(-sway)
                self.parts.get("left_arm", self.node).setP(-sway * 0.6)
                self.parts.get("right_arm", self.node).setP(sway * 0.6)
            else:
                for key in ("left_leg", "right_leg", "left_arm", "right_arm"):
                    if key in self.parts:
                        self.parts[key].setP(0)
            self.node.setPos(Vec3(self.x, self.y, 0.02 + bob))
            self.node.setH(self.heading)
