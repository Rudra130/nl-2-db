"""Configuration and Settings Module."""
from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # NVIDIA NIM Configuration
    NVIDIA_NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_NIM_API_KEY: str = Field(default="", description="NVIDIA NIM API Key")
    NVIDIA_NIM_MODEL: str = "meta/llama-3.1-70b-instruct"
    NVIDIA_NIM_TIMEOUT_SECONDS: int = 30
    NVIDIA_NIM_TEMPERATURE: float = 0.1
    USE_MOCK_LLM: bool = False

    # Guardrails
    MAX_QUERY_TIMEOUT_SECONDS: int = 5
    DEFAULT_ROW_LIMIT: int = 50
    HARD_MAX_ROWS: int = 500
    MAX_RECOVERY_RETRIES: int = 2

    # Database 1: MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "nl2db_test"

    # Database 2: PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DATABASE: str = "nl2db_test"

    # Database 3: MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "nl2db_test"

    # Database 4: SQLite
    SQLITE_DB_PATH: str = "./data/nl2db_sample.db"

    @property
    def mysql_async_url(self) -> str:
        pwd = f":{self.MYSQL_PASSWORD}" if self.MYSQL_PASSWORD else ""
        return f"mysql+aiomysql://{self.MYSQL_USER}{pwd}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    @property
    def postgres_async_url(self) -> str:
        pwd = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}{pwd}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"

    @property
    def sqlite_async_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
