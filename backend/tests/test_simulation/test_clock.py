"""Tests for the GameClock."""

from the_world.simulation.clock import GameClock, MINUTES_PER_DAY, DAYS_PER_SEASON


def test_initial_state():
    clock = GameClock()
    assert clock.tick == 0
    assert clock.hour == 0
    assert clock.day == 1
    assert clock.season == "spring"
    assert clock.paused is True


def test_advance_minutes():
    clock = GameClock()
    clock.advance(90)  # 1 hour 30 minutes
    assert clock.tick == 90
    assert clock.hour == 1
    assert clock.minute == 30


def test_advance_full_day():
    clock = GameClock()
    clock.advance(MINUTES_PER_DAY)  # 1440 minutes
    assert clock.day == 2
    assert clock.hour == 0


def test_season_change():
    clock = GameClock()
    # Advance 28 days
    clock.advance(MINUTES_PER_DAY * DAYS_PER_SEASON)
    assert clock.season == "summer"
    assert clock.day == DAYS_PER_SEASON + 1

    # Advance another 28 days
    clock.advance(MINUTES_PER_DAY * DAYS_PER_SEASON)
    assert clock.season == "autumn"

    # Advance 2 more seasons → back to spring
    clock.advance(MINUTES_PER_DAY * DAYS_PER_SEASON * 2)
    assert clock.season == "spring"


def test_to_clock_state():
    clock = GameClock()
    clock.advance(60 * 14)  # 14:00
    state = clock.to_clock_state()
    assert state["currentTick"] == 840
    assert state["currentHour"] == 14
    assert state["currentDay"] == 1
    assert state["currentSeason"] == "spring"
    assert state["isPaused"] is True


def test_daytime_night():
    clock = GameClock()
    clock.advance(60 * 12)  # noon
    assert clock.is_daytime is True
    assert clock.is_night is False

    clock2 = GameClock()
    clock2.advance(60 * 3)  # 3 AM
    assert clock2.is_daytime is False
    assert clock2.is_night is True
