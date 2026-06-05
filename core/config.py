import os
from typing import Annotated
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseSettings):
    level: str = "INFO"
    file: str | None = None
    disable_access_log: bool = False

    model_config = SettingsConfigDict(env_prefix="LOG_")


class DatabaseSettings(BaseSettings):
    user: str = "app"
    host: str = "postgres"
    port: str = "5432"
    name: str = "app"

    def get_database_url_sync(self) -> str:
        """
        Returns a synchronous connection URL to PostgreSQL.

        Behavior:
        - If the DB_PASSWORD environment variable is set, it is used (for running Alembic locally).
        - Otherwise, it gets the password from HashiCorp Vault (Kubernetes mode).

        Returns:
        str: Full database URL in the format postgresql://user:password@host:port/dbname
        """
        raw_password = os.getenv("DB_PASSWORD")
        if raw_password:
            password = quote_plus(raw_password)
        else:
            from core.secrets import secret_manager

            password = quote_plus(secret_manager.get_db_password())

        return f"postgresql://{self.user}:{password}@{self.host}:{self.port}/{self.name}"

    def get_database_url_async(self, password: str) -> str:
        return f"postgresql+asyncpg://{self.user}:{quote_plus(password)}@{self.host}:{self.port}/{self.name}"

    model_config = SettingsConfigDict(env_prefix="DB_")


class AuthSettings(BaseSettings):
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(env_prefix="AUTH_")


class RedisCacheSettings(BaseSettings):
    host: str = "redis"
    port: int = 6379

    # Stream names
    user_events_stream: str = "user_events"
    email_workers_group: str = "email_workers"

    # Pub/Sub channels
    login_channel: str = "user_login_events"

    # Cache settings
    user_cache_key_prefix: str = "user"
    visitors_key_prefix: str = "visitors"
    user_cache_ttl: int = 300

    # Leaderboard settings
    leaderboard_key: str = "leaderboard:weekly"
    leaderboard_top_n: int = 10

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class VaultSettings(BaseSettings):
    addr: str = "http://vault.app.svc:8200"
    k8s_role: str = "api-role"
    jwt_token_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"

    model_config = SettingsConfigDict(env_prefix="VAULT_")


class Settings(BaseSettings):
    db: Annotated[DatabaseSettings, Field(default_factory=DatabaseSettings)]
    auth: Annotated[AuthSettings, Field(default_factory=AuthSettings)]
    redis: Annotated[RedisCacheSettings, Field(default_factory=RedisCacheSettings)]
    logging: Annotated[LoggingSettings, Field(default_factory=LoggingSettings)]
    vault: Annotated[VaultSettings, Field(default_factory=VaultSettings)]


settings = Settings()
