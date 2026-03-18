"""Generic LLM text-generation helper for non-dialogue tasks.

Used by the reflection and planning subsystems.  Tries Claude (haiku) first,
falls back to Ollama, and returns None if neither is reachable.
Never raises — all errors are logged and swallowed.
"""

from __future__ import annotations

import logging

from the_world.config import settings

logger = logging.getLogger("the_world.ai.llm_utils")


async def generate_text_llm(prompt: str, max_tokens: int = 200) -> str | None:
    """Call an LLM with *prompt* and return the completion text.

    Resolution order:
    1. Claude Haiku (cheap, fast) — if CLAUDE_API_KEY is set
    2. Ollama — if the local server is reachable
    3. None — if nothing is available

    Parameters
    ----------
    prompt:     Full text prompt.
    max_tokens: Maximum tokens to generate.
    """
    # ------------------------------------------------------------------
    # 1. Try Claude Haiku
    # ------------------------------------------------------------------
    if settings.CLAUDE_API_KEY:
        try:
            import anthropic  # lazy import

            client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip() or None
        except Exception:
            logger.debug("Claude Haiku unavailable for llm_utils, trying Ollama")

    # ------------------------------------------------------------------
    # 2. Try Ollama
    # ------------------------------------------------------------------
    try:
        import httpx

        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.7},
        }
        async with httpx.AsyncClient(trust_env=False, timeout=20.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_URL}/api/generate", json=payload
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            return text or None
    except Exception:
        logger.debug("Ollama unavailable for llm_utils")

    return None
