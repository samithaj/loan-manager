from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    debug: bool = True
    database_url: str = "postgresql+asyncpg://postgres@127.0.0.1:5432/loan_manager"
    # Demo mode accepts any non-empty Basic credentials
    demo_open_basic_auth: bool = False

    class Config:
        env_prefix = "LM_"


def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


