from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The project's .env lives at the repo root (one level above backend/), same
# place docker-compose's `env_file: .env` reads it from. Resolve it by an
# absolute path rather than the bare ".env" pydantic-settings default, which
# only gets found if the process happens to be launched with that exact
# directory as its cwd (e.g. silently ignored if run from within backend/).
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    app_name: str = "AI Growth Twin"
    environment: str = "development"

    database_url: str = "postgresql+psycopg://growth_twin:growth_twin@localhost:5432/growth_twin"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    posthog_api_key: str = ""
    posthog_host: str = "https://us.i.posthog.com"

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
