from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    secret_key: str = "dev-only-change-in-production"
    database_url: str = ""

    aws_region: str = "ap-south-1"
    aws_s3_bucket: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    session_cookie_name: str = "doctor_session"
    session_max_age_hours: int = 24
    cors_origins: str = "http://127.0.0.1:8000,http://localhost:8000"

    session_rate_limit_attempts: int = 10
    session_rate_limit_window_seconds: int = 900

    s3_presign_expiry_seconds: int = 900

    db_pool_size: int = 10
    db_max_overflow: int = 20

    otp_enabled: bool = False
    otp_ttl_minutes: int = 10
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 60
    otp_max_requests_per_hour: int = 5

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    sms_default_country_code: str = "91"

    otp_dev_mode: bool = False

    static_cache_seconds: int = 604800

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        url = (self.database_url or "").strip()
        if not url:
            raise ValueError("DATABASE_URL is required. Use your Neon PostgreSQL connection string.")
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://") and "+psycopg2" not in url:
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
