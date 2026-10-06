from sqlalchemy import inspect, text

from app.database import engine


def _column_names(table: str) -> set[str]:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table)}


def run_migrations() -> None:
    doctor_columns = _column_names("doctors")
    if not doctor_columns or "full_name" in doctor_columns:
        return

    dialect = engine.dialect.name
    with engine.begin() as connection:
        if dialect == "postgresql":
            connection.execute(text("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS full_name VARCHAR(256) DEFAULT ''"))
            connection.execute(
                text("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS registration_number VARCHAR(128) DEFAULT ''")
            )
            connection.execute(text("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS clinic_name VARCHAR(256) DEFAULT ''"))
            connection.execute(
                text("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS clinic_address VARCHAR(512) DEFAULT ''")
            )
            connection.execute(text("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"))
        else:
            connection.execute(text("ALTER TABLE doctors ADD COLUMN full_name VARCHAR(256) DEFAULT ''"))
            connection.execute(text("ALTER TABLE doctors ADD COLUMN registration_number VARCHAR(128) DEFAULT ''"))
            connection.execute(text("ALTER TABLE doctors ADD COLUMN clinic_name VARCHAR(256) DEFAULT ''"))
            connection.execute(text("ALTER TABLE doctors ADD COLUMN clinic_address VARCHAR(512) DEFAULT ''"))
            connection.execute(text("ALTER TABLE doctors ADD COLUMN updated_at DATETIME"))
