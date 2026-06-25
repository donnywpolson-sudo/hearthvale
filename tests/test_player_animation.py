from __future__ import annotations

import math

from panda3d.core import NodePath

import game.entities.player as player_module
from game.entities.player import Player
from game.world.grid import TileGrid
from game.world import visuals


def test_player_action_animation_sets_and_restores_pose() -> None:
    player = _player_with_fake_nodes()

    player.start_action_animation("woodcutting")
    action_arm_pose = player.parts["right_arm"].hpr

    assert player.action_animation == "woodcutting"
    assert player.parts["right_arm"].hpr != (0.0, 0.0, 0.0)
    assert player.parts["tool"].hpr != (-16.0, 0.0, -10.0)

    assert player.stop_action_animation()
    assert player.action_animation is None
    assert player.parts["right_arm"].hpr != action_arm_pose
    assert player.parts["tool"].hpr == (-16.0, 0.0, -10.0)


def test_player_movement_stops_action_animation() -> None:
    player = _player_with_fake_nodes()

    player.start_action_animation("fishing")
    player.set_path([(1, 1), (1, 2)])

    assert player.action_animation is None
    assert player.path == [(1, 2)]


def test_player_faces_walk_direction_without_moonwalking() -> None:
    player = _player_with_fake_nodes()

    player.set_path([(1, 1), (1, 2)])
    player.update(0.05)

    assert player.heading == 180.0
    assert player.node.heading == 180.0

    player.set_position_tile((1, 1))
    player.set_path([(1, 1), (2, 1)])
    player.update(0.05)

    assert player.heading == 90.0
    assert player.node.heading == 90.0


def test_player_idle_pose_has_subtle_motion() -> None:
    player = _player_with_fake_nodes()

    player.update(0.5)

    assert player.idle_time == 0.5
    assert player.parts["body"].hpr != (0.0, 0.0, 0.0)
    assert player.parts["head"].hpr != (0.0, 0.0, 0.0)


def test_player_combat_styles_use_distinct_action_poses() -> None:
    poses: dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]] = {}
    for action_type in ("combat_attack", "combat_strength", "combat_defence", "combat_ranged", "combat_magic"):
        player = _player_with_fake_nodes()
        player.start_action_animation(action_type)
        poses[action_type] = (player.parts["right_arm"].hpr, player.parts["tool"].hpr)

    assert len(set(poses.values())) == len(poses)


def test_player_combat_action_clip_applies_when_available(monkeypatch) -> None:
    clip_parts = {
        part: {"base": [0.0, 0.0, 0.0], "amplitude": [0.0, 0.0, 0.0], "speed": 0.0}
        for part in ("left_leg", "right_leg", "left_arm", "right_arm", "body", "head", "tool")
    }
    clip_parts["body"] = {"base": [1.0, 2.0, 3.0], "amplitude": [0.0, 0.0, 0.0], "speed": 0.0}
    clip_parts["right_arm"] = {"base": [4.0, 5.0, 6.0], "amplitude": [0.0, 0.0, 0.0], "speed": 0.0}
    clip_parts["tool"] = {"base": [-7.0, -8.0, -9.0], "amplitude": [0.0, 0.0, 0.0], "speed": 0.0}
    clip = {"name": "player_combat_attack", "parts": clip_parts}

    monkeypatch.setattr(
        player_module,
        "load_animation_clip_data",
        lambda asset_name: clip if asset_name == "player_combat_attack" else None,
    )

    player = _player_with_fake_nodes()
    player.start_action_animation("combat_attack")

    assert tuple(round(value, 3) for value in player.parts["body"].hpr) == (1.0, 2.0, 3.0)
    assert tuple(round(value, 3) for value in player.parts["right_arm"].hpr) == (4.0, 5.0, 6.0)
    assert tuple(round(value, 3) for value in player.parts["tool"].hpr) == (-7.0, -8.0, -9.0)


def test_player_combat_reaction_falls_back_and_clears_without_clip(monkeypatch) -> None:
    monkeypatch.setattr(player_module, "load_animation_clip_data", lambda _asset_name: None)

    player = _player_with_fake_nodes()
    player.start_action_animation("combat_reaction")

    assert player.action_animation == "combat_reaction"
    assert player.parts["body"].hpr != (0.0, 0.0, 0.0)

    player.update(0.31)

    assert player.action_animation is None


def test_player_render_falls_back_when_model_loading_misses(monkeypatch) -> None:
    monkeypatch.setattr(visuals, "load_model", lambda _asset_name: None)
    monkeypatch.setattr(player_module, "load_animation_clip_data", lambda _asset_name: None)

    player = Player(TileGrid(4, 4), (1, 1))
    player.render(NodePath("parent"))

    required_parts = {"left_leg", "right_leg", "left_arm", "right_arm", "body", "head", "tool"}
    assert required_parts.issubset(player.parts)


def test_player_idle_clip_applies_when_available(monkeypatch) -> None:
    clip_parts = {
        part: {"base": [0.0, 0.0, 0.0], "amplitude": [0.0, 0.0, 0.0], "speed": 0.0}
        for part in ("left_leg", "right_leg", "left_arm", "right_arm", "body", "head", "tool")
    }
    clip_parts["body"] = {
        "base": [1.0, 2.0, 3.0],
        "amplitude": [4.0, 5.0, 6.0],
        "speed": 0.0,
        "phase": math.pi / 2.0,
    }
    clip = {"name": "player_idle", "parts": clip_parts}

    monkeypatch.setattr(player_module, "load_animation_clip_data", lambda asset_name: clip if asset_name == "player_idle" else None)
    monkeypatch.setattr(visuals, "load_model", lambda _asset_name: None)

    player = Player(TileGrid(4, 4), (1, 1))
    player.render(NodePath("parent"))
    player.update(0.0)

    assert tuple(round(value, 3) for value in player.parts["body"].getHpr()) == (5.0, 7.0, 9.0)


def test_player_click_movement_uses_slower_walk_speed() -> None:
    player = _player_with_fake_nodes()

    player.set_path([(1, 1), (1, 2)])
    player.update(0.25)

    assert player.tile == (1, 1)
    assert player.path == [(1, 2)]
    assert round(player.y, 2) == 2.25


def _player_with_fake_nodes() -> Player:
    player = Player(TileGrid(4, 4), (1, 1))
    player.node = _FakeNode()
    player.parts = {
        key: _FakeNode()
        for key in ("left_leg", "right_leg", "left_arm", "right_arm", "body", "head", "tool")
    }
    return player


class _FakeNode:
    def __init__(self) -> None:
        self.hpr = (0.0, 0.0, 0.0)
        self.pos = (0.0, 0.0, 0.0)
        self.heading = 0.0

    def setHpr(self, h: float, p: float, r: float) -> None:
        self.hpr = (round(h, 3), round(p, 3), round(r, 3))

    def setP(self, p: float) -> None:
        self.hpr = (self.hpr[0], round(p, 3), self.hpr[2])

    def setPos(self, *args: object) -> None:
        if len(args) == 1:
            value = args[0]
            self.pos = (round(float(value[0]), 3), round(float(value[1]), 3), round(float(value[2]), 3))  # type: ignore[index]
        elif len(args) == 3:
            self.pos = (round(float(args[0]), 3), round(float(args[1]), 3), round(float(args[2]), 3))

    def setH(self, h: float) -> None:
        self.heading = round(h, 3)
