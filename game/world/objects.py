from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from panda3d.core import Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat
from panda3d.core import GeomVertexWriter, LineSegs, NodePath
from panda3d.core import TransparencyAttrib, Vec3

from game.world.grid import Tile

Color = tuple[float, float, float, float]


@dataclass
class WorldObject:
    object_id: str
    kind: str
    tile: Tile
    blocking: bool = True
    active: bool = True
    display_name: str = ""
    chopped: bool = False
    node_type: str = ""
    skill_id: str = ""
    required_level: int = 1
    level: int = 1
    hitpoints: int = 0
    max_hitpoints: int = 0
    xp_reward: int = 0
    item_reward: str = ""
    quantity_reward: int = 1
    item_id: str = ""
    quantity: int = 0
    quest_id: str = ""
    depleted_state: str = "depleted"
    respawn_seconds: float | None = None
    depleted: bool = False
    node: Any = None
    scenery: bool = False

    @property
    def is_interactable(self) -> bool:
        if not self.active:
            return False
        if self.scenery:
            return True
        return (
            self.kind in {
                "shop",
                "bank",
                "cooking_range",
                "combat_dummy",
                "mob",
                "ground_item",
                "furnace",
                "anvil",
                "npc",
            }
            or self.is_resource_node
            or self.depleted
        )

    @property
    def is_resource_node(self) -> bool:
        return bool(self.node_type and self.skill_id and self.item_reward)

    @property
    def node_id(self) -> str:
        return self.object_id


def make_box(name: str, size: tuple[float, float, float], color: Color) -> NodePath:
    sx, sy, sz = size
    hx, hy = sx / 2.0, sy / 2.0
    vertices = [
        (-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0),
        (-hx, -hy, sz), (hx, -hy, sz), (hx, hy, sz), (-hx, hy, sz),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    return _make_poly_node(name, vertices, faces, color)


def make_quad(name: str, size: float, color: Color) -> NodePath:
    vertices = [(0, 0, 0), (size, 0, 0), (size, size, 0), (0, size, 0)]
    return _make_poly_node(name, vertices, [(0, 1, 2, 3)], color)


def make_cylinder(name: str, radius: float, height: float, sides: int, color: Color) -> NodePath:
    vertices: list[tuple[float, float, float]] = []
    for z in (0.0, height):
        for index in range(sides):
            angle = math.tau * index / sides
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, z))

    bottom_center = len(vertices)
    vertices.append((0.0, 0.0, 0.0))
    top_center = len(vertices)
    vertices.append((0.0, 0.0, height))

    faces: list[tuple[int, ...]] = []
    for index in range(sides):
        nxt = (index + 1) % sides
        faces.append((index, nxt, sides + nxt, sides + index))
        faces.append((bottom_center, nxt, index))
        faces.append((top_center, sides + index, sides + nxt))
    return _make_poly_node(name, vertices, faces, color)


def make_cone(name: str, radius: float, height: float, sides: int, color: Color) -> NodePath:
    vertices: list[tuple[float, float, float]] = []
    for index in range(sides):
        angle = math.tau * index / sides
        vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, 0.0))
    tip = len(vertices)
    vertices.append((0.0, 0.0, height))
    center = len(vertices)
    vertices.append((0.0, 0.0, 0.0))

    faces: list[tuple[int, ...]] = []
    for index in range(sides):
        nxt = (index + 1) % sides
        faces.append((index, nxt, tip))
        faces.append((center, nxt, index))
    return _make_poly_node(name, vertices, faces, color)


def make_grid_lines(width: int, height: int, color: Color) -> NodePath:
    lines = LineSegs()
    lines.setColor(*color)
    lines.setThickness(1.0)
    z = 0.015
    for x in range(width + 1):
        lines.moveTo(x, 0, z)
        lines.drawTo(x, height, z)
    for y in range(height + 1):
        lines.moveTo(0, y, z)
        lines.drawTo(width, y, z)
    return NodePath(lines.create())


def _make_poly_node(
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    color: Color,
) -> NodePath:
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    normal_writer = GeomVertexWriter(vdata, "normal")
    color_writer = GeomVertexWriter(vdata, "color")

    tris = GeomTriangles(Geom.UHStatic)
    next_vertex = 0
    for face in faces:
        triangles: list[tuple[int, int, int]] = []
        if len(face) == 3:
            triangles.append((face[0], face[1], face[2]))
        elif len(face) == 4:
            a, b, c, d = face
            triangles.append((a, b, c))
            triangles.append((a, c, d))
        for a, b, c in triangles:
            normal = _triangle_normal(vertices[a], vertices[b], vertices[c])
            for vertex_index in (a, b, c):
                vertex_writer.addData3f(*vertices[vertex_index])
                normal_writer.addData3f(normal[0], normal[1], normal[2])
                color_writer.addData4f(*color)
            tris.addVertices(next_vertex, next_vertex + 1, next_vertex + 2)
            next_vertex += 3
    tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    path = NodePath(node)
    if color[3] < 1.0:
        path.setTransparency(TransparencyAttrib.MAlpha)
    return path


def _triangle_normal(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    c: tuple[float, float, float],
) -> Vec3:
    left = Vec3(b[0] - a[0], b[1] - a[1], b[2] - a[2])
    right = Vec3(c[0] - a[0], c[1] - a[1], c[2] - a[2])
    normal = left.cross(right)
    if normal.lengthSquared() <= 0.000001:
        return Vec3(0.0, 0.0, 1.0)
    normal.normalize()
    return normal
