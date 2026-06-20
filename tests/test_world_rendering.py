from __future__ import annotations

import math

from panda3d.core import NodePath

from game.world import visuals
from game.world.map import TERRAIN_CHUNK_SIZE, WorldMap


def test_large_world_render_chunks_terrain_and_keeps_interactives_live() -> None:
    world = WorldMap(
        {
            "width": 100,
            "height": 100,
            "blocked_tiles": [[4, 4]],
            "resource_nodes": [],
            "decorations": [
                {"id": "sign_01", "kind": "signpost", "position": [5, 5]},
            ],
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
    assert world.target_at((23, 15)) is shop

    sign = world.target_at((5, 5))
    assert sign is not None
    assert sign.object_id == "sign_01"
    assert sign.node is not None

    rocks = world.target_at((4, 4))
    assert rocks is not None
    assert rocks.object_id == "blocked_4_4"
    assert rocks.node is not None


def test_asset_renderer_hook_can_override_world_object_rendering() -> None:
    calls: list[tuple[str, str, int]] = []

    def render_shop_asset(holder, obj, _resource_node, _resource_state, tier) -> None:
        calls.append((holder.getName(), obj.object_id, tier))
        holder.attachNewNode("asset_marker")

    visuals.register_asset_renderer("shop", render_shop_asset)
    try:
        world = WorldMap(
            {
                "width": 4,
                "height": 4,
                "blocked_tiles": [],
                "resource_nodes": [],
                "shop": {"id": "shop_01", "name": "General Buyer", "tile": [1, 1]},
            }
        )
        parent = NodePath("test_render")

        world.render(parent)

        shop = world.get_object("shop_01")
        assert shop is not None
        assert calls == [("shop_01", "shop_01", 1)]
        assert shop.node.find("**/asset_marker").isEmpty() is False
    finally:
        visuals.register_asset_renderer("shop", None)
