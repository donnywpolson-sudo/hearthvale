from __future__ import annotations

from game.engine.camera import CameraState, GameCamera


class FakeCamera:
    def __init__(self) -> None:
        self.position: tuple[float, float, float] | None = None
        self.target = None

    def setPos(self, x: float, y: float, z: float) -> None:
        self.position = (x, y, z)

    def lookAt(self, target) -> None:
        self.target = target


def test_camera_input_clamps_to_loaded_world_bounds() -> None:
    state = CameraState(center_x=99.0, center_y=99.0, heading=0.0, zoom=22.0)
    camera = GameCamera(FakeCamera(), state, bounds_width=100, bounds_height=100)

    camera.update_from_input({"w": True, "d": True}, dt=10.0)

    assert state.center_x == 100.0
    assert state.center_y == 100.0


def test_camera_load_clamps_saved_position_to_loaded_world_bounds() -> None:
    state = CameraState(center_x=15.0, center_y=15.0, heading=45.0, zoom=22.0)
    camera = GameCamera(FakeCamera(), state, bounds_width=100, bounds_height=100)

    camera.load_dict({"center_x": 140.0, "center_y": -10.0, "heading": 90.0, "zoom": 20.0})

    assert state.center_x == 100.0
    assert state.center_y == 0.0
    assert state.heading == 90.0
    assert state.zoom == 20.0
