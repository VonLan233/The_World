"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings.

    All values are read from environment variables (or a .env file).
    Prefix-less names are used so that, e.g., DATABASE_URL maps directly.
    """

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/the_world"
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- AI / LLM ---
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    CLAUDE_API_KEY: str | None = None

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- App ---
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    # --- Simulation ---
    SIM_TIME_SCALE: float = 1.0
    SIM_TICK_INTERVAL_MS: int = 1000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Module-level singleton so the rest of the app can just import it.
settings = Settings()
