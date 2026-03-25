from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Workflow Orchestrator API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")
    database_url: str = Field(alias="DATABASE_URL")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    openrouter_model: str = Field(default="openai/gpt-4o-mini", alias="OPENROUTER_MODEL")
    openrouter_timeout_s: int = Field(default=30, alias="OPENROUTER_TIMEOUT_S")
    openrouter_referer: str = Field(default="http://localhost", alias="OPENROUTER_REFERER")
    openrouter_app_name: str = Field(default="ai-workflow-orchestrator", alias="OPENROUTER_APP_NAME")
    openrouter_mock: bool = Field(default=False, alias="OPENROUTER_MOCK")
    auth_secret_key: str = Field(default="change-me-in-local-env", alias="AUTH_SECRET_KEY")
    auth_algorithm: str = Field(default="HS256", alias="AUTH_ALGORITHM")
    auth_access_token_exp_minutes: int = Field(default=1440, alias="AUTH_ACCESS_TOKEN_EXP_MINUTES")


@lru_cache
def get_settings() -> Settings:
    return Settings()
