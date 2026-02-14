"""Tests for the RelationshipService."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.models.character import Character
from the_world.models.user import User
from the_world.services.relationship_service import (
    RelationshipService,
    calculate_compatibility,
    classify_type,
)

# Stable UUIDs
UUID_USER = uuid.uuid5(uuid.NAMESPACE_DNS, "testuser")
UUID_A = uuid.uuid5(uuid.NAMESPACE_DNS, "alice")
UUID_B = uuid.uuid5(uuid.NAMESPACE_DNS, "bob")
UUID_C = uuid.uuid5(uuid.NAMESPACE_DNS, "carol")


# ---------------------------------------------------------------------------
# Helper: get a fresh DB session + seed user & characters
# ---------------------------------------------------------------------------

@pytest.fixture()
async def db_session():
    """Yield a test-scoped async DB session with seeded characters."""
    from tests.conftest import TestSessionLocal
    async with TestSessionLocal() as session:
        # Seed a user
        user = User(
            id=UUID_USER,
            username="testuser",
            email="test@test.com",
            hashed_password="fakehash",
        )
        session.add(user)
        await session.flush()

        # Seed characters
        for char_id, name in [(UUID_A, "Alice"), (UUID_B, "Bob"), (UUID_C, "Carol")]:
            char = Character(
                id=char_id,
                owner_id=UUID_USER,
                name=name,
                personality={"openness": 50, "conscientiousness": 50,
                             "extraversion": 50, "agreeableness": 50,
                             "neuroticism": 50},
            )
            session.add(char)
        await session.flush()

        yield session


# ---------------------------------------------------------------------------
# calculate_compatibility (pure function, no DB needed)
# ---------------------------------------------------------------------------

class TestCalculateCompatibility:
    def test_identical_personalities_high_compat(self):
        p = {"openness": 70, "conscientiousness": 60, "extraversion": 50,
             "agreeableness": 80, "neuroticism": 30}
        score = calculate_compatibility(p, p)
        assert score > 0.5

    def test_opposite_personalities_lower_compat(self):
        pa = {"openness": 90, "conscientiousness": 90, "extraversion": 90,
              "agreeableness": 90, "neuroticism": 10}
        pb = {"openness": 10, "conscientiousness": 10, "extraversion": 10,
              "agreeableness": 10, "neuroticism": 90}
        score = calculate_compatibility(pa, pb)
        assert score < 0.3

    def test_both_high_neuroticism_penalty(self):
        base = {"openness": 50, "conscientiousness": 50, "extraversion": 50,
                "agreeableness": 50}
        high_n = {**base, "neuroticism": 80}
        low_n = {**base, "neuroticism": 30}

        score_both_high = calculate_compatibility(high_n, high_n)
        score_one_low = calculate_compatibility(high_n, low_n)
        assert score_both_high < score_one_low

    def test_returns_in_valid_range(self):
        pa = {"openness": 0, "conscientiousness": 0, "extraversion": 0,
              "agreeableness": 0, "neuroticism": 100}
        pb = {"openness": 100, "conscientiousness": 100, "extraversion": 100,
              "agreeableness": 100, "neuroticism": 100}
        score = calculate_compatibility(pa, pb)
        assert -1.0 <= score <= 1.0

    def test_empty_personalities_default(self):
        score = calculate_compatibility({}, {})
        assert -1.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# classify_type (uses mock objects to avoid SQLAlchemy descriptor issues)
# ---------------------------------------------------------------------------

class TestClassifyType:
    def _make_rel(self, friendship=0.0, romance=0.0, rivalry=0.0):
        rel = MagicMock()
        rel.friendship_score = friendship
        rel.romance_score = romance
        rel.rivalry_score = rivalry
        return rel

    def test_stranger(self):
        assert classify_type(self._make_rel(friendship=5)) == "stranger"

    def test_acquaintance(self):
        assert classify_type(self._make_rel(friendship=20)) == "acquaintance"

    def test_friend(self):
        assert classify_type(self._make_rel(friendship=50)) == "friend"

    def test_close_friend(self):
        assert classify_type(self._make_rel(friendship=80)) == "close_friend"

    def test_rival(self):
        assert classify_type(self._make_rel(rivalry=60)) == "rival"

    def test_romantic(self):
        assert classify_type(self._make_rel(romance=60, friendship=80)) == "romantic"

    def test_rival_takes_priority_over_romantic(self):
        assert classify_type(self._make_rel(rivalry=60, romance=60)) == "rival"


# ---------------------------------------------------------------------------
# RelationshipService (requires DB)
# ---------------------------------------------------------------------------

class TestRelationshipServiceGetOrCreate:
    @pytest.mark.asyncio
    async def test_creates_new_relationship(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        rel = await svc.get_or_create(str(UUID_A), str(UUID_B))
        assert rel is not None
        assert rel.friendship_score == 0.0
        assert rel.relationship_type == "stranger"

    @pytest.mark.asyncio
    async def test_idempotent(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        rel1 = await svc.get_or_create(str(UUID_A), str(UUID_B))
        rel2 = await svc.get_or_create(str(UUID_A), str(UUID_B))
        assert rel1.id == rel2.id

    @pytest.mark.asyncio
    async def test_bidirectional_lookup(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        rel1 = await svc.get_or_create(str(UUID_A), str(UUID_B))
        rel2 = await svc.get_relationship(str(UUID_B), str(UUID_A))
        assert rel2 is not None
        assert rel2.id == rel1.id


class TestRelationshipServiceEvolve:
    @pytest.mark.asyncio
    async def test_positive_interaction_increases_score(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        pa = {"openness": 50, "conscientiousness": 50, "extraversion": 50,
              "agreeableness": 50, "neuroticism": 50}
        rel, milestones = await svc.evolve_after_interaction(
            str(UUID_A), str(UUID_B), 1.0, pa, pa
        )
        assert rel.friendship_score > 0

    @pytest.mark.asyncio
    async def test_negative_interaction_decreases_score(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        pa = {"openness": 50, "conscientiousness": 50, "extraversion": 50,
              "agreeableness": 50, "neuroticism": 50}
        rel, _ = await svc.evolve_after_interaction(
            str(UUID_A), str(UUID_B), -1.0, pa, pa
        )
        assert rel.friendship_score < 0

    @pytest.mark.asyncio
    async def test_score_clamped(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        pa = {"openness": 50, "conscientiousness": 50, "extraversion": 50,
              "agreeableness": 50, "neuroticism": 50}
        for _ in range(50):
            rel, _ = await svc.evolve_after_interaction(
                str(UUID_A), str(UUID_B), 1.0, pa, pa
            )
        assert rel.friendship_score <= 100.0

    @pytest.mark.asyncio
    async def test_milestone_detection(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        pa = {"openness": 50, "conscientiousness": 50, "extraversion": 50,
              "agreeableness": 50, "neuroticism": 50}
        all_milestones: list[str] = []
        for _ in range(20):
            _, ms = await svc.evolve_after_interaction(
                str(UUID_A), str(UUID_B), 1.0, pa, pa
            )
            all_milestones.extend(ms)
        assert "+25" in all_milestones


class TestRelationshipServiceSummary:
    @pytest.mark.asyncio
    async def test_append_and_retrieve(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        await svc.update_interaction_summary(str(UUID_A), str(UUID_B), 100, "Hello!")
        await svc.update_interaction_summary(str(UUID_A), str(UUID_B), 200, "How are you?")

        rel = await svc.get_relationship(str(UUID_A), str(UUID_B))
        assert rel is not None
        summaries = svc.get_recent_summaries(rel, limit=5)
        assert len(summaries) == 2
        assert summaries[0] == "Hello!"
        assert summaries[1] == "How are you?"

    @pytest.mark.asyncio
    async def test_truncation_at_20(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        for i in range(25):
            await svc.update_interaction_summary(
                str(UUID_A), str(UUID_B), i * 10, f"msg-{i}"
            )

        rel = await svc.get_relationship(str(UUID_A), str(UUID_B))
        assert rel is not None
        summaries = svc.get_recent_summaries(rel, limit=100)
        assert len(summaries) == 20
        assert summaries[-1] == "msg-24"


class TestGetAllForCharacter:
    @pytest.mark.asyncio
    async def test_returns_all_relations(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        await svc.get_or_create(str(UUID_A), str(UUID_B))
        await svc.get_or_create(str(UUID_A), str(UUID_C))

        rels = await svc.get_all_for_character(str(UUID_A))
        assert len(rels) == 2

    @pytest.mark.asyncio
    async def test_includes_reverse_direction(self, db_session: AsyncSession):
        svc = RelationshipService(db_session)
        await svc.get_or_create(str(UUID_B), str(UUID_A))

        rels = await svc.get_all_for_character(str(UUID_A))
        assert len(rels) == 1
