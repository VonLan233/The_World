"""Default world seed data — creates 'Starter Town' with six locations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from the_world.models.world import Location, World

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Starter Town definition
# ---------------------------------------------------------------------------

STARTER_TOWN_NAME = "Starter Town"

_LOCATIONS: list[dict] = [
    {
        "name": "Home",
        "location_type": "home",
        "description": "A cozy little house — rest, eat, and recharge.",
        "position_x": 100.0,
        "position_y": 300.0,
        "capacity": 4,
        "available_activities": [
            "eat", "sleep", "nap", "shower", "relax",
            "watch_tv", "cook", "work", "read", "use_bathroom",
        ],
    },
    {
        "name": "Central Park",
        "location_type": "park",
        "description": "A lush green park in the centre of town.",
        "position_x": 400.0,
        "position_y": 150.0,
        "capacity": 20,
        "available_activities": [
            "exercise", "chat", "hangout", "meditate",
            "garden", "relax", "nap", "read",
        ],
    },
    {
        "name": "Cozy Cafe",
        "location_type": "restaurant",
        "description": "A warm café with great coffee and pastries.",
        "position_x": 650.0,
        "position_y": 300.0,
        "capacity": 12,
        "available_activities": [
            "eat", "chat", "read", "study", "use_bathroom",
        ],
    },
    {
        "name": "Public Library",
        "location_type": "library",
        "description": "Shelves upon shelves of books and quiet corners.",
        "position_x": 400.0,
        "position_y": 450.0,
        "capacity": 15,
        "available_activities": [
            "read", "study", "relax", "use_bathroom",
        ],
    },
    {
        "name": "Fitness Center",
        "location_type": "gym",
        "description": "Stay fit! Treadmills, weights, and showers.",
        "position_x": 200.0,
        "position_y": 100.0,
        "capacity": 10,
        "available_activities": [
            "exercise", "shower", "use_bathroom",
        ],
    },
    {
        "name": "Game Lounge",
        "location_type": "entertainment",
        "description": "Arcade machines, board games, and big screens.",
        "position_x": 650.0,
        "position_y": 100.0,
        "capacity": 15,
        "available_activities": [
            "play_games", "hangout", "chat", "watch_tv", "use_bathroom",
        ],
    },
]


async def seed_default_world(db: AsyncSession, owner_id: uuid.UUID) -> World:
    """Create the default *Starter Town* world with six locations.

    Returns the created ``World`` ORM instance (already flushed, with an id).
    """
    world = World(
        name=STARTER_TOWN_NAME,
        description="A peaceful starter town with everything you need.",
        owner_id=owner_id,
        is_public=True,
        settings={
            "tickRate": 1000,
            "dayLength": 1440,
            "seasonLength": 28,
            "enableWeather": False,
            "enableRandomEvents": True,
            "difficultyModifier": 1.0,
        },
    )
    db.add(world)
    await db.flush()

    for loc_data in _LOCATIONS:
        loc = Location(
            world_id=world.id,
            **loc_data,
        )
        db.add(loc)

    await db.flush()
    await db.refresh(world)
    return world
