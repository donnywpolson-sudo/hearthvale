from __future__ import annotations

import math
from dataclasses import dataclass

from panda3d.core import Vec3

from game import settings


@dataclass
class CameraState:
    center_x: float
    center_y: float
    heading: float
    zoom: float


class GameCamera:
    def __init__(
        self,
        camera,
        state: CameraState,
        *,
        bounds_width: float | None = None,
        bounds_height: float | None = None,
    ) -> None:
        self.camera = camera
        self.state = state
        self.bounds_width = bounds_width
        self.bounds_height = bounds_height

    def update_from_input(self, keys: dict[str, bool], dt: float) -> None:
        rad = math.radians(self.state.heading)
        forward_x = math.sin(rad)
        forward_y = math.cos(rad)
        right_x = math.cos(rad)
        right_y = -math.sin(rad)

        speed = settings.CAMERA_PAN_SPEED * dt
        if keys.get("w"):
            self._pan(forward_x * speed, forward_y * speed)
        if keys.get("s"):
            self._pan(-forward_x * speed, -forward_y * speed)
        if keys.get("d"):
            self._pan(right_x * speed, right_y * speed)
        if keys.get("a"):
            self._pan(-right_x * speed, -right_y * speed)
        if keys.get("q"):
            self.state.heading += settings.CAMERA_ROTATE_SPEED * dt
        if keys.get("e"):
            self.state.heading -= settings.CAMERA_ROTATE_SPEED * dt

        self.apply()

    def zoom(self, amount: float) -> None:
        self.state.zoom = max(
            settings.CAMERA_MIN_ZOOM,
            min(settings.CAMERA_MAX_ZOOM, self.state.zoom + amount),
        )
        self.apply()

    def apply(self) -> None:
        self._clamp_to_bounds()
        heading = math.radians(self.state.heading)
        pitch = math.radians(settings.CAMERA_PITCH_DEGREES)
        horizontal_distance = self.state.zoom * math.cos(pitch)
        height = self.state.zoom * math.sin(pitch)

        cam_x = self.state.center_x - math.sin(heading) * horizontal_distance
        cam_y = self.state.center_y - math.cos(heading) * horizontal_distance
        cam_z = height

        target = Vec3(self.state.center_x, self.state.center_y, 0.0)
        self.camera.setPos(cam_x, cam_y, cam_z)
        self.camera.lookAt(target)

    def _pan(self, dx: float, dy: float) -> None:
        self.state.center_x += dx
        self.state.center_y += dy

    def _clamp_to_bounds(self) -> None:
        self.state.center_x = _clamp_axis(self.state.center_x, self.bounds_width)
        self.state.center_y = _clamp_axis(self.state.center_y, self.bounds_height)

    def to_dict(self) -> dict[str, float]:
        return {
            "center_x": self.state.center_x,
            "center_y": self.state.center_y,
            "heading": self.state.heading,
            "zoom": self.state.zoom,
        }

    def load_dict(self, data: dict[str, float]) -> None:
        self.state.center_x = float(data.get("center_x", self.state.center_x))
        self.state.center_y = float(data.get("center_y", self.state.center_y))
        self.state.heading = float(data.get("heading", self.state.heading))
        self.state.zoom = float(data.get("zoom", self.state.zoom))
        self.apply()


def _clamp_axis(value: float, upper_bound: float | None) -> float:
    if upper_bound is None:
        return max(0.0, value)
    return max(0.0, min(float(upper_bound), value))
