# Asset Pipeline

Drop license-safe assets here.

- `textures/`: optional PNG/JPG/BMP textures
- `models/`: optional Panda3D-ready models (`.bam`, `.egg`, `.glb`, `.gltf`)
- `animations/`: optional animation clips or source files

Provenance for the committed texture batch:

- `grass.png`: self-authored RGBA tile texture for grassy ground.
- `dirt.png`: self-authored RGBA tile texture for packed dirt.
- `water.png`: self-authored RGBA tile texture for water surfaces.
- `wood.png`: self-authored RGBA tile texture for planks and bark.
- `stone.png`: self-authored RGBA tile texture for stone and rock surfaces.
- `cloth.png`: self-authored RGBA tile texture for clothing and fabric.
- `skin.png`: self-authored RGBA tile texture for skin-toned surfaces.
- `organic.png`: self-authored RGBA tile texture for mossy or living surfaces.
- `bone.png`: self-authored RGBA tile texture for bones and ivory surfaces.
- `metal.png`: self-authored RGBA tile texture for metal surfaces.
- `gel.png`: self-authored RGBA tile texture for slime and gel surfaces.
- `gold.png`: self-authored RGBA tile texture for gold and coin surfaces.

Provenance for the committed model batch:

- `tree.egg`: self-authored low-poly tree silhouette for woodcutting scenes.
- `rock.egg`: self-authored low-poly rock silhouette for mining scenes.
- `player.egg`: self-authored low-poly player rig with named animation parts.
- `npc.egg`: self-authored low-poly NPC silhouette for towns and quests.
- `mob.egg`: self-authored low-poly hostile creature silhouette for combat.

Provenance for the committed animation batch:

- `player_idle.json`: self-authored player idle motion profile for the rig.
- `player_walk.json`: self-authored player walk motion profile for the rig.
- `npc_mob_idle.json`: self-authored shared idle motion profile for NPCs and mobs.

Provenance for the committed combat animation batch:

- `player_combat_attack.json`: self-authored player attack motion profile for the rig.
- `player_combat_strength.json`: self-authored player strength attack motion profile for the rig.
- `player_combat_defence.json`: self-authored player defensive combat motion profile for the rig.
- `player_combat_ranged.json`: self-authored player ranged combat motion profile for the rig.
- `player_combat_magic.json`: self-authored player magic combat motion profile for the rig.
- `player_combat_reaction.json`: self-authored player hit reaction motion profile for the rig.
- `npc_mob_combat_response.json`: self-authored shared combat response motion profile for NPCs and mobs.

Provenance for the committed VFX texture batch:

- `flash.png`: self-authored RGBA flash overlay for hit and spell bursts.
- `impact.png`: self-authored RGBA impact overlay for projectile and hit effects.
- `spark.png`: self-authored RGBA spark overlay for projectile and magic effects.
- `dust.png`: self-authored RGBA dust overlay for depletion and debris effects.
- `respawn.png`: self-authored RGBA respawn glow overlay for resource return feedback.

Provenance for the committed audio batch:

- `ambient.wav`: self-authored looping ambient bed for optional runtime playback.

If an asset is missing, the game falls back to procedural textures and the existing procedural geometry.

Do not add ripped or near-branded RuneScape assets here.
