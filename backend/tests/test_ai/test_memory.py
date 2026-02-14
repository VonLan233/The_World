"""Tests for the MemoryManager (requires DB fixtures)."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.ai.memory import MemoryManager
from the_world.models.character import Character
from the_world.models.user import User

# Re-use the test DB session from conftest
from tests.conftest import TestSessionLocal


@pytest.fixture()
async def db() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


async def _create_user(db: AsyncSession) -> uuid.UUID:
    """Insert a minimal User row and return its UUID."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        username=f"testuser-{user_id.hex[:8]}",
        email=f"{user_id.hex[:8]}@test.com",
        hashed_password="fakehash",
    )
    db.add(user)
    await db.flush()
    return user_id


async def _create_character(db: AsyncSession, user_id: uuid.UUID) -> str:
    """Insert a minimal Character row and return its id as a string."""
    char_id = uuid.uuid4()
    char = Character(
        id=char_id,
        owner_id=user_id,
        name="TestChar",
    )
    db.add(char)
    await db.flush()
    return str(char_id)


@pytest.fixture()
async def char_id(db: AsyncSession) -> str:
    user_id = await _create_user(db)
    return await _create_character(db, user_id)


@pytest.fixture()
async def target_id() -> str:
    """Target ID does not need to be a real character — used only in context JSON."""
    return str(uuid.uuid4())


class TestMemoryCreate:
    @pytest.mark.asyncio
    async def test_create_memory(self, db: AsyncSession, char_id: str):
        mgr = MemoryManager(db)
        mem = await mgr.create_memory(
            character_id=char_id,
            memory_type="interaction",
            content="Met Bob at the park",
            sim_timestamp=100,
            importance=0.7,
            emotional_valence=0.3,
            context={"target_character_id": "bob-id"},
        )
        assert mem.id is not None
        assert mem.content == "Met Bob at the park"
        assert mem.importance == 0.7


class TestMemoryRetrieve:
    @pytest.mark.asyncio
    async def test_retrieve_recent(self, db: AsyncSession, char_id: str):
        mgr = MemoryManager(db)
        for i in range(5):
            await mgr.create_memory(
                character_id=char_id,
                memory_type="interaction",
                content=f"Memory {i}",
                sim_timestamp=i * 10,
            )
        await db.flush()

        recent = await mgr.retrieve_recent(char_id, limit=3)
        assert len(recent) == 3
        # Should be ordered by sim_timestamp desc
        assert recent[0].sim_timestamp >= recent[1].sim_timestamp

    @pytest.mark.asyncio
    async def test_retrieve_recent_with_type_filter(self, db: AsyncSession, char_id: str):
        mgr = MemoryManager(db)
        await mgr.create_memory(char_id, "interaction", "A", 10)
        await mgr.create_memory(char_id, "observation", "B", 20)
        await db.flush()

        result = await mgr.retrieve_recent(char_id, type_filter="observation")
        assert len(result) == 1
        assert result[0].content == "B"

    @pytest.mark.asyncio
    async def test_retrieve_relevant_scoring(self, db: AsyncSession, char_id: str):
        mgr = MemoryManager(db)
        # High importance, recent
        await mgr.create_memory(char_id, "interaction", "Important recent", 990,
                                importance=0.9, emotional_valence=0.5)
        # Low importance, old
        await mgr.create_memory(char_id, "interaction", "Old unimportant", 10,
                                importance=0.1, emotional_valence=0.0)
        await db.flush()

        relevant = await mgr.retrieve_relevant(char_id, current_tick=1000, limit=2)
        assert len(relevant) == 2
        # The important recent one should rank higher
        assert relevant[0].content == "Important recent"


class TestInteractionCount:
    @pytest.mark.asyncio
    async def test_count_zero_initially(self, db: AsyncSession, char_id: str, target_id: str):
        mgr = MemoryManager(db)
        count = await mgr.get_interaction_count(char_id, target_id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_after_interactions(self, db: AsyncSession, char_id: str, target_id: str):
        mgr = MemoryManager(db)
        for i in range(3):
            await mgr.create_memory(
                char_id, "interaction", f"Chat {i}", i * 10,
                context={"target_character_id": target_id},
            )
        await db.flush()

        count = await mgr.get_interaction_count(char_id, target_id)
        assert count == 3

    @pytest.mark.asyncio
    async def test_count_excludes_other_targets(self, db: AsyncSession, char_id: str, target_id: str):
        mgr = MemoryManager(db)
        await mgr.create_memory(
            char_id, "interaction", "Chat with target", 10,
            context={"target_character_id": target_id},
        )
        await mgr.create_memory(
            char_id, "interaction", "Chat with someone else", 20,
            context={"target_character_id": "other-id"},
        )
        await db.flush()

        count = await mgr.get_interaction_count(char_id, target_id)
        assert count == 1


class TestFormatMemories:
    def test_format_empty(self):
        assert MemoryManager.format_memories_for_prompt([]) == []

    @pytest.mark.asyncio
    async def test_format_produces_strings(self, db: AsyncSession, char_id: str):
        mgr = MemoryManager(db)
        mem = await mgr.create_memory(char_id, "interaction", "Hello world", 100)
        lines = MemoryManager.format_memories_for_prompt([mem])
        assert len(lines) == 1
        assert "[interaction]" in lines[0]
        assert "Hello world" in lines[0]
