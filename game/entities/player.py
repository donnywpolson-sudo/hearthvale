from __future__ import annotations

import math

from panda3d.core import NodePath, Vec3

from game.assets.runtime import load_animation_clip_data
from game import settings
from game.world import visuals
from game.world.grid import Tile, TileGrid


PLAYER_RIG_PARTS = ("left_leg", "right_leg", "left_arm", "right_arm", "body", "head", "tool")
PLAYER_COMBAT_ACTIONS = (
    "combat_attack",
    "combat_strength",
    "combat_defence",
    "combat_ranged",
    "combat_magic",
    "combat_reaction",
)


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
        self.idle_time = 0.0
        self.action_animation: str | None = None
        self.action_time = 0.0
        self.action_duration: float | None = None
        self._idle_motion_profile = load_animation_clip_data("player_idle")
        self._walk_motion_profile = load_animation_clip_data("player_walk")
        self._action_motion_profiles = {
            action: load_animation_clip_data(f"player_{action}")
            for action in PLAYER_COMBAT_ACTIONS
        }

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
        if self.path:
            self.stop_action_animation(sync=False)

    def update(self, dt: float) -> None:
        if not self.path:
            self.walk_time = 0.0
            self.idle_time += dt
            if self.action_animation is not None:
                self.action_time += dt
                if self.action_duration is not None and self.action_time >= self.action_duration:
                    self.stop_action_animation(sync=False)
            self._sync_node()
            return

        self.stop_action_animation(sync=False)
        self.idle_time = 0.0
        self.walk_time += dt * 7.15
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
            self.heading = heading_for_delta(dx, dy)
            self.x += dx / distance * step
            self.y += dy / distance * step

        self._sync_node()

    def set_position_tile(self, tile: Tile) -> None:
        self.stop_action_animation(sync=False)
        self.tile = tile
        self.x, self.y = self.grid.to_world(tile)
        self.path.clear()
        self._sync_node()

    def to_dict(self) -> dict[str, object]:
        return {"tile": list(self.tile), "position": [self.x, self.y]}

    def load_dict(self, data: dict[str, object]) -> None:
        self.stop_action_animation(sync=False)
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

    def start_action_animation(self, action_type: str) -> None:
        if self.action_animation != action_type:
            self.action_time = 0.0
        self.action_animation = action_type
        self.action_duration = 0.30 if action_type == "combat_reaction" else None
        self._sync_node()

    def stop_action_animation(self, *, sync: bool = True) -> bool:
        if self.action_animation is None and self.action_time == 0.0:
            return False
        self.action_animation = None
        self.action_time = 0.0
        self.action_duration = None
        if sync:
            self._sync_node()
        return True

    def _sync_node(self) -> None:
        if self.node is not None:
            bob = 0.0
            if self.path:
                stride = math.sin(self.walk_time)
                counter = math.sin(self.walk_time + math.pi)
                lift = abs(math.sin(self.walk_time))
                bob = lift * 0.045
                self._reset_pose()
                if self._walk_motion_profile is not None and self._apply_motion_profile(
                    self._walk_motion_profile,
                    self.walk_time,
                    required_parts=PLAYER_RIG_PARTS,
                ):
                    pass
                else:
                    self._apply_walk_pose(stride, counter, lift)
            else:
                self._reset_pose()
                if self.action_animation is not None:
                    self._apply_action_pose(self.action_animation)
                elif self._idle_motion_profile is not None and self._apply_motion_profile(
                    self._idle_motion_profile,
                    self.idle_time,
                    required_parts=PLAYER_RIG_PARTS,
                ):
                    pass
                else:
                    self._apply_idle_pose()
            self.node.setPos(Vec3(self.x, self.y, 0.02 + bob))
            self.node.setH(self.heading)

    def _apply_walk_pose(self, stride: float, counter: float, lift: float) -> None:
        self._set_part_hpr("left_leg", 0.0, stride * 22.0, stride * 2.5)
        self._set_part_hpr("right_leg", 0.0, counter * 22.0, counter * 2.5)
        self._set_part_hpr("left_arm", 0.0, counter * 18.0, -5.0 + counter * 2.5)
        self._set_part_hpr("right_arm", 0.0, stride * 18.0, 5.0 + stride * 2.5)
        self._set_part_hpr("body", 0.0, 1.2 + lift * 1.4, stride * 2.0)
        self._set_part_hpr("head", 0.0, -0.8 + lift * 0.8, -stride * 1.0)
        self._set_part_hpr("tool", -16.0 + stride * 2.4, -4.0 + counter * 5.2, -10.0 + stride * 3.2)

    def _apply_action_pose(self, action_type: str) -> None:
        if action_type == "combat":
            action_type = "combat_attack"
        profile = self._action_motion_profiles.get(action_type)
        if profile is not None and self._apply_motion_profile(
            profile,
            self.action_time,
            required_parts=PLAYER_RIG_PARTS,
        ):
            return

        cycle = math.sin(self.action_time * 6.0)
        fast_cycle = math.sin(self.action_time * 9.5)
        impact = max(0.0, fast_cycle)
        recoil = max(0.0, -fast_cycle)
        if action_type == "combat_reaction":
            self._set_part_hpr("body", 0.0, -6.0 + impact * 8.0, 12.0 + impact * 4.0)
            self._set_part_hpr("head", 0.0, 4.0 - impact * 2.0, -6.0)
            self._set_part_hpr("left_leg", 0.0, -4.0, -3.0)
            self._set_part_hpr("right_leg", 0.0, 4.0, 3.0)
            self._set_part_hpr("left_arm", 0.0, 14.0 + impact * 6.0, -18.0)
            self._set_part_hpr("right_arm", 0.0, -16.0 - impact * 6.0, 18.0)
            self._set_part_hpr("tool", -14.0, -20.0 - impact * 12.0, -16.0)
        elif action_type == "woodcutting":
            self._set_part_hpr("body", 0.0, 5.0 + impact * 5.0, -8.0 + cycle * 2.0)
            self._set_part_hpr("head", 0.0, 3.0 + impact * 2.0, -3.0)
            self._set_part_hpr("left_leg", 0.0, -8.0, -4.0)
            self._set_part_hpr("right_leg", 0.0, 7.0, 4.0)
            self._set_part_hpr("right_arm", 4.0, -62.0 + fast_cycle * 32.0, 18.0 + impact * 9.0)
            self._set_part_hpr("left_arm", -8.0, 26.0 - impact * 9.0, -14.0)
            self._set_part_hpr("tool", -35.0, -58.0 + fast_cycle * 42.0, -28.0 - recoil * 12.0)
        elif action_type == "mining":
            self._set_part_hpr("body", 0.0, 7.0 + impact * 4.0, 4.0)
            self._set_part_hpr("head", 0.0, 5.0, 2.0)
            self._set_part_hpr("left_leg", 0.0, -6.0, -3.0)
            self._set_part_hpr("right_leg", 0.0, 8.0, 3.0)
            self._set_part_hpr("right_arm", 3.0, -68.0 + fast_cycle * 34.0, 10.0)
            self._set_part_hpr("left_arm", -4.0, 22.0 - impact * 8.0, -10.0)
            self._set_part_hpr("tool", -18.0, -62.0 + fast_cycle * 44.0, -12.0 - recoil * 8.0)
        elif action_type == "fishing":
            self._set_part_hpr("body", 0.0, 8.0 + cycle * 2.0, -4.0)
            self._set_part_hpr("head", 0.0, 6.0 + cycle, -2.0)
            self._set_part_hpr("left_leg", 0.0, 2.0, -2.0)
            self._set_part_hpr("right_leg", 0.0, -2.0, 2.0)
            self._set_part_hpr("right_arm", 0.0, -26.0 + cycle * 4.0, -34.0 + cycle * 10.0)
            self._set_part_hpr("left_arm", 0.0, 14.0 + cycle * 3.0, 14.0)
            self._set_part_hpr("tool", -42.0, 2.0 + cycle * 5.0, -50.0 + cycle * 14.0)
        elif action_type == "cooking":
            self._set_part_hpr("body", 0.0, 6.0 + cycle * 1.5, 1.5)
            self._set_part_hpr("head", 0.0, 4.0 + cycle * 1.2, 0.0)
            self._set_part_hpr("right_arm", 0.0, -24.0 + cycle * 12.0, 16.0)
            self._set_part_hpr("left_arm", 0.0, 12.0 - cycle * 3.0, -11.0)
            self._set_part_hpr("tool", -8.0, -16.0 + cycle * 12.0, 22.0)
        elif action_type == "smelting":
            self._set_part_hpr("body", 0.0, 8.0 + cycle * 1.4, 0.0)
            self._set_part_hpr("right_arm", 0.0, -18.0 + cycle * 5.0, 12.0)
            self._set_part_hpr("left_arm", 0.0, 10.0 - cycle * 3.0, -12.0)
            self._set_part_hpr("head", 0.0, 4.0 + cycle, 0.0)
        elif action_type == "smithing":
            self._set_part_hpr("body", 0.0, 6.0 + impact * 5.0, 4.0)
            self._set_part_hpr("head", 0.0, 4.0, 2.0)
            self._set_part_hpr("left_leg", 0.0, -7.0, -3.0)
            self._set_part_hpr("right_leg", 0.0, 7.0, 3.0)
            self._set_part_hpr("right_arm", 2.0, -70.0 + fast_cycle * 36.0, 9.0)
            self._set_part_hpr("left_arm", -4.0, 24.0 - impact * 9.0, -9.0)
            self._set_part_hpr("tool", -14.0, -66.0 + fast_cycle * 46.0, -10.0 - recoil * 8.0)
        elif action_type == "combat":
            self._apply_action_pose("combat_attack")
        elif action_type == "combat_attack":
            self._set_part_hpr("body", 0.0, 4.0 + impact * 4.0, 9.0 + fast_cycle * 5.0)
            self._set_part_hpr("head", 0.0, 2.0, 3.0 + fast_cycle * 2.0)
            self._set_part_hpr("left_leg", 0.0, -8.0, -4.0)
            self._set_part_hpr("right_leg", 0.0, 9.0, 4.0)
            self._set_part_hpr("right_arm", 0.0, -56.0 + fast_cycle * 32.0, 28.0)
            self._set_part_hpr("left_arm", 0.0, 20.0, -22.0 + impact * 7.0)
            self._set_part_hpr("tool", -26.0, -52.0 + fast_cycle * 40.0, 20.0 - recoil * 10.0)
        elif action_type == "combat_strength":
            self._set_part_hpr("body", 0.0, 8.0 + impact * 6.0, 13.0 + fast_cycle * 6.0)
            self._set_part_hpr("head", 0.0, 3.0, 4.0 + fast_cycle * 2.0)
            self._set_part_hpr("left_leg", 0.0, -11.0, -6.0)
            self._set_part_hpr("right_leg", 0.0, 12.0, 6.0)
            self._set_part_hpr("right_arm", 2.0, -68.0 + fast_cycle * 40.0, 32.0)
            self._set_part_hpr("left_arm", 0.0, 26.0, -25.0 + impact * 9.0)
            self._set_part_hpr("tool", -32.0, -64.0 + fast_cycle * 48.0, 24.0 - recoil * 14.0)
        elif action_type == "combat_defence":
            self._set_part_hpr("body", 0.0, -2.0 + impact * 2.0, 4.0 + cycle * 2.0)
            self._set_part_hpr("head", 0.0, 1.0, 1.0)
            self._set_part_hpr("left_leg", 0.0, -10.0, -8.0)
            self._set_part_hpr("right_leg", 0.0, 8.0, 8.0)
            self._set_part_hpr("right_arm", 0.0, -38.0 + fast_cycle * 20.0, 18.0)
            self._set_part_hpr("left_arm", 0.0, 42.0, -34.0 + impact * 5.0)
            self._set_part_hpr("tool", -18.0, -36.0 + fast_cycle * 28.0, 10.0)
        elif action_type == "combat_ranged":
            draw = max(0.0, -cycle)
            self._set_part_hpr("body", 0.0, 2.0 + draw * 2.0, -8.0)
            self._set_part_hpr("head", 0.0, 1.5, -4.0)
            self._set_part_hpr("left_leg", 0.0, -6.0, -5.0)
            self._set_part_hpr("right_leg", 0.0, 6.0, 5.0)
            self._set_part_hpr("right_arm", 0.0, -16.0 - draw * 28.0, 40.0)
            self._set_part_hpr("left_arm", 0.0, -4.0 + draw * 8.0, -42.0)
            self._set_part_hpr("tool", -4.0, -8.0 - draw * 12.0, -58.0 + cycle * 8.0)
        elif action_type == "combat_magic":
            cast = max(0.0, fast_cycle)
            self._set_part_hpr("body", 0.0, 5.0 + cast * 3.0, 0.0)
            self._set_part_hpr("head", 0.0, 2.0 + cast * 2.0, 0.0)
            self._set_part_hpr("left_leg", 0.0, -3.0, -3.0)
            self._set_part_hpr("right_leg", 0.0, 3.0, 3.0)
            self._set_part_hpr("right_arm", 0.0, -34.0 + cast * 18.0, 24.0)
            self._set_part_hpr("left_arm", 0.0, -22.0 + cast * 16.0, -24.0)
            self._set_part_hpr("tool", -10.0 + cast * 8.0, -20.0 + cast * 20.0, 36.0 + cycle * 8.0)
        elif action_type == "gathering":
            self._set_part_hpr("body", 0.0, 4.0 + cycle * 2.0, 0.0)
            self._set_part_hpr("right_arm", 0.0, -30.0 + fast_cycle * 18.0, 8.0)
            self._set_part_hpr("left_arm", 0.0, 14.0 - impact * 4.0, -8.0)
            self._set_part_hpr("tool", -18.0, -28.0 + fast_cycle * 24.0, -10.0)

    def _apply_idle_pose(self) -> None:
        breath = math.sin(self.idle_time * 2.2)
        sway = math.sin(self.idle_time * 1.3)
        self._set_part_hpr("body", 0.0, 0.8 + breath * 0.8, sway * 0.9)
        self._set_part_hpr("head", 0.0, -0.4 + breath * 0.4, -sway * 0.5)
        self._set_part_hpr("left_arm", 0.0, 2.0 + breath * 1.2, -4.0)
        self._set_part_hpr("right_arm", 0.0, -2.0 - breath * 1.2, 4.0)

    def _apply_motion_profile(
        self,
        profile: dict[str, object],
        phase: float,
        *,
        required_parts: tuple[str, ...] | None = None,
    ) -> bool:
        parts = profile.get("parts")
        if not isinstance(parts, dict):
            return False

        valid_parts: dict[str, dict[str, object]] = {}
        for part_name, raw_spec in parts.items():
            if not isinstance(part_name, str) or not isinstance(raw_spec, dict):
                continue
            valid_parts[part_name] = raw_spec

        if not valid_parts:
            return False
        if required_parts is not None and any(part_name not in valid_parts for part_name in required_parts):
            return False

        for part_name, spec in valid_parts.items():
            base = _vec3_from_value(spec.get("base"), (0.0, 0.0, 0.0))
            amplitude = _vec3_from_value(spec.get("amplitude"), (0.0, 0.0, 0.0))
            speed = _coerce_float(spec.get("speed"), 1.0)
            phase_offset = _coerce_float(spec.get("phase"), 0.0)
            offset = math.sin(phase * speed + phase_offset)
            self._set_part_hpr(
                part_name,
                base[0] + amplitude[0] * offset,
                base[1] + amplitude[1] * offset,
                base[2] + amplitude[2] * offset,
            )
        return True

    def _reset_pose(self) -> None:
        for key in ("left_leg", "right_leg", "left_arm", "right_arm", "body", "head"):
            self._set_part_hpr(key, 0.0, 0.0, 0.0)
        self._set_part_hpr("tool", -16.0, 0.0, -10.0)

    def _reset_upper_pose(self) -> None:
        for key in ("body", "head"):
            self._set_part_hpr(key, 0.0, 0.0, 0.0)
        self._set_part_hpr("tool", -16.0, 0.0, -10.0)

    def _set_part_hpr(self, key: str, h: float, p: float, r: float) -> None:
        part = self.parts.get(key)
        if part is None:
            return
        part.setHpr(h, p, r)


def heading_for_delta(dx: float, dy: float) -> float:
    if abs(dx) <= 0.000001 and abs(dy) <= 0.000001:
        return 0.0
    heading = math.degrees(math.atan2(-dx, dy)) + 180.0
    if heading > 180.0:
        heading -= 360.0
    return heading


def _vec3_from_value(value: object, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 3:
        try:
            return (float(value[0]), float(value[1]), float(value[2]))
        except (TypeError, ValueError):
            return default
    return default


def _coerce_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
