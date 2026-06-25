from __future__ import annotations

import pytest

from panda3d.core import NodePath, Texture

from game.assets.runtime import (
    apply_surface_texture,
    get_surface_texture,
    load_animation_clip,
    load_animation_clip_data,
    load_model,
    load_sound,
    load_texture,
)


ASSET_NAMES = [
    "grass",
    "dirt",
    "water",
    "wood",
    "stone",
    "cloth",
    "skin",
    "organic",
    "bone",
    "metal",
    "gel",
    "gold",
]
VFX_NAMES = [
    "flash",
    "impact",
    "spark",
    "dust",
    "respawn",
]
MODEL_NAMES = [
    "tree",
    "rock",
    "player",
    "npc",
    "mob",
]
ANIMATION_NAMES = [
    "player_idle",
    "player_walk",
    "npc_mob_idle",
    "player_combat_attack",
    "player_combat_strength",
    "player_combat_defence",
    "player_combat_ranged",
    "player_combat_magic",
    "player_combat_reaction",
    "npc_mob_combat_response",
]
AUDIO_NAMES = [
    "ambient",
]


@pytest.mark.parametrize("asset_name", ASSET_NAMES)
def test_committed_surface_textures_load(asset_name: str) -> None:
    texture = load_texture(asset_name)

    assert isinstance(texture, Texture)
    assert texture.getFilename().getBasename() == f"{asset_name}.png"


def test_surface_texture_is_cached_and_applies_to_nodepath() -> None:
    texture = get_surface_texture("grass", 0)
    cached = get_surface_texture("grass", 0)

    assert isinstance(texture, Texture)
    assert texture is cached

    node = NodePath("probe")
    apply_surface_texture(node, "grass", 0)
    assert node.hasTexture() is True
    bound = node.getTexture()
    assert bound is not None
    assert bound.getFilename().getBasename() == "grass.png"


@pytest.mark.parametrize("asset_name", VFX_NAMES)
def test_committed_vfx_textures_load(asset_name: str) -> None:
    texture = load_texture(asset_name)

    assert isinstance(texture, Texture)
    assert texture.getFilename().getBasename() == f"{asset_name}.png"


def test_committed_vfx_surface_texture_is_cached_and_applies_to_nodepath() -> None:
    texture = get_surface_texture("respawn", 0)
    cached = get_surface_texture("respawn", 0)

    assert isinstance(texture, Texture)
    assert texture is cached

    node = NodePath("probe")
    apply_surface_texture(node, "respawn", 0)
    assert node.hasTexture() is True
    bound = node.getTexture()
    assert bound is not None
    assert bound.getFilename().getBasename() == "respawn.png"


@pytest.mark.parametrize("asset_name", ANIMATION_NAMES)
def test_committed_animation_clips_load(asset_name: str) -> None:
    path = load_animation_clip(asset_name)
    data = load_animation_clip_data(asset_name)

    assert path is not None
    assert path.name == f"{asset_name}.json"
    assert isinstance(data, dict)
    assert data is load_animation_clip_data(asset_name)
    assert data.get("name") == asset_name


@pytest.mark.parametrize("asset_name", AUDIO_NAMES)
def test_committed_audio_files_load(asset_name: str) -> None:
    path = load_sound(asset_name)

    assert path is not None
    assert path.name == f"{asset_name}.wav"


@pytest.mark.parametrize("asset_name", MODEL_NAMES)
def test_committed_models_load(asset_name: str) -> None:
    model = load_model(asset_name)

    assert isinstance(model, NodePath)
    assert model.find(f"**/{asset_name}_model").isEmpty() is False


def test_committed_model_copy_to_nodepath_binds_tree_model() -> None:
    model = load_model("tree")
    assert model is not None

    holder = NodePath("probe")
    copied = model.copyTo(holder)

    assert copied.getParent().getName() == "probe"
    assert holder.find("**/tree_model").isEmpty() is False


def test_player_model_exposes_required_rig_nodes() -> None:
    model = load_model("player")
    assert model is not None

    required_parts = ("left_leg", "right_leg", "left_arm", "right_arm", "body", "head", "tool")
    for part in required_parts:
        assert model.find(f"**/{part}").isEmpty() is False


def test_missing_assets_fall_back_cleanly() -> None:
    assert load_texture("missing_texture") is None
    assert load_model("missing_model") is None
    assert load_animation_clip("missing_clip") is None
