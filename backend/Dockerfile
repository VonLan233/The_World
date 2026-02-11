# =============================================================================
# Multi-stage Dockerfile for The World backend
# =============================================================================

# --------------- base ---------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv (fast Python package manager)
RUN pip install --no-cache-dir uv

# --------------- deps ---------------
FROM base AS deps

COPY pyproject.toml ./

# Install production dependencies only (no dev extras)
RUN uv pip install --system --no-cache .

# --------------- runtime ---------------
FROM deps AS runtime

# Copy source tree and alembic config
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Expose the default uvicorn port
EXPOSE 8000

# Run the ASGI server
CMD ["uvicorn", "the_world.main:app", "--host", "0.0.0.0", "--port", "8000"]
