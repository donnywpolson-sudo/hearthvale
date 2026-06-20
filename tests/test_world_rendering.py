from __future__ import annotations

import math

from panda3d.core import NodePath

from game.world.map import TERRAIN_CHUNK_SIZE, WorldMap


def test_large_world_render_chunks_terrain_and_keeps_interactives_live() -> None:
    world = WorldMap(
        {
            "width": 100,
            "height": 100,
            "blocked_tiles": [],
            "resource_nodes": [],
            "shop": {"id": "shop_01", "name": "General Buyer", "tile": [23, 15]},
        }
    )
    parent = NodePath("test_render")

    world.render(parent)

    expected_chunks = math.ceil(100 / TERRAIN_CHUNK_SIZE) ** 2
    assert len(world.terrain_chunks) == expected_chunks
    assert all(chunk.getName().startswith("terrain_chunk_") for chunk in world.terrain_chunks)

    shop = world.get_object("shop_01")
    assert shop is not None
    assert shop.node is not None
    assert shop.node.getParent().getName() == "world"
    assert world.object_at((23, 15)) is shop
