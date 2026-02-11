"""Tests for the SimulationEngine."""

import asyncio

import pytest

from the_world.simulation.engine import SimulationEngine


def test_engine_creation():
    engine = SimulationEngine(world_id="test-world")
    assert engine.world_id == "test-world"
    assert engine.paused is True
    assert engine.running is False
    assert len(engine.characters) == 0


def test_add_location():
    engine = SimulationEngine(world_id="test")
    engine.add_location("Home", "home", 100.0, 300.0, ["eat", "sleep"])
    assert "Home" in engine.locations
    assert engine._loc_name_to_type["Home"] == "home"


def test_add_character():
    engine = SimulationEngine(world_id="test")
    engine.add_location("Home", "home", 100.0, 300.0, ["eat", "sleep"])
    csim = engine.add_character("char-1", "Luna", {"openness": 0.9})
    assert "char-1" in engine.characters
    assert csim.name == "Luna"
    assert csim.current_location == "Home"


def test_remove_character():
    engine = SimulationEngine(world_id="test")
    engine.add_location("Home", "home", 100.0, 300.0)
    engine.add_character("char-1", "Luna", {})
    engine.remove_character("char-1")
    assert "char-1" not in engine.characters


def test_set_speed():
    engine = SimulationEngine(world_id="test")
    engine.set_speed(5.0)
    assert engine.time_scale == 5.0
    engine.set_speed(0.1)  # below minimum
    assert engine.time_scale == 0.25
    engine.set_speed(100.0)  # above maximum
    assert engine.time_scale == 10.0


def test_get_state():
    engine = SimulationEngine(world_id="test")
    engine.add_location("Home", "home", 100.0, 300.0)
    engine.add_character("c1", "Alice", {"openness": 0.5})
    state = engine.get_state()
    assert state["worldId"] == "test"
    assert state["paused"] is True
    assert len(state["characters"]) == 1
    assert state["characters"][0]["characterId"] == "c1"
    assert "clock" in state


@pytest.mark.asyncio
async def test_engine_start_stop():
    """Engine can start and stop without errors."""
    engine = SimulationEngine(world_id="test", tick_interval_s=0.05)
    engine.add_location("Home", "home", 100.0, 300.0, ["eat", "sleep", "relax"])
    engine.add_character("c1", "Alice", {"openness": 0.5})

    engine.start()
    assert engine.running is True
    assert engine.paused is False

    # Let it run a few ticks
    await asyncio.sleep(0.3)

    # Clock should have advanced
    assert engine.clock.tick > 0

    engine.stop()
    assert engine.running is False
