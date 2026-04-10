"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LINE
    line_channel_access_token: str = ""
    line_channel_secret: str = ""

    # Sendbird
    sendbird_app_id: str = ""
    sendbird_api_token: str = ""
    bot_user_id: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def sendbird_api_url(self) -> str:
        return f"https://api-{self.sendbird_app_id}.sendbird.com/v3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
