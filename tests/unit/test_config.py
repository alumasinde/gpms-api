import os

from app.core.config import Settings


def _settings(cors_origins: str) -> Settings:
    return Settings(
        secret_key="test-secret",
        platform_database_url="mysql+aiomysql://user:pass@localhost/gatepass_platform",
        redis_url="redis://localhost:6379/0",
        cors_origins=cors_origins,
    )


def test_cors_json_env_value_is_parsed():
    settings = _settings('["http://localhost:3000", "http://localhost:5173"]')
    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]


def test_cors_csv_value_is_parsed():
    settings = _settings("http://localhost:3000,http://localhost:5173")
    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]
