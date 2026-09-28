from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role, User

UserSortField = Literal["created_at", "email", "username"]

_SORT_COLUMNS: dict[str, ColumnElement[object]] = {
    "created_at": User.created_at,  # type: ignore[dict-item]
    "email": User.email,  # type: ignore[dict-item]
    "username": User.username,  # type: ignore[dict-item]
}


@dataclass(frozen=True, slots=True)
class UserFilters:
    role: str | None = None
    is_active: bool | None = None


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_name(self, name: str) -> Role | None:
        return await self._session.scalar(select(Role).where(Role.name == name))


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self._session.scalar(select(User).where(User.email == email))

    async def get_by_username(self, username: str) -> User | None:
        return await self._session.scalar(select(User).where(User.username == username))

    def add(self, user: User) -> None:
        self._session.add(user)

    async def list(
        self,
        *,
        filters: UserFilters,
        offset: int,
        limit: int,
        sort: UserSortField = "created_at",
        descending: bool = False,
    ) -> tuple[Sequence[User], int]:
        conditions: list[ColumnElement[bool]] = []
        if filters.role is not None:
            conditions.append(User.role.has(Role.name == filters.role))
        if filters.is_active is not None:
            conditions.append(User.is_active.is_(filters.is_active))

        total = await self._session.scalar(
            select(func.count()).select_from(User).where(*conditions)
        )
        column = _SORT_COLUMNS[sort]
        order = column.desc() if descending else column.asc()
        result = await self._session.scalars(
            select(User).where(*conditions).order_by(order, User.id).offset(offset).limit(limit)
        )
        return result.unique().all(), total or 0
