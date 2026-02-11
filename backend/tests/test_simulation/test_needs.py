"""Tests for the NeedsManager."""

from the_world.simulation.needs import NeedsManager


def test_initial_values():
    nm = NeedsManager()
    assert nm.hunger == 80.0
    assert nm.energy == 100.0


def test_decay_reduces_needs():
    nm = NeedsManager()
    nm.decay(60)  # 1 game hour
    assert nm.hunger < 80.0
    assert nm.energy < 100.0
    assert nm.social < 70.0


def test_decay_clamp_to_zero():
    nm = NeedsManager(hunger=1.0)
    nm.decay(60 * 10)  # 10 hours
    assert nm.hunger == 0.0


def test_sleep_recovers_energy():
    nm = NeedsManager(energy=20.0)
    nm.decay(60, is_sleeping=True)  # 1 hour sleeping
    assert nm.energy > 20.0  # energy should increase


def test_personality_extraversion_affects_social():
    # High extraversion → social decays faster
    high_ext = NeedsManager(social=50.0)
    high_ext.decay(60, personality={"extraversion": 1.0})

    low_ext = NeedsManager(social=50.0)
    low_ext.decay(60, personality={"extraversion": 0.0})

    assert high_ext.social < low_ext.social


def test_apply_activity_effect():
    nm = NeedsManager(hunger=30.0, fun=20.0)
    nm.apply_activity_effect({"hunger": 50.0, "fun": 10.0})
    assert nm.hunger == 80.0
    assert nm.fun == 30.0


def test_clamp_to_100():
    nm = NeedsManager(hunger=90.0)
    nm.apply_activity_effect({"hunger": 50.0})
    assert nm.hunger == 100.0


def test_urgency_scores():
    nm = NeedsManager(hunger=0.0, energy=100.0)
    scores = nm.get_urgency_scores()
    assert scores["hunger"] == 1.0  # max urgency
    assert scores["energy"] == 0.0  # no urgency


def test_is_critical():
    nm = NeedsManager(hunger=10.0, energy=50.0)
    assert nm.is_critical("hunger") is True
    assert nm.is_critical("energy") is False


def test_any_critical():
    nm = NeedsManager(hunger=80.0, energy=5.0)
    assert nm.any_critical() == "energy"


def test_calculate_mood():
    # All needs high → happy
    nm = NeedsManager(hunger=80, energy=90, social=70, fun=70, hygiene=90, comfort=80)
    score, label = nm.calculate_mood()
    assert score > 60
    assert label in ("happy", "ecstatic")

    # All needs low → miserable
    nm2 = NeedsManager(hunger=5, energy=5, social=5, fun=5, hygiene=5, comfort=5)
    score2, label2 = nm2.calculate_mood()
    assert score2 < 15
    assert label2 in ("miserable", "desperate")


def test_to_dict():
    nm = NeedsManager()
    d = nm.to_dict()
    assert set(d.keys()) == {"hunger", "energy", "social", "fun", "hygiene", "comfort"}
    assert all(isinstance(v, float) for v in d.values())
