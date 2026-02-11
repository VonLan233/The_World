"""Activity definitions — what characters can do and how it affects their needs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Activity:
    """A single activity a character can perform."""

    name: str
    duration_minutes: int
    need_effects: dict[str, float] = field(default_factory=dict)
    required_location_types: list[str] = field(default_factory=list)
    personality_affinity: dict[str, float] = field(default_factory=dict)
    description_template: str = ""

    def __hash__(self) -> int:
        return hash(self.name)


# ---------------------------------------------------------------------------
# Core activity catalogue
# ---------------------------------------------------------------------------

# Survival
EAT = Activity(
    name="eat",
    duration_minutes=30,
    need_effects={"hunger": 50.0},
    required_location_types=["home", "restaurant"],
    description_template="{name} is eating a meal",
)

SLEEP = Activity(
    name="sleep",
    duration_minutes=480,
    need_effects={"energy": 100.0},  # energy set to 100 via special handling
    required_location_types=["home"],
    description_template="{name} is sleeping",
)

NAP = Activity(
    name="nap",
    duration_minutes=60,
    need_effects={"energy": 30.0},
    required_location_types=["home", "park"],
    description_template="{name} is taking a nap",
)

# Hygiene
SHOWER = Activity(
    name="shower",
    duration_minutes=15,
    need_effects={"hygiene": 100.0},  # full restore
    required_location_types=["home", "gym"],
    description_template="{name} is taking a shower",
)

USE_BATHROOM = Activity(
    name="use_bathroom",
    duration_minutes=10,
    need_effects={"comfort": 20.0},
    required_location_types=["home", "restaurant", "library", "gym", "entertainment"],
    description_template="{name} is using the bathroom",
)

# Social
CHAT = Activity(
    name="chat",
    duration_minutes=20,
    need_effects={"social": 25.0},
    required_location_types=["park", "restaurant", "entertainment", "library"],
    personality_affinity={"extraversion": 0.6},
    description_template="{name} is chatting with someone",
)

HANGOUT = Activity(
    name="hangout",
    duration_minutes=45,
    need_effects={"social": 35.0, "fun": 15.0},
    required_location_types=["park", "restaurant", "entertainment"],
    personality_affinity={"extraversion": 0.7, "agreeableness": 0.4},
    description_template="{name} is hanging out",
)

# Entertainment
READ = Activity(
    name="read",
    duration_minutes=30,
    need_effects={"fun": 20.0},
    required_location_types=["home", "library", "park", "restaurant"],
    personality_affinity={"openness": 0.6},
    description_template="{name} is reading a book",
)

WATCH_TV = Activity(
    name="watch_tv",
    duration_minutes=45,
    need_effects={"fun": 30.0},
    required_location_types=["home", "entertainment"],
    description_template="{name} is watching TV",
)

PLAY_GAMES = Activity(
    name="play_games",
    duration_minutes=60,
    need_effects={"fun": 40.0},
    required_location_types=["home", "entertainment"],
    personality_affinity={"openness": 0.3},
    description_template="{name} is playing games",
)

EXERCISE = Activity(
    name="exercise",
    duration_minutes=30,
    need_effects={"fun": 15.0, "energy": -10.0, "comfort": 10.0},
    required_location_types=["gym", "park"],
    personality_affinity={"conscientiousness": 0.5},
    description_template="{name} is exercising",
)

# Work / Skill
WORK = Activity(
    name="work",
    duration_minutes=120,
    need_effects={"fun": -15.0, "energy": -10.0},
    required_location_types=["home"],
    personality_affinity={"conscientiousness": 0.7},
    description_template="{name} is working",
)

STUDY = Activity(
    name="study",
    duration_minutes=60,
    need_effects={"fun": -10.0},
    required_location_types=["home", "library", "restaurant"],
    personality_affinity={"openness": 0.6, "conscientiousness": 0.5},
    description_template="{name} is studying",
)

COOK = Activity(
    name="cook",
    duration_minutes=30,
    need_effects={"hunger": 40.0, "fun": 10.0},
    required_location_types=["home"],
    personality_affinity={"conscientiousness": 0.3},
    description_template="{name} is cooking",
)

# Leisure
RELAX = Activity(
    name="relax",
    duration_minutes=20,
    need_effects={"comfort": 15.0, "energy": 10.0},
    required_location_types=["home", "park", "library"],
    description_template="{name} is relaxing",
)

MEDITATE = Activity(
    name="meditate",
    duration_minutes=15,
    need_effects={"comfort": 20.0, "social": -5.0},
    required_location_types=["home", "park"],
    personality_affinity={"openness": 0.5},
    description_template="{name} is meditating",
)

GARDEN = Activity(
    name="garden",
    duration_minutes=45,
    need_effects={"fun": 25.0, "comfort": 10.0},
    required_location_types=["park"],
    personality_affinity={"openness": 0.4, "agreeableness": 0.3},
    description_template="{name} is gardening",
)

# Movement (special — duration is variable, set by engine)
WALK_TO = Activity(
    name="walk_to",
    duration_minutes=10,
    need_effects={"energy": -2.0},
    required_location_types=[],  # available everywhere (means "leaving")
    description_template="{name} is walking to {destination}",
)

# Idle (fallback)
IDLE = Activity(
    name="idle",
    duration_minutes=5,
    need_effects={},
    required_location_types=[],
    description_template="{name} is idling",
)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_ACTIVITIES: dict[str, Activity] = {
    a.name: a
    for a in [
        EAT, SLEEP, NAP, SHOWER, USE_BATHROOM,
        CHAT, HANGOUT,
        READ, WATCH_TV, PLAY_GAMES, EXERCISE,
        WORK, STUDY, COOK,
        RELAX, MEDITATE, GARDEN,
        WALK_TO, IDLE,
    ]
}


def activities_for_location(location_type: str) -> list[Activity]:
    """Return activities available at a location of the given type."""
    return [
        a for a in ALL_ACTIVITIES.values()
        if location_type in a.required_location_types
    ]
