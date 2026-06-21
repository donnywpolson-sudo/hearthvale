from __future__ import annotations

from game.systems.combat import CombatSystem, DropStack, MobDefinition
from game.systems.skills import Skills, skill_xp_thresholds
from game.world.grid import TileGrid


class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class FixedRng:
    def __init__(self, random_value: float = 0.0, damage: int = 1) -> None:
        self.random_value = random_value
        self.damage = damage

    def random(self) -> float:
        return self.random_value

    def randint(self, _lower: int, upper: int) -> int:
        return min(self.damage, upper)


def test_combat_auto_attacks_until_mob_dies_and_respawns() -> None:
    clock = FakeClock()
    system = CombatSystem([_mob()], time_provider=clock, rng=FixedRng())
    grid = TileGrid(5, 5)

    started = system.start_attack("mob_01", (1, 2), grid, set())

    assert started.success is True
    assert started.pending is True
    assert started.feedback == "Attacking Test sentry: 2/2 HP; you: 10/10 HP; 1.0s"

    clock.now += 1.0
    first_hit = system.update()

    assert first_hit is not None
    assert first_hit.pending is True
    assert first_hit.killed is False
    assert system.states["mob_01"].hitpoints == 1

    clock.now += 1.0
    killed = system.update()

    assert killed is not None
    assert killed.killed is True
    assert killed.drops == (DropStack("coins", 3), DropStack("wooden_splinters", 1))
    assert system.is_dead("mob_01") is True

    clock.now += 5.0
    system.refresh_all()

    assert system.is_dead("mob_01") is False
    assert system.to_dict() == {}


def test_combat_state_round_trip_preserves_dead_mob() -> None:
    clock = FakeClock()
    system = CombatSystem([_mob()], time_provider=clock, rng=FixedRng())
    grid = TileGrid(5, 5)
    system.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 2.0
    assert system.update() is not None
    clock.now += 2.0
    assert system.update() is not None

    loaded = CombatSystem([_mob()], time_provider=clock)
    loaded.load_dict(system.to_dict())

    assert loaded.is_dead("mob_01") is True


def test_combat_damages_player_grants_xp_and_can_heal() -> None:
    clock = FakeClock()
    skills = Skills(_skills())
    system = CombatSystem([_mob(hitpoints=3, level=3)], skills=skills, time_provider=clock, rng=FixedRng())
    grid = TileGrid(5, 5)

    system.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 1.0
    result = system.update()

    assert result is not None
    assert result.enemy_damage == 1
    assert result.feedback == "Hit Test sentry: 2/3 HP left; Test sentry hit you for 1; you: 9/10 HP"
    assert system.current_hitpoints == 9
    assert skills.xp("attack") == 4
    assert skills.xp("strength") == 0
    assert skills.xp("defence") == 0
    assert skills.xp("hitpoints") == 1

    assert system.heal(3) == 1
    assert system.current_hitpoints == 10


def test_combat_training_style_controls_combat_xp() -> None:
    clock = FakeClock()
    skills = Skills(_skills())
    system = CombatSystem([_mob(hitpoints=3, level=1)], skills=skills, time_provider=clock, rng=FixedRng())
    system.set_training_style("strength")
    grid = TileGrid(5, 5)

    system.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 1.0
    result = system.update()

    assert result is not None
    assert skills.xp("attack") == 0
    assert skills.xp("strength") == 4
    assert skills.xp("defence") == 0
    assert skills.xp("hitpoints") == 1


def test_combat_starting_attack_does_not_grant_instant_xp() -> None:
    clock = FakeClock()
    skills = Skills(_skills())
    system = CombatSystem([_mob(hitpoints=3, level=1)], skills=skills, time_provider=clock, rng=FixedRng())
    grid = TileGrid(5, 5)

    result = system.start_attack("mob_01", (1, 2), grid, set())

    assert result.pending is True
    assert skills.xp("attack") == 0
    assert skills.xp("hitpoints") == 0


def test_combat_miss_deals_no_damage_or_xp() -> None:
    clock = FakeClock()
    skills = Skills(_skills())
    system = CombatSystem([_mob(hitpoints=3, level=1)], skills=skills, time_provider=clock, rng=FixedRng(1.0))
    grid = TileGrid(5, 5)

    system.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 1.0
    result = system.update()

    assert result is not None
    assert result.player_damage == 0
    assert system.states["mob_01"].hitpoints == 3
    assert result.feedback == "Missed Test sentry: 3/3 HP left; Test sentry hit you for 1; you: 9/10 HP"
    assert skills.xp("attack") == 0
    assert skills.xp("hitpoints") == 0


def test_ranged_and_magic_styles_award_their_own_xp() -> None:
    clock = FakeClock()
    skills = Skills(_skills())
    ranged = CombatSystem([_mob(hitpoints=3, level=1)], skills=skills, time_provider=clock, rng=FixedRng())
    grid = TileGrid(5, 5)
    ranged.set_training_style("ranged")

    ranged.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 1.0
    result = ranged.update()

    assert result is not None
    assert result.combat_style == "ranged"
    assert skills.xp("ranged") == 4
    assert skills.xp("attack") == 0

    magic = CombatSystem([_mob(hitpoints=3, level=1)], skills=skills, time_provider=clock, rng=FixedRng())
    magic.set_training_style("magic")
    magic.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 1.0
    result = magic.update()

    assert result is not None
    assert result.combat_style == "magic"
    assert skills.xp("magic") == 4


def test_combat_range_depends_on_player_style_and_mob_range() -> None:
    clock = FakeClock()
    grid = TileGrid(8, 8)
    melee_mob = _mob(hitpoints=3, level=3, position=(1, 5), attack_range=1)
    system = CombatSystem([melee_mob], time_provider=clock, rng=FixedRng())

    too_far = system.start_attack("mob_01", (1, 1), grid, set())

    assert too_far.success is False
    assert too_far.feedback == "Too far away"

    system.set_training_style("ranged")
    started = system.start_attack("mob_01", (1, 1), grid, set())
    clock.now += 1.0
    result = system.update()

    assert started.pending is True
    assert result is not None
    assert result.player_damage == 1
    assert result.enemy_damage == 0
    assert system.current_hitpoints == 10

    ranged_mob = _mob(hitpoints=3, level=3, position=(1, 5), attack_range=4)
    ranged_enemy = CombatSystem([ranged_mob], time_provider=clock, rng=FixedRng())
    ranged_enemy.set_training_style("magic")
    ranged_enemy.start_attack("mob_01", (1, 1), grid, set())
    clock.now += 1.0
    result = ranged_enemy.update()

    assert result is not None
    assert result.enemy_damage == 1
    assert ranged_enemy.current_hitpoints == 9


def test_combat_reports_player_death() -> None:
    clock = FakeClock()
    system = CombatSystem([_mob(hitpoints=4, level=9)], current_hitpoints=2, time_provider=clock, rng=FixedRng())
    grid = TileGrid(5, 5)

    system.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 1.0
    result = system.update()

    assert result is not None
    assert result.player_dead is True
    assert result.feedback == "You were defeated by Test sentry; Test sentry: 3/4 HP; you: 0/10 HP"
    assert system.current_hitpoints == 0


def _mob(
    hitpoints: int = 2,
    level: int = 1,
    position: tuple[int, int] = (2, 2),
    attack_range: int = 1,
) -> MobDefinition:
    return MobDefinition(
        mob_id="mob_01",
        display_name="Test sentry",
        level=level,
        hitpoints=hitpoints,
        attack_seconds=1.0,
        respawn_seconds=5.0,
        position=position,
        drops=(DropStack("coins", 3), DropStack("wooden_splinters", 1)),
        attack_range=attack_range,
    )


def _skills() -> dict[str, dict[str, object]]:
    thresholds = skill_xp_thresholds()
    return {
        "attack": {"display_name": "Attack", "starting_level": 1, "xp_thresholds": thresholds},
        "strength": {"display_name": "Strength", "starting_level": 1, "xp_thresholds": thresholds},
        "defence": {"display_name": "Defence", "starting_level": 1, "xp_thresholds": thresholds},
        "ranged": {"display_name": "Ranged", "starting_level": 1, "xp_thresholds": thresholds},
        "magic": {"display_name": "Magic", "starting_level": 1, "xp_thresholds": thresholds},
        "hitpoints": {"display_name": "Hitpoints", "starting_level": 10, "xp_thresholds": thresholds},
    }
