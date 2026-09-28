from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role

# Kept in sync with the initial Alembic migration, which inserts the same rows.
DEFAULT_ROLES: dict[str, str] = {
    "admin": "Full access, including user and role management",
    "developer": "Create and manage projects and run analyses",
    "viewer": "Read-only access to dashboards and reports",
}


async def ensure_roles(session: AsyncSession) -> None:
    """Insert any missing default roles. Safe to call repeatedly."""
    existing = set((await session.scalars(select(Role.name))).all())
    for name, description in DEFAULT_ROLES.items():
        if name not in existing:
            session.add(Role(name=name, description=description))
    await session.flush()
