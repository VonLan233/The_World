"""Tests for the EventScheduler."""

from __future__ import annotations

from unittest.mock import patch

from the_world.simulation.clock import GameClock, MINUTES_PER_DAY, MINUTES_PER_HOUR
from the_world.simulation.engine import CharacterSim
from the_world.simulation.event_scheduler import EventScheduler, EVENT_COOLDOWN_TICKS
from the_world.simulation.events import (
    RANDOM_EVENTS,
    WeatherState,
    WeatherType,
)
from the_world.simulation.needs import NeedsManager


def _make_char(char_id: str = "c1", name: str = "Alice", location: str = "Home") -> CharacterSim:
    return CharacterSim(
        id=char_id,
        name=name,
        personality={"openness": 0.7, "conscientiousness": 0.5, "extraversion": 0.6,
                      "agreeableness": 0.5, "neuroticism": 0.4},
        current_location=location,
        current_location_type="home",
    )


def _make_scheduler(tick: int = 0) -> tuple[EventScheduler, GameClock]:
    clock = GameClock()
    if tick > 0:
        clock.advance(tick)
    scheduler = EventScheduler(clock=clock)
    return scheduler, clock


def test_scheduler_creation():
    scheduler, clock = _make_scheduler()
    assert scheduler.check_interval_ticks == 30
    assert scheduler.weather.current == WeatherType.clear


def test_weather_to_dict():
    scheduler, _ = _make_scheduler()
    d = scheduler.weather.to_dict()
    assert d["current"] == "clear"
    assert "temperatureModifier" in d


def test_weather_changes_on_hour_boundary():
    """Weather should update when the clock hour changes."""
    scheduler, clock = _make_scheduler()
    chars = {"c1": _make_char()}
    locs = {"Home": {"type": "home", "position_x": 0, "position_y": 0}}
    loc_map = {"Home": "home"}

    # Force weather change by patching random
    with patch("the_world.simulation.event_scheduler.random.random", return_value=0.99):
        # Advance to a new hour
        clock.advance(MINUTES_PER_HOUR)
        scheduler.check_and_fire(chars, locs, loc_map)
        # Weather system should have checked (regardless of whether it changed)
        assert scheduler._last_weather_hour == clock.hour


def test_weather_no_change_same_hour():
    """Weather should not re-check within the same hour."""
    scheduler, clock = _make_scheduler()
    scheduler._last_weather_hour = 0  # already checked hour 0

    chars = {"c1": _make_char()}
    locs = {"Home": {"type": "home", "position_x": 0, "position_y": 0}}
    loc_map = {"Home": "home"}

    events = scheduler.check_and_fire(chars, locs, loc_map)
    # No weather events (same hour)
    weather_events = [e for e in events if e["type"] == "weather_change"]
    assert len(weather_events) == 0


def test_seasonal_festival_fires_on_day_14():
    """Seasonal festival triggers on day 14 at 10AM."""
    # Day 14 at 10AM = (13 days * 1440) + (10 hours * 60) = 18720 + 600 = 19320
    tick = 13 * MINUTES_PER_DAY + 10 * MINUTES_PER_HOUR
    scheduler, clock = _make_scheduler(tick)

    assert clock.day_of_season == 14
    assert clock.hour == 10

    chars = {"c1": _make_char()}
    locs = {"Home": {"type": "home", "position_x": 0, "position_y": 0}}
    loc_map = {"Home": "home"}

    events = scheduler.check_and_fire(chars, locs, loc_map)
    seasonal = [e for e in events if e["type"] == "seasonal_event"]
    assert len(seasonal) == 1
    assert seasonal[0]["data"]["category"] == "seasonal"
    assert "Spring Festival" in seasonal[0]["data"]["title"]


def test_seasonal_festival_does_not_repeat():
    """Festival should only fire once per season."""
    tick = 13 * MINUTES_PER_DAY + 10 * MINUTES_PER_HOUR
    scheduler, clock = _make_scheduler(tick)

    chars = {"c1": _make_char()}
    locs = {"Home": {"type": "home", "position_x": 0, "position_y": 0}}
    loc_map = {"Home": "home"}

    events1 = scheduler.check_and_fire(chars, locs, loc_map)
    seasonal1 = [e for e in events1 if e["type"] == "seasonal_event"]
    assert len(seasonal1) == 1

    # Call again — should not repeat
    events2 = scheduler.check_and_fire(chars, locs, loc_map)
    seasonal2 = [e for e in events2 if e["type"] == "seasonal_event"]
    assert len(seasonal2) == 0


def test_birthday_fires_at_8am():
    """Birthday event fires on the correct day at 8AM."""
    # Day 5 at 8AM = 4 * 1440 + 8 * 60 = 5760 + 480 = 6240
    tick = 4 * MINUTES_PER_DAY + 8 * MINUTES_PER_HOUR
    scheduler, clock = _make_scheduler(tick)

    assert clock.day == 5
    assert clock.hour == 8

    csim = _make_char()
    chars = {"c1": csim}
    locs = {"Home": {"type": "home", "position_x": 0, "position_y": 0}}
    loc_map = {"Home": "home"}
    birthdays = {"c1": 5}  # birthday on day 5

    events = scheduler.check_and_fire(chars, locs, loc_map, character_birthdays=birthdays)
    bday = [e for e in events if e["type"] == "birthday_event"]
    assert len(bday) == 1
    assert "birthday" in bday[0]["description"].lower()


def test_birthday_does_not_repeat_same_day():
    """Birthday should only fire once per day."""
    tick = 4 * MINUTES_PER_DAY + 8 * MINUTES_PER_HOUR
    scheduler, clock = _make_scheduler(tick)

    csim = _make_char()
    chars = {"c1": csim}
    locs = {"Home": {"type": "home", "position_x": 0, "position_y": 0}}
    loc_map = {"Home": "home"}
    birthdays = {"c1": 5}

    events1 = scheduler.check_and_fire(chars, locs, loc_map, character_birthdays=birthdays)
    bday1 = [e for e in events1 if e["type"] == "birthday_event"]
    assert len(bday1) == 1

    events2 = scheduler.check_and_fire(chars, locs, loc_map, character_birthdays=birthdays)
    bday2 = [e for e in events2 if e["type"] == "birthday_event"]
    assert len(bday2) == 0


def test_random_event_respects_location_filter():
    """Events with location constraints should only fire at matching locations."""
    scheduler, clock = _make_scheduler(60)  # 1 hour in

    # Get eligible events for "gym" location
    eligible = scheduler._get_eligible_events("gym")
    for e in eligible:
        if e.allowed_location_types:
            assert "gym" in e.allowed_location_types


def test_random_event_respects_hour_filter():
    """Events with hour constraints should be filtered by current hour."""
    # Test at noon (hour 12)
    scheduler, clock = _make_scheduler(12 * MINUTES_PER_HOUR)
    eligible = scheduler._get_eligible_events("park")

    for e in eligible:
        if e.allowed_hours is not None:
            start_h, end_h = e.allowed_hours
            if start_h <= end_h:
                assert start_h <= 12 <= end_h
            else:  # wrap around
                assert 12 >= start_h or 12 <= end_h


def test_cooldown_prevents_repeat():
    """Same event should not fire within cooldown period."""
    scheduler, clock = _make_scheduler(100)
    scheduler._cooldowns["test_event"] = 100

    assert scheduler._is_on_cooldown("test_event") is True

    # Advance past cooldown
    clock.advance(EVENT_COOLDOWN_TICKS + 1)
    assert scheduler._is_on_cooldown("test_event") is False


def test_apply_effects_modifies_needs():
    """Event effects should modify character needs."""
    scheduler, _ = _make_scheduler()
    csim = _make_char()
    initial_fun = csim.needs.fun

    from the_world.simulation.events import FIND_STRAY_CAT
    scheduler._apply_effects(csim, FIND_STRAY_CAT)

    expected_fun = min(100.0, initial_fun + FIND_STRAY_CAT.need_effects.get("fun", 0))
    assert csim.needs.fun == expected_fun


def test_build_event_format():
    """Built event dict should have the right structure."""
    scheduler, clock = _make_scheduler(500)
    csim = _make_char()

    from the_world.simulation.events import FIND_STRAY_CAT
    event = scheduler._build_event(FIND_STRAY_CAT, csim)

    assert event["type"] == "random_event"
    assert event["characterId"] == "c1"
    assert event["characterName"] == "Alice"
    assert event["tick"] == 500
    assert "Alice" in event["description"]
    assert event["data"]["eventId"] == "find_stray_cat"
    assert event["data"]["memoryWorthy"] is True


def test_weighted_choice_deterministic():
    """Weighted choice with single option should always return that option."""
    result = EventScheduler._weighted_choice({WeatherType.rain: 1.0})
    assert result == WeatherType.rain


def test_check_and_fire_returns_list():
    """check_and_fire should always return a list."""
    scheduler, clock = _make_scheduler()
    chars = {"c1": _make_char()}
    locs = {"Home": {"type": "home", "position_x": 0, "position_y": 0}}
    loc_map = {"Home": "home"}

    result = scheduler.check_and_fire(chars, locs, loc_map)
    assert isinstance(result, list)


def test_roll_probability_personality_boost():
    """Higher matching personality trait should increase roll probability."""
    scheduler, _ = _make_scheduler()

    from the_world.simulation.events import FIND_STRAY_CAT

    # Test with high agreeableness (should boost probability)
    high_agree = {"agreeableness": 1.0, "openness": 1.0}
    low_agree = {"agreeableness": 0.0, "openness": 0.0}

    # Run many trials to check statistical difference
    high_count = sum(1 for _ in range(10000) if scheduler._roll_probability(FIND_STRAY_CAT, high_agree))
    low_count = sum(1 for _ in range(10000) if scheduler._roll_probability(FIND_STRAY_CAT, low_agree))

    # High agreeableness should trigger more often
    assert high_count > low_count
