from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

from panda3d.core import Filename, ModelPool, NodePath, PNMImage, Texture, TexturePool, TextureStage

ASSETS_DIR = Path(__file__).resolve().parent
AUDIO_DIR = ASSETS_DIR / "audio"
TEXTURES_DIR = ASSETS_DIR / "textures"
MODELS_DIR = ASSETS_DIR / "models"
ANIMATIONS_DIR = ASSETS_DIR / "animations"

_SURFACE_STAGE = TextureStage("surface")
_AUDIO_EXTENSIONS = (".wav", ".ogg", ".mp3", ".flac")
_TEXTURE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".dds", ".tga")
_MODEL_EXTENSIONS = (".bam", ".egg", ".pz", ".glb", ".gltf")
_ANIMATION_EXTENSIONS = (".json", ".bam", ".egg", ".chan", ".glb", ".gltf")


def load_texture(asset_name: str) -> Texture | None:
    path = _resolve_asset_path(TEXTURES_DIR, asset_name, _TEXTURE_EXTENSIONS)
    if path is None:
        return None
    texture = TexturePool.loadTexture(Filename.fromOsSpecific(str(path)))
    if texture is None:
        return None
    _configure_texture(texture)
    return texture


def load_model(asset_name: str) -> NodePath | None:
    path = _resolve_asset_path(MODELS_DIR, asset_name, _MODEL_EXTENSIONS)
    if path is None:
        return None
    model = ModelPool.loadModel(Filename.fromOsSpecific(str(path)))
    if model is None:
        return None
    if isinstance(model, NodePath):
        return model
    return NodePath(model)


def load_animation_clip(asset_name: str) -> Path | None:
    return _resolve_asset_path(ANIMATIONS_DIR, asset_name, _ANIMATION_EXTENSIONS)


def load_sound(asset_name: str) -> Path | None:
    return _resolve_asset_path(AUDIO_DIR, asset_name, _AUDIO_EXTENSIONS)


@lru_cache(maxsize=None)
def load_animation_clip_data(asset_name: str) -> dict[str, object] | None:
    path = load_animation_clip(asset_name)
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def apply_surface_texture(node: NodePath, surface: str, variant: int = 0) -> None:
    node.setTexture(_SURFACE_STAGE, get_surface_texture(surface, variant))


@lru_cache(maxsize=None)
def get_surface_texture(surface: str, variant: int = 0) -> Texture:
    external = _load_external_surface_texture(surface, variant)
    if external is not None:
        return external
    return _build_surface_texture(surface, variant)


def _load_external_surface_texture(surface: str, variant: int) -> Texture | None:
    surface = _normalize_asset_name(surface)
    candidates = []
    if variant > 0:
        candidates.extend(
            (
                f"{surface}_{variant}",
                f"{surface}-{variant}",
                f"{surface}/{variant}",
            )
        )
    candidates.append(surface)
    for candidate in candidates:
        texture = load_texture(candidate)
        if texture is not None:
            return texture
    return None


def _build_surface_texture(surface: str, variant: int) -> Texture:
    family, base, accent, highlight, alpha = _surface_palette(surface)
    seed = _seed(surface, variant)
    image = PNMImage(48, 48, 4)
    for y in range(image.getYSize()):
        for x in range(image.getXSize()):
            color = _sample_surface_color(family, base, accent, highlight, alpha, seed, x, y)
            image.setXelA(x, y, *color)
    texture = Texture()
    if not texture.load(image):
        raise RuntimeError(f"Failed to build procedural texture for {surface!r}")
    _configure_texture(texture)
    return texture


def _sample_surface_color(
    family: str,
    base: tuple[float, float, float],
    accent: tuple[float, float, float],
    highlight: tuple[float, float, float],
    alpha: float,
    seed: int,
    x: int,
    y: int,
) -> tuple[float, float, float, float]:
    noise = _noise(seed, x, y)
    fine = _noise(seed ^ 0x9E3779B9, x * 3 + 7, y * 3 + 11)
    mix = 0.18 + noise * 0.52
    color = _lerp_color(base, accent, mix)

    if family == "grass":
        blade = math.sin((x + seed % 9) * 0.55) * 0.035 + math.cos((y + seed % 13) * 0.42) * 0.025
        color = _shift_brightness(color, blade + (fine - 0.5) * 0.08)
        if noise > 0.79:
            color = _lerp_color(color, highlight, (noise - 0.79) / 0.21)
    elif family == "water":
        wave = math.sin((x + seed % 17) * 0.55) * 0.05 + math.cos((y + seed % 11) * 0.50) * 0.06
        color = _shift_brightness(color, wave + (fine - 0.5) * 0.06)
        if noise > 0.70:
            color = _lerp_color(color, highlight, (noise - 0.70) / 0.30)
    elif family == "wood":
        grain = math.sin((x + seed % 19) * 0.70) * 0.07 + math.sin((y + seed % 5) * 0.35) * 0.03
        color = _shift_brightness(color, grain + (fine - 0.5) * 0.05)
        if noise > 0.84:
            color = _lerp_color(color, highlight, (noise - 0.84) / 0.16)
    elif family == "stone":
        grain = (noise - 0.5) * 0.22 + math.sin((x + seed % 7) * 0.25) * 0.03
        color = _shift_brightness(color, grain + (fine - 0.5) * 0.06)
        if noise > 0.86:
            color = _lerp_color(color, highlight, (noise - 0.86) / 0.14)
    elif family == "cloth":
        weave = ((x // 3 + y // 4 + seed) % 2) * 0.06 - 0.03
        color = _shift_brightness(color, weave + (fine - 0.5) * 0.04)
        if noise > 0.82:
            color = _lerp_color(color, highlight, (noise - 0.82) / 0.18)
    elif family == "skin":
        softness = (noise - 0.5) * 0.08 + (fine - 0.5) * 0.03
        color = _shift_brightness(color, softness)
        if noise > 0.90:
            color = _lerp_color(color, highlight, (noise - 0.90) / 0.10)
    elif family == "metal":
        brush = math.sin((x + y + seed % 23) * 0.35) * 0.05 + (fine - 0.5) * 0.05
        color = _shift_brightness(color, brush)
        if noise > 0.78:
            color = _lerp_color(color, highlight, (noise - 0.78) / 0.22)
    elif family == "gold":
        shine = math.cos((x + seed % 11) * 0.45) * 0.08 + math.sin((y + seed % 7) * 0.25) * 0.04
        color = _shift_brightness(color, shine + (fine - 0.5) * 0.04)
        if noise > 0.72:
            color = _lerp_color(color, highlight, (noise - 0.72) / 0.28)
    elif family == "bone":
        pock = (noise - 0.5) * 0.10 + (fine - 0.5) * 0.02
        color = _shift_brightness(color, pock)
        if noise > 0.88:
            color = _lerp_color(color, highlight, (noise - 0.88) / 0.12)
    elif family == "gel":
        blob = math.sin((x + seed % 13) * 0.50) * 0.05 + math.cos((y + seed % 17) * 0.42) * 0.05
        color = _shift_brightness(color, blob + (fine - 0.5) * 0.06)
        if noise > 0.84:
            color = _lerp_color(color, highlight, (noise - 0.84) / 0.16)
    elif family == "organic":
        fur = math.sin((x + seed % 15) * 0.65) * 0.03 + (noise - 0.5) * 0.12
        color = _shift_brightness(color, fur + (fine - 0.5) * 0.04)
        if noise > 0.83:
            color = _lerp_color(color, highlight, (noise - 0.83) / 0.17)
    elif family == "spark":
        pulse = math.sin((x + y + seed % 19) * 0.30) * 0.05 + math.cos((x - y + seed % 13) * 0.20) * 0.04
        color = _shift_brightness(color, pulse + (fine - 0.5) * 0.05)
        if noise > 0.76:
            color = _lerp_color(color, highlight, (noise - 0.76) / 0.24)
    else:
        color = _shift_brightness(color, (noise - 0.5) * 0.10)

    return _clamp_color((*color, alpha))


def _surface_palette(surface: str) -> tuple[str, tuple[float, float, float], tuple[float, float, float], tuple[float, float, float], float]:
    name = _normalize_asset_name(surface)
    if "water" in name or "shimmer" in name or "foam" in name:
        return "water", (0.10, 0.33, 0.55), (0.16, 0.48, 0.74), (0.74, 0.92, 1.0), 1.0
    if "grass" in name or "leaf" in name or "moss" in name or "organic" in name:
        return "grass", (0.18, 0.34, 0.12), (0.28, 0.48, 0.18), (0.56, 0.70, 0.28), 1.0
    if "dirt" in name or "sand" in name or "shore" in name:
        return "stone", (0.40, 0.26, 0.14), (0.52, 0.36, 0.18), (0.76, 0.56, 0.30), 1.0
    if "wood" in name or "bark" in name or "plank" in name or "branch" in name or "trunk" in name or "root" in name:
        return "wood", (0.34, 0.20, 0.10), (0.50, 0.32, 0.16), (0.76, 0.58, 0.30), 1.0
    if "cloth" in name or "tunic" in name or "sleeve" in name or "skirt" in name or "robe" in name or "sash" in name:
        return "cloth", (0.43, 0.28, 0.20), (0.60, 0.42, 0.30), (0.86, 0.76, 0.64), 1.0
    if "skin" in name or "hand" in name or "head" in name or "nose" in name or "leg" in name:
        return "skin", (0.68, 0.48, 0.38), (0.80, 0.60, 0.48), (0.95, 0.78, 0.66), 1.0
    if "leather" in name or "boot" in name or "belt" in name or "cuff" in name or "pouch" in name:
        return "wood", (0.24, 0.16, 0.10), (0.34, 0.22, 0.14), (0.52, 0.36, 0.20), 1.0
    if "bone" in name or "skull" in name or "tooth" in name:
        return "bone", (0.72, 0.68, 0.56), (0.84, 0.80, 0.68), (0.96, 0.92, 0.84), 1.0
    if "gold" in name or "coin" in name:
        return "gold", (0.66, 0.50, 0.08), (0.82, 0.66, 0.16), (1.0, 0.92, 0.42), 1.0
    if "metal" in name or "blade" in name or "rivet" in name or "buckle" in name or "band" in name:
        return "metal", (0.28, 0.30, 0.34), (0.46, 0.48, 0.52), (0.82, 0.86, 0.90), 1.0
    if "spark" in name or "glow" in name or "orb" in name:
        return "spark", (0.20, 0.38, 0.64), (0.44, 0.72, 0.96), (0.92, 0.98, 1.0), 1.0
    if "gel" in name or "slime" in name or "blob" in name:
        return "gel", (0.14, 0.42, 0.20), (0.20, 0.66, 0.30), (0.74, 0.98, 0.78), 0.96
    if "ore_copper" in name or "copper" in name:
        return "metal", (0.34, 0.16, 0.10), (0.64, 0.30, 0.14), (0.92, 0.52, 0.22), 1.0
    if "ore_tin" in name or "tin" in name:
        return "metal", (0.36, 0.38, 0.38), (0.58, 0.60, 0.58), (0.88, 0.90, 0.88), 1.0
    if "ore_iron" in name or "iron" in name:
        return "metal", (0.28, 0.18, 0.12), (0.50, 0.30, 0.18), (0.74, 0.46, 0.24), 1.0
    if "ore_coal" in name or "coal" in name:
        return "stone", (0.08, 0.08, 0.10), (0.18, 0.18, 0.20), (0.30, 0.30, 0.34), 1.0
    if "ore_mithril" in name or "mithril" in name:
        return "metal", (0.10, 0.24, 0.42), (0.18, 0.40, 0.66), (0.42, 0.74, 0.98), 1.0
    if "ore_adamant" in name or "adamant" in name:
        return "metal", (0.10, 0.34, 0.20), (0.22, 0.56, 0.34), (0.56, 0.86, 0.42), 1.0
    if "ore_starsteel" in name or "starsteel" in name:
        return "metal", (0.20, 0.34, 0.48), (0.36, 0.58, 0.78), (0.76, 0.92, 1.0), 1.0
    return "stone", (0.28, 0.28, 0.30), (0.40, 0.40, 0.42), (0.76, 0.76, 0.80), 1.0


def _resolve_asset_path(root: Path, asset_name: str, extensions: tuple[str, ...]) -> Path | None:
    candidate = Path(asset_name)
    if candidate.is_absolute():
        return candidate if candidate.is_file() else None

    if candidate.suffix:
        direct = root / candidate
        if direct.is_file():
            return direct
    else:
        direct = root / candidate
        if direct.is_file():
            return direct
        for extension in extensions:
            suffixed = root / candidate.with_suffix(extension)
            if suffixed.is_file():
                return suffixed

    if candidate.suffix:
        for extension in extensions:
            suffixed = root / candidate.with_suffix(extension)
            if suffixed.is_file():
                return suffixed
    return None


def _configure_texture(texture: Texture) -> None:
    texture.setWrapU(Texture.WM_repeat)
    texture.setWrapV(Texture.WM_repeat)
    texture.setMinfilter(Texture.FTLinearMipmapLinear)
    texture.setMagfilter(Texture.FTLinear)


def _normalize_asset_name(asset_name: str) -> str:
    return asset_name.replace("\\", "/").strip().lower()


def _seed(surface: str, variant: int) -> int:
    value = variant * 0x45D9F3B
    for char in _normalize_asset_name(surface):
        value = ((value << 5) - value + ord(char)) & 0xFFFFFFFF
    return value & 0xFFFFFFFF


def _noise(seed: int, x: int, y: int) -> float:
    value = (seed ^ (x * 0x9E3779B1) ^ (y * 0x85EBCA77)) & 0xFFFFFFFF
    value ^= value >> 16
    value = (value * 0x7FEB352D) & 0xFFFFFFFF
    value ^= value >> 15
    return (value & 0xFFFFFFFF) / 0xFFFFFFFF


def _lerp_color(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    factor: float,
) -> tuple[float, float, float]:
    factor = max(0.0, min(1.0, factor))
    return tuple(a[index] + (b[index] - a[index]) * factor for index in range(3))


def _shift_brightness(color: tuple[float, float, float], factor: float) -> tuple[float, float, float]:
    return _clamp_color(tuple(channel + factor for channel in color) + (1.0,))[:3]


def _clamp_color(color: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return tuple(max(0.0, min(1.0, channel)) for channel in color)  # type: ignore[return-value]
