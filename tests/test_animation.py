from __future__ import annotations

import math

from game.world.animation import SceneAnimator


def test_loop_animation_stops_and_restores_node_state() -> None:
    animator = SceneAnimator()
    node = _FakeNode()

    animator.start_bob("action:bob", node, amplitude=0.50, speed=math.pi)
    animator.update(0.5)

    assert node.pos == (0.0, 0.0, 0.5)

    assert animator.stop_prefix("action:") == 1
    assert node.pos == (0.0, 0.0, 0.0)
    assert animator.active_keys() == set()


def test_one_shot_animation_finishes_and_restores() -> None:
    animator = SceneAnimator()
    node = _FakeNode()

    animator.start_recoil("fx:hit", node, direction=(1.0, 0.0, 0.0), distance=0.20, duration=0.2)
    animator.update(0.1)

    assert node.pos == (0.2, 0.0, 0.0)

    animator.update(0.1)

    assert node.pos == (0.0, 0.0, 0.0)
    assert animator.active_keys() == set()


def test_shake_animation_cancels_and_restores_position() -> None:
    animator = SceneAnimator()
    node = _FakeNode()

    animator.start_shake("action:shake", node, amplitude=0.50, speed=math.pi)
    animator.update(0.5)

    assert node.pos[0] == 0.5

    assert animator.stop("action:shake")
    assert node.pos == (0.0, 0.0, 0.0)


def test_burst_animation_finishes_and_restores_scale_and_color() -> None:
    animator = SceneAnimator()
    node = _FakeNode()

    animator.start_burst("fx:burst", node, amplitude=0.50, color=(1.5, 1.2, 0.8, 1.0), duration=0.2)
    animator.update(0.1)

    assert node.scale == (1.5, 1.5, 1.5)
    assert node.color_scale != (1.0, 1.0, 1.0, 1.0)

    animator.update(0.1)

    assert node.scale == (1.0, 1.0, 1.0)
    assert node.color_scale == (1.0, 1.0, 1.0, 1.0)
    assert animator.active_keys() == set()


def test_spark_animation_can_remove_temporary_node() -> None:
    animator = SceneAnimator()
    node = _FakeNode()

    animator.start_spark("fx:spark", node, duration=0.1, remove_on_finish=True)
    animator.update(0.1)

    assert node.removed is True
    assert animator.active_keys() == set()


def test_defeat_animation_removes_temporary_node() -> None:
    animator = SceneAnimator()
    node = _FakeNode()

    animator.start_defeat("fx:defeat", node, duration=0.1)
    animator.update(0.1)

    assert node.removed is True
    assert animator.active_keys() == set()


def test_float_text_animation_creates_and_removes_temporary_text() -> None:
    from panda3d.core import NodePath

    animator = SceneAnimator()
    target = NodePath("target")

    animator.start_float_text("fx:damage", target, text="-2", duration=0.1)

    assert target.find("**/fx:damage:text").isEmpty() is False

    animator.update(0.1)

    assert target.find("**/fx:damage:text").isEmpty() is True
    assert animator.active_keys() == set()


class _FakeNode:
    def __init__(self) -> None:
        self.pos = (0.0, 0.0, 0.0)
        self.hpr = (0.0, 0.0, 0.0)
        self.scale = (1.0, 1.0, 1.0)
        self.color_scale = (1.0, 1.0, 1.0, 1.0)
        self.removed = False

    def getPos(self) -> tuple[float, float, float]:
        return self.pos

    def setPos(self, x: float, y: float, z: float) -> None:
        self.pos = (round(x, 3), round(y, 3), round(z, 3))

    def getHpr(self) -> tuple[float, float, float]:
        return self.hpr

    def setHpr(self, h: float, p: float, r: float) -> None:
        self.hpr = (round(h, 3), round(p, 3), round(r, 3))

    def getScale(self) -> tuple[float, float, float]:
        return self.scale

    def setScale(self, x: float, y: float, z: float) -> None:
        self.scale = (round(x, 3), round(y, 3), round(z, 3))

    def getColorScale(self) -> tuple[float, float, float, float]:
        return self.color_scale

    def setColorScale(self, r: float, g: float, b: float, a: float) -> None:
        self.color_scale = (round(r, 3), round(g, 3), round(b, 3), round(a, 3))

    def removeNode(self) -> None:
        self.removed = True

    def isEmpty(self) -> bool:
        return self.removed
