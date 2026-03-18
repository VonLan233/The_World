"""Third-party AI providers — user-supplied API keys for text and image generation."""

from __future__ import annotations

import base64
import logging

import httpx

logger = logging.getLogger("the_world.ai.third_party")

_OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
_OPENAI_IMAGE_URL = "https://api.openai.com/v1/images/generations"


async def generate_text(
    prompt: str,
    provider: str,
    api_key: str,
    model: str | None = None,
) -> str:
    """Generate text using a user-supplied API key.

    Supports provider values: "anthropic", "openai".
    """
    if provider == "anthropic":
        return await _anthropic_text(prompt, api_key, model or "claude-sonnet-4-6")
    if provider == "openai":
        return await _openai_text(prompt, api_key, model or "gpt-4o")
    raise ValueError(f"Unsupported text provider: {provider!r}")


async def generate_image(prompt: str, api_key: str) -> bytes:
    """Generate an image via DALL-E 3, return raw PNG/JPEG bytes."""
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            _OPENAI_IMAGE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "response_format": "b64_json",
            },
        )
        resp.raise_for_status()
        b64 = resp.json()["data"][0]["b64_json"]
        return base64.b64decode(b64)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _anthropic_text(prompt: str, api_key: str, model: str) -> str:
    import anthropic  # optional dependency — only imported when needed

    client = anthropic.AsyncAnthropic(api_key=api_key)
    message = await client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text  # type: ignore[union-attr]


async def _openai_text(prompt: str, api_key: str, model: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            _OPENAI_CHAT_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2048,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
