from app.config import Settings

_INSECURE_SECRET_MARKERS = (
    "dev-only-change-in-production",
    "dev-secret-replace-before-production",
    "change-this-to-a-long-random-string-in-production",
)


def validate_settings(settings: Settings) -> None:
    if not settings.database_url.strip():
        raise RuntimeError("DATABASE_URL is required (Neon PostgreSQL connection string).")

    if settings.is_production:
        secret = settings.secret_key.strip()
        if len(secret) < 32:
            raise RuntimeError("SECRET_KEY must be at least 32 characters in production.")
        if secret.lower() in _INSECURE_SECRET_MARKERS or "dev-secret" in secret.lower():
            raise RuntimeError("Set a unique SECRET_KEY for production.")
        if not settings.aws_s3_bucket.strip():
            raise RuntimeError("AWS_S3_BUCKET is required in production.")
        if not settings.aws_access_key_id.strip() or not settings.aws_secret_access_key.strip():
            raise RuntimeError("AWS credentials are required in production.")
