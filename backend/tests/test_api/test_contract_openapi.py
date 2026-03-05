"""Contract guard tests based on generated OpenAPI schema.

These tests protect critical HTTP method/path contracts from accidental drift.
"""

import pytest

from the_world.main import app


@pytest.mark.asyncio
async def test_openapi_contains_core_paths_and_methods() -> None:
    """Core API contracts should exist with expected HTTP methods."""
    schema = app.openapi()
    paths = schema["paths"]

    expected_methods = {
        "/health": {"get"},
        "/api/v1/auth/register": {"post"},
        "/api/v1/auth/login": {"post"},
        "/api/v1/auth/me": {"get"},
        "/api/v1/characters/": {"get", "post"},
        "/api/v1/characters/public": {"get"},
        "/api/v1/characters/{character_id}": {"get", "put", "patch", "delete"},
        "/api/v1/worlds/": {"get", "post"},
        "/api/v1/worlds/{world_id}": {"get"},
        "/api/v1/simulation/{world_id}/start": {"post"},
        "/api/v1/simulation/{world_id}/pause": {"post"},
        "/api/v1/simulation/{world_id}/speed": {"post"},
        "/api/v1/simulation/{world_id}/state": {"get"},
        "/api/v1/relationships/{character_id}": {"get"},
        "/api/v1/relationships/{character_id}/{target_id}": {"get"},
    }

    for path, methods in expected_methods.items():
        assert path in paths, f"Missing path in OpenAPI schema: {path}"
        actual = set(paths[path].keys())
        assert methods.issubset(actual), (
            f"Path {path} missing methods {methods - actual}; actual methods: {actual}"
        )


@pytest.mark.asyncio
async def test_login_contract_uses_form_urlencoded() -> None:
    """Login endpoint should keep form-data contract expected by frontend store."""
    schema = app.openapi()
    login_post = schema["paths"]["/api/v1/auth/login"]["post"]
    content = login_post["requestBody"]["content"]
    assert "application/x-www-form-urlencoded" in content
