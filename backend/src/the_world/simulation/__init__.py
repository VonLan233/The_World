"""The World simulation engine — discrete-event character life simulation."""

from the_world.simulation.activities import ALL_ACTIVITIES, Activity, activities_for_location
from the_world.simulation.autonomy import choose_activity
from the_world.simulation.clock import GameClock
from the_world.simulation.engine import CharacterSim, SimulationEngine
from the_world.simulation.needs import NeedsManager
from the_world.simulation.world_seed import seed_default_world

__all__ = [
    "ALL_ACTIVITIES",
    "Activity",
    "CharacterSim",
    "GameClock",
    "NeedsManager",
    "SimulationEngine",
    "activities_for_location",
    "choose_activity",
    "seed_default_world",
]
