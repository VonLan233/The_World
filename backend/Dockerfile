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

COPY pyproject.toml uv.lock ./

# Create minimal package structure so hatch can build and resolve dependencies
RUN mkdir -p src/the_world && touch src/the_world/__init__.py

# Install package + all dependencies
RUN uv pip install --system --no-cache .

# --------------- runtime ---------------
FROM deps AS runtime

# Real source replaces dummy; PYTHONPATH ensures it's found before site-packages
ENV PYTHONPATH=/app/src

# Copy source tree and alembic config
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Ensure alembic versions directory exists
RUN mkdir -p ./alembic/versions

# Copy entrypoint script
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Expose the default uvicorn port
EXPOSE 8000

# Entrypoint runs migrations then starts the server
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "the_world.main:app", "--host", "0.0.0.0", "--port", "8000"]
