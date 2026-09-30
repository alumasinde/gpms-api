from functools import lru_cache
import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import NoDecode
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Gatepass"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    platform_database_url: str
    mysql_pool_size: int = 10
    mysql_max_overflow: int = 20
    mysql_pool_timeout: int = 30
    mysql_pool_recycle: int = 1800

    redis_url: str
    redis_max_connections: int = 20
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value):
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                parsed = json.loads(raw)
                if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                    raise ValueError("CORS_ORIGINS must be a JSON array of strings")
                return [item.strip() for item in parsed if item.strip()]
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
