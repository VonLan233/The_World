"""Tests for simulation snapshot serialisation/deserialisation."""

import pytest

from the_world.simulation.engine import CharacterSim, SimulationEngine


# ---------------------------------------------------------------------------
# CharacterSim round-trip
# ---------------------------------------------------------------------------

class TestCharacterSimSnapshot:
    def _make_char(self) -> CharacterSim:
        csim = CharacterSim(
            id="char-1",
            name="Alice",
            personality={"openness": 0.8, "extraversion": 0.6},
        )
        csim.needs.hunger = 42.5
        csim.needs.energy = 88.0
        csim.needs.social = 30.0
        csim.needs.fun = 55.0
        csim.needs.hygiene = 72.3
        csim.needs.comfort = 61.0
        csim.current_activity = "cooking"
        csim.current_location = "Kitchen"
        csim.current_location_type = "kitchen"
        csim.position_x = 200.0
        csim.position_y = 450.0
        return csim

    def test_to_snapshot_fields(self) -> None:
        csim = self._make_char()
        snap = csim.to_snapshot()
        assert snap["id"] == "char-1"
        assert snap["name"] == "Alice"
        assert snap["personality"]["openness"] == 0.8
        assert snap["needs"]["hunger"] == 42.5
        assert snap["current_activity"] == "cooking"
        assert snap["current_location"] == "Kitchen"
        assert snap["position_x"] == 200.0

    def test_roundtrip(self) -> None:
        original = self._make_char()
        snap = original.to_snapshot()
        restored = CharacterSim.from_snapshot(snap)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.personality == original.personality
        assert restored.current_activity == original.current_activity
        assert restored.current_location == original.current_location
        assert restored.current_location_type == original.current_location_type
        assert restored.position_x == original.position_x
        assert restored.position_y == original.position_y

    def test_needs_roundtrip(self) -> None:
        original = self._make_char()
        snap = original.to_snapshot()
        restored = CharacterSim.from_snapshot(snap)

        assert restored.needs.hunger == original.needs.hunger
        assert restored.needs.energy == original.needs.energy
        assert restored.needs.social == original.needs.social
        assert restored.needs.fun == original.needs.fun
        assert restored.needs.hygiene == original.needs.hygiene
        assert restored.needs.comfort == original.needs.comfort


# ---------------------------------------------------------------------------
# SimulationEngine round-trip
# ---------------------------------------------------------------------------

class TestEngineSnapshot:
    def _make_engine(self) -> SimulationEngine:
        engine = SimulationEngine(world_id="world-1", time_scale=2.0)
        engine.add_location("Home", "home", 100, 300)
        engine.add_location("Park", "park", 400, 200)
        engine.add_character("c1", "Bob", {"openness": 0.5})
        engine.clock.advance(120)  # advance to tick 120
        return engine

    def test_to_snapshot_structure(self) -> None:
        engine = self._make_engine()
        snap = engine.to_snapshot()

        assert snap["tick"] == 120
        assert snap["time_scale"] == 2.0
        assert snap["paused"] is True
        assert "c1" in snap["characters"]
        assert "weather" in snap

    def test_restore_from_snapshot(self) -> None:
        engine = self._make_engine()
        # Modify a character's needs
        engine.characters["c1"].needs.hunger = 33.3
        snap = engine.to_snapshot()

        # Create a fresh engine and restore
        new_engine = SimulationEngine(world_id="world-1")
        new_engine.add_location("Home", "home", 100, 300)
        new_engine.restore_from_snapshot(snap)

        assert new_engine.clock.tick == 120
        assert new_engine.clock.hour == 2  # 120 minutes = 2 hours
        assert new_engine.time_scale == 2.0
        assert "c1" in new_engine.characters
        assert new_engine.characters["c1"].needs.hunger == 33.3
        assert new_engine.characters["c1"].name == "Bob"
