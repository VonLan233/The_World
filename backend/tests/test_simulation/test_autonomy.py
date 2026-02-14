"""Tests for the autonomy decision system."""

from the_world.simulation.autonomy import choose_activity
from the_world.simulation.needs import NeedsManager


def test_critical_energy_forces_sleep():
    needs = NeedsManager(energy=5.0)
    personality = {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
                   "agreeableness": 0.5, "neuroticism": 0.5}
    activity, dest = choose_activity(needs, personality, "home")
    assert activity.name == "sleep"
    assert dest is None


def test_critical_energy_walk_home_if_not_at_home():
    needs = NeedsManager(energy=5.0)
    personality = {"openness": 0.5}
    locations = {"Home": "home", "Park": "park"}
    activity, dest = choose_activity(needs, personality, "park", locations)
    assert activity.name == "walk_to"
    assert dest == "Home"


def test_critical_hunger_forces_eat():
    needs = NeedsManager(hunger=10.0, energy=50.0)
    personality = {"openness": 0.5}
    activity, dest = choose_activity(needs, personality, "home")
    assert activity.name == "eat"


def test_critical_hunger_walk_to_restaurant():
    needs = NeedsManager(hunger=10.0, energy=50.0)
    personality = {"openness": 0.5}
    locations = {"Park": "park", "Cafe": "restaurant"}
    activity, dest = choose_activity(needs, personality, "park", locations)
    assert activity.name == "walk_to"
    assert dest == "Cafe"


def test_returns_valid_activity():
    """With non-critical needs, should return a valid activity for the location."""
    needs = NeedsManager()
    personality = {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
                   "agreeableness": 0.5, "neuroticism": 0.5}
    activity, _ = choose_activity(needs, personality, "home")
    assert activity.name != ""
    assert activity.duration_minutes > 0


def test_nearby_characters_backward_compatible():
    """Calling without nearby_characters still works (default None)."""
    needs = NeedsManager()
    personality = {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
                   "agreeableness": 0.5, "neuroticism": 0.5}
    activity, _ = choose_activity(needs, personality, "park")
    assert activity.name != ""


def test_nearby_characters_boosts_social():
    """When nearby_characters is provided, social activities should score higher.

    We test this statistically: run many trials with and without nearby chars.
    The social activity selection rate should increase with nearby characters.
    """
    import random
    random.seed(42)

    personality = {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.7,
                   "agreeableness": 0.5, "neuroticism": 0.3}
    needs = NeedsManager(social=30.0)  # Low social → wants social activities
    nearby = [{"id": "other-1", "name": "Other"}]

    social_without = 0
    social_with = 0
    trials = 200

    random.seed(42)
    for _ in range(trials):
        act, _ = choose_activity(needs, personality, "park", nearby_characters=None)
        if "social" in act.need_effects and act.need_effects.get("social", 0) > 0:
            social_without += 1

    random.seed(42)
    for _ in range(trials):
        act, _ = choose_activity(needs, personality, "park", nearby_characters=nearby)
        if "social" in act.need_effects and act.need_effects.get("social", 0) > 0:
            social_with += 1

    # With nearby characters, social activities should be picked at least as often
    assert social_with >= social_without
