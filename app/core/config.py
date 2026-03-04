from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SignalMind"
    database_url: str = "sqlite:///./signalmind.db"
    artifact_dir: Path = Path("data/artifacts")
    llm_provider: str = "mock"
    llm_model_name: str = "incident-brief-v1"
    random_seed: int = 42

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIGNALMIND_")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    return settings

