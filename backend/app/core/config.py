from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Security
    secret_key: str = "your-secret-key-here-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/data_storage"
    database_url_async: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/data_storage"
    )

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Email
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_port: int = 587
    mail_server: str = ""
    mail_tls: bool = True
    mail_ssl: bool = False

    # Sentry
    sentry_dsn: Optional[str] = None

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_login_attempts: int = 5

    # Environment
    environment: str = "development"
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
