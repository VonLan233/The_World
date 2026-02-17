"""Tests for event definitions."""

from the_world.simulation.events import (
    ALL_RANDOM_EVENT_DEFS,
    RANDOM_EVENTS,
    SEASONAL_EVENTS,
    WEATHER_EVENTS,
    WEATHER_TRANSITION_TABLE,
    BIRTHDAY,
    EventCategory,
    RandomEventDef,
    WeatherState,
    WeatherType,
)


def test_weather_state_to_dict():
    ws = WeatherState(current=WeatherType.rain, temperature_modifier=-0.3, changed_at_tick=100)
    d = ws.to_dict()
    assert d["current"] == "rain"
    assert d["temperatureModifier"] == -0.3
    assert d["changedAtTick"] == 100


def test_weather_state_defaults():
    ws = WeatherState()
    assert ws.current == WeatherType.clear
    assert ws.temperature_modifier == 0.0
    assert ws.changed_at_tick == 0


def test_all_random_events_have_unique_ids():
    ids = [e.event_id for e in ALL_RANDOM_EVENT_DEFS.values()]
    assert len(ids) == len(set(ids))


def test_random_events_have_valid_categories():
    for event in RANDOM_EVENTS:
        assert event.category in (EventCategory.random_encounter, EventCategory.location)


def test_weather_events_are_auto_probability():
    for event in WEATHER_EVENTS.values():
        assert event.base_probability == 1.0
        assert event.category == EventCategory.weather


def test_seasonal_events_cover_all_seasons():
    assert set(SEASONAL_EVENTS.keys()) == {"spring", "summer", "autumn", "winter"}
    for event in SEASONAL_EVENTS.values():
        assert event.category == EventCategory.seasonal
        assert event.memory_worthy is True


def test_birthday_event():
    assert BIRTHDAY.category == EventCategory.birthday
    assert BIRTHDAY.memory_worthy is True
    assert BIRTHDAY.memory_importance == 1.0


def test_transition_table_covers_all_seasons():
    for season in ("spring", "summer", "autumn", "winter"):
        assert season in WEATHER_TRANSITION_TABLE
        table = WEATHER_TRANSITION_TABLE[season]
        # Should have transitions for all weather types
        for wt in WeatherType:
            assert wt in table, f"Missing {wt} in {season} transition table"
            probs = table[wt]
            total = sum(probs.values())
            assert abs(total - 1.0) < 0.01, f"{season}/{wt} probabilities sum to {total}"


def test_random_event_def_frozen():
    event = RANDOM_EVENTS[0]
    assert isinstance(event, RandomEventDef)
    # Should be frozen (immutable)
    try:
        event.title = "new title"  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass
