"""Random event definitions — weather, seasonal festivals, encounters, birthdays."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EventCategory(str, Enum):
    random_encounter = "random_encounter"
    weather = "weather"
    seasonal = "seasonal"
    birthday = "birthday"
    location = "location"


class WeatherType(str, Enum):
    clear = "clear"
    cloudy = "cloudy"
    rain = "rain"
    storm = "storm"
    snow = "snow"
    hot = "hot"


# ---------------------------------------------------------------------------
# Weather state
# ---------------------------------------------------------------------------

@dataclass
class WeatherState:
    """Current weather conditions in the simulation world."""

    current: WeatherType = WeatherType.clear
    temperature_modifier: float = 0.0  # -1.0 (cold) to +1.0 (hot)
    changed_at_tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "current": self.current.value,
            "temperatureModifier": self.temperature_modifier,
            "changedAtTick": self.changed_at_tick,
        }


# ---------------------------------------------------------------------------
# Weather transition tables (Markov chain, per season)
# ---------------------------------------------------------------------------

# Each season maps from current weather → {next_weather: probability}
# Probabilities for each row must sum to ~1.0

WEATHER_TRANSITION_TABLE: dict[str, dict[WeatherType, dict[WeatherType, float]]] = {
    "spring": {
        WeatherType.clear:  {WeatherType.clear: 0.45, WeatherType.cloudy: 0.25, WeatherType.rain: 0.25, WeatherType.storm: 0.05},
        WeatherType.cloudy: {WeatherType.clear: 0.30, WeatherType.cloudy: 0.30, WeatherType.rain: 0.30, WeatherType.storm: 0.10},
        WeatherType.rain:   {WeatherType.clear: 0.25, WeatherType.cloudy: 0.30, WeatherType.rain: 0.35, WeatherType.storm: 0.10},
        WeatherType.storm:  {WeatherType.clear: 0.20, WeatherType.cloudy: 0.35, WeatherType.rain: 0.35, WeatherType.storm: 0.10},
        WeatherType.snow:   {WeatherType.clear: 0.40, WeatherType.cloudy: 0.30, WeatherType.rain: 0.25, WeatherType.storm: 0.05},
        WeatherType.hot:    {WeatherType.clear: 0.45, WeatherType.cloudy: 0.25, WeatherType.rain: 0.25, WeatherType.storm: 0.05},
    },
    "summer": {
        WeatherType.clear:  {WeatherType.clear: 0.50, WeatherType.cloudy: 0.15, WeatherType.rain: 0.15, WeatherType.hot: 0.15, WeatherType.storm: 0.05},
        WeatherType.cloudy: {WeatherType.clear: 0.35, WeatherType.cloudy: 0.25, WeatherType.rain: 0.20, WeatherType.hot: 0.10, WeatherType.storm: 0.10},
        WeatherType.rain:   {WeatherType.clear: 0.30, WeatherType.cloudy: 0.25, WeatherType.rain: 0.25, WeatherType.hot: 0.10, WeatherType.storm: 0.10},
        WeatherType.storm:  {WeatherType.clear: 0.25, WeatherType.cloudy: 0.30, WeatherType.rain: 0.25, WeatherType.hot: 0.10, WeatherType.storm: 0.10},
        WeatherType.hot:    {WeatherType.clear: 0.35, WeatherType.cloudy: 0.15, WeatherType.rain: 0.10, WeatherType.hot: 0.35, WeatherType.storm: 0.05},
        WeatherType.snow:   {WeatherType.clear: 0.50, WeatherType.cloudy: 0.15, WeatherType.rain: 0.15, WeatherType.hot: 0.15, WeatherType.storm: 0.05},
    },
    "autumn": {
        WeatherType.clear:  {WeatherType.clear: 0.30, WeatherType.cloudy: 0.30, WeatherType.rain: 0.30, WeatherType.storm: 0.10},
        WeatherType.cloudy: {WeatherType.clear: 0.20, WeatherType.cloudy: 0.35, WeatherType.rain: 0.35, WeatherType.storm: 0.10},
        WeatherType.rain:   {WeatherType.clear: 0.20, WeatherType.cloudy: 0.25, WeatherType.rain: 0.40, WeatherType.storm: 0.15},
        WeatherType.storm:  {WeatherType.clear: 0.20, WeatherType.cloudy: 0.30, WeatherType.rain: 0.35, WeatherType.storm: 0.15},
        WeatherType.snow:   {WeatherType.clear: 0.30, WeatherType.cloudy: 0.30, WeatherType.rain: 0.30, WeatherType.storm: 0.10},
        WeatherType.hot:    {WeatherType.clear: 0.30, WeatherType.cloudy: 0.30, WeatherType.rain: 0.30, WeatherType.storm: 0.10},
    },
    "winter": {
        WeatherType.clear:  {WeatherType.clear: 0.25, WeatherType.cloudy: 0.25, WeatherType.snow: 0.30, WeatherType.rain: 0.10, WeatherType.storm: 0.10},
        WeatherType.cloudy: {WeatherType.clear: 0.20, WeatherType.cloudy: 0.25, WeatherType.snow: 0.35, WeatherType.rain: 0.10, WeatherType.storm: 0.10},
        WeatherType.rain:   {WeatherType.clear: 0.20, WeatherType.cloudy: 0.25, WeatherType.snow: 0.30, WeatherType.rain: 0.15, WeatherType.storm: 0.10},
        WeatherType.storm:  {WeatherType.clear: 0.15, WeatherType.cloudy: 0.25, WeatherType.snow: 0.30, WeatherType.rain: 0.15, WeatherType.storm: 0.15},
        WeatherType.snow:   {WeatherType.clear: 0.15, WeatherType.cloudy: 0.20, WeatherType.snow: 0.45, WeatherType.rain: 0.10, WeatherType.storm: 0.10},
        WeatherType.hot:    {WeatherType.clear: 0.25, WeatherType.cloudy: 0.25, WeatherType.snow: 0.30, WeatherType.rain: 0.10, WeatherType.storm: 0.10},
    },
}

# Temperature modifiers per weather type
WEATHER_TEMPERATURE: dict[WeatherType, float] = {
    WeatherType.clear: 0.0,
    WeatherType.cloudy: -0.1,
    WeatherType.rain: -0.3,
    WeatherType.storm: -0.4,
    WeatherType.snow: -0.8,
    WeatherType.hot: 0.8,
}


# ---------------------------------------------------------------------------
# Random event definition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RandomEventDef:
    """A random event that can trigger during simulation."""

    event_id: str
    category: EventCategory
    title: str
    description_template: str  # {name} = character name

    # Effects on character needs
    need_effects: dict[str, float] = field(default_factory=dict)
    mood_modifier: float = 0.0  # direct mood boost/penalty

    # Constraints
    allowed_seasons: list[str] = field(default_factory=list)  # empty = all
    allowed_location_types: list[str] = field(default_factory=list)  # empty = all
    allowed_hours: tuple[int, int] | None = None  # (start, end) inclusive, None = all

    # Probability
    base_probability: float = 0.01  # per check (0.01 = 1%)
    personality_modifiers: dict[str, float] = field(default_factory=dict)
    # e.g. {"openness": 0.5} means high openness increases probability

    # Memory settings
    memory_worthy: bool = True
    memory_importance: float = 0.6
    memory_valence: float = 0.3  # positive = happy memory

    def __hash__(self) -> int:
        return hash(self.event_id)


# ---------------------------------------------------------------------------
# Event catalogue
# ---------------------------------------------------------------------------

# -- Random encounters --

FIND_STRAY_CAT = RandomEventDef(
    event_id="find_stray_cat",
    category=EventCategory.random_encounter,
    title="Found a Stray Cat",
    description_template="{name} found a cute stray cat and spent some time petting it.",
    need_effects={"fun": 15.0, "social": 10.0},
    mood_modifier=5.0,
    allowed_location_types=["park", "home"],
    base_probability=0.008,
    personality_modifiers={"agreeableness": 0.4, "openness": 0.2},
    memory_importance=0.7,
    memory_valence=0.6,
)

MYSTERIOUS_STRANGER = RandomEventDef(
    event_id="mysterious_stranger",
    category=EventCategory.random_encounter,
    title="Mysterious Stranger",
    description_template="{name} had a strange but fascinating encounter with a mysterious stranger.",
    need_effects={"social": 15.0, "fun": 10.0},
    mood_modifier=3.0,
    allowed_location_types=["park", "restaurant", "library"],
    allowed_hours=(20, 4),  # night-time
    base_probability=0.005,
    personality_modifiers={"openness": 0.6},
    memory_importance=0.8,
    memory_valence=0.4,
)

FIND_HIDDEN_ITEM = RandomEventDef(
    event_id="find_hidden_item",
    category=EventCategory.random_encounter,
    title="Hidden Discovery",
    description_template="{name} discovered something interesting hidden nearby!",
    need_effects={"fun": 20.0},
    mood_modifier=8.0,
    base_probability=0.003,
    personality_modifiers={"openness": 0.5},
    memory_importance=0.7,
    memory_valence=0.5,
)

# -- Location events --

CAFE_SPECIAL_MENU = RandomEventDef(
    event_id="cafe_special_menu",
    category=EventCategory.location,
    title="Special Menu Day",
    description_template="{name} is enjoying today's special menu at the cafe!",
    need_effects={"hunger": 20.0, "fun": 10.0},
    mood_modifier=4.0,
    allowed_location_types=["restaurant"],
    base_probability=0.015,
    memory_importance=0.4,
    memory_valence=0.3,
)

PARK_FESTIVAL = RandomEventDef(
    event_id="park_festival",
    category=EventCategory.location,
    title="Park Festival",
    description_template="{name} stumbled upon a lively festival in the park!",
    need_effects={"fun": 25.0, "social": 20.0},
    mood_modifier=10.0,
    allowed_location_types=["park"],
    allowed_hours=(8, 20),  # daytime
    base_probability=0.005,
    personality_modifiers={"extraversion": 0.5},
    memory_importance=0.7,
    memory_valence=0.7,
)

LIBRARY_BOOK_FAIR = RandomEventDef(
    event_id="library_book_fair",
    category=EventCategory.location,
    title="Book Fair",
    description_template="{name} is browsing through a wonderful book fair at the library!",
    need_effects={"fun": 15.0},
    mood_modifier=5.0,
    allowed_location_types=["library"],
    base_probability=0.010,
    personality_modifiers={"openness": 0.5},
    memory_importance=0.5,
    memory_valence=0.4,
)

GYM_CHALLENGE = RandomEventDef(
    event_id="gym_challenge",
    category=EventCategory.location,
    title="Fitness Challenge",
    description_template="{name} joined a spontaneous fitness challenge at the gym!",
    need_effects={"fun": 15.0, "energy": -10.0, "comfort": 10.0},
    mood_modifier=6.0,
    allowed_location_types=["gym"],
    base_probability=0.010,
    personality_modifiers={"conscientiousness": 0.4, "extraversion": 0.3},
    memory_importance=0.5,
    memory_valence=0.4,
)

GAME_TOURNAMENT = RandomEventDef(
    event_id="game_tournament",
    category=EventCategory.location,
    title="Game Tournament",
    description_template="{name} entered an exciting game tournament!",
    need_effects={"fun": 30.0, "social": 15.0},
    mood_modifier=8.0,
    allowed_location_types=["entertainment"],
    base_probability=0.008,
    personality_modifiers={"openness": 0.3, "extraversion": 0.3},
    memory_importance=0.6,
    memory_valence=0.5,
)

# -- Weather events (auto-triggered on weather change) --

RAIN_START = RandomEventDef(
    event_id="rain_start",
    category=EventCategory.weather,
    title="It Started Raining",
    description_template="It started raining. {name} looks up at the sky.",
    need_effects={"comfort": -5.0},
    mood_modifier=-2.0,
    base_probability=1.0,  # auto on weather change
    memory_worthy=False,
    memory_importance=0.2,
    memory_valence=-0.1,
)

STORM_WARNING = RandomEventDef(
    event_id="storm_warning",
    category=EventCategory.weather,
    title="Storm Warning",
    description_template="A storm is approaching! {name} should find shelter.",
    need_effects={"comfort": -10.0},
    mood_modifier=-5.0,
    base_probability=1.0,
    memory_worthy=True,
    memory_importance=0.5,
    memory_valence=-0.4,
)

BEAUTIFUL_DAY = RandomEventDef(
    event_id="beautiful_day",
    category=EventCategory.weather,
    title="Beautiful Day",
    description_template="What a beautiful day! {name} feels great.",
    need_effects={"comfort": 5.0, "fun": 5.0},
    mood_modifier=3.0,
    allowed_seasons=["spring", "summer"],
    base_probability=1.0,
    memory_worthy=False,
    memory_importance=0.2,
    memory_valence=0.3,
)

SNOW_DAY = RandomEventDef(
    event_id="snow_day",
    category=EventCategory.weather,
    title="Snow Day",
    description_template="Snow is falling! {name} watches the snowflakes.",
    need_effects={"fun": 10.0, "comfort": -3.0},
    mood_modifier=2.0,
    allowed_seasons=["winter"],
    base_probability=1.0,
    memory_worthy=True,
    memory_importance=0.4,
    memory_valence=0.3,
)

# -- Seasonal festivals (auto-triggered on day 14 of each season) --

SPRING_FESTIVAL = RandomEventDef(
    event_id="spring_festival",
    category=EventCategory.seasonal,
    title="Spring Festival",
    description_template="{name} celebrates the Spring Festival with everyone!",
    need_effects={"fun": 30.0, "social": 25.0, "hunger": 15.0},
    mood_modifier=15.0,
    allowed_seasons=["spring"],
    base_probability=1.0,
    memory_worthy=True,
    memory_importance=0.9,
    memory_valence=0.8,
)

SUMMER_PARTY = RandomEventDef(
    event_id="summer_party",
    category=EventCategory.seasonal,
    title="Summer Party",
    description_template="{name} joins the big Summer Party!",
    need_effects={"fun": 35.0, "social": 30.0},
    mood_modifier=15.0,
    allowed_seasons=["summer"],
    base_probability=1.0,
    memory_worthy=True,
    memory_importance=0.9,
    memory_valence=0.8,
)

AUTUMN_HARVEST = RandomEventDef(
    event_id="autumn_harvest",
    category=EventCategory.seasonal,
    title="Autumn Harvest",
    description_template="{name} enjoys the Autumn Harvest celebration!",
    need_effects={"fun": 25.0, "social": 20.0, "hunger": 25.0},
    mood_modifier=15.0,
    allowed_seasons=["autumn"],
    base_probability=1.0,
    memory_worthy=True,
    memory_importance=0.9,
    memory_valence=0.8,
)

WINTER_HOLIDAY = RandomEventDef(
    event_id="winter_holiday",
    category=EventCategory.seasonal,
    title="Winter Holiday",
    description_template="{name} celebrates the cozy Winter Holiday!",
    need_effects={"fun": 30.0, "social": 25.0, "comfort": 20.0},
    mood_modifier=15.0,
    allowed_seasons=["winter"],
    base_probability=1.0,
    memory_worthy=True,
    memory_importance=0.9,
    memory_valence=0.8,
)

# -- Birthday (auto-triggered on character's birth day) --

BIRTHDAY = RandomEventDef(
    event_id="birthday",
    category=EventCategory.birthday,
    title="Happy Birthday!",
    description_template="It's {name}'s birthday! Everyone wishes them well.",
    need_effects={"fun": 30.0, "social": 25.0},
    mood_modifier=20.0,
    base_probability=1.0,
    memory_worthy=True,
    memory_importance=1.0,
    memory_valence=0.9,
)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

RANDOM_EVENTS: list[RandomEventDef] = [
    FIND_STRAY_CAT,
    MYSTERIOUS_STRANGER,
    FIND_HIDDEN_ITEM,
    CAFE_SPECIAL_MENU,
    PARK_FESTIVAL,
    LIBRARY_BOOK_FAIR,
    GYM_CHALLENGE,
    GAME_TOURNAMENT,
]

WEATHER_EVENTS: dict[str, RandomEventDef] = {
    "rain": RAIN_START,
    "storm": STORM_WARNING,
    "clear_nice": BEAUTIFUL_DAY,
    "snow": SNOW_DAY,
}

SEASONAL_EVENTS: dict[str, RandomEventDef] = {
    "spring": SPRING_FESTIVAL,
    "summer": SUMMER_PARTY,
    "autumn": AUTUMN_HARVEST,
    "winter": WINTER_HOLIDAY,
}

ALL_RANDOM_EVENT_DEFS: dict[str, RandomEventDef] = {
    e.event_id: e
    for e in [
        *RANDOM_EVENTS,
        *WEATHER_EVENTS.values(),
        *SEASONAL_EVENTS.values(),
        BIRTHDAY,
    ]
}
