"""Redis client singleton with graceful degradation."""

from __future__ import annotations

import logging

import redis.asyncio as redis

from the_world.config import settings

logger = logging.getLogger("the_world.db.redis")

_client: redis.Redis | None = None


async def get_redis() -> redis.Redis | None:
    """Return a shared async Redis client, or *None* if unavailable."""
    global _client  # noqa: PLW0603
    if _client is not None:
        try:
            await _client.ping()
            return _client
        except Exception:
            _client = None

    try:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await _client.ping()
        return _client
    except Exception:
        logger.debug("Redis unavailable at %s — falling back to in-memory", settings.REDIS_URL)
        _client = None
        return None
