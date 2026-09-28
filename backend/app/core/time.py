from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_aware(value: datetime) -> datetime:
    """Treat naive datetimes as UTC (SQLite drops tzinfo; PostgreSQL keeps it)."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
